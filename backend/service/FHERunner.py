import json
import base64
import warnings
import numpy as np
from datetime import datetime
from pathlib import Path
from concrete import fhe

from model.PatientHospitalization import PatientHospitalization
from model.HospitalExpense import HospitalExpense

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).parent.parent
KEYS_DIR = PROJECT_ROOT / "fhe_keys"
EXPENSE_KEYS_DIR = PROJECT_ROOT / "fhe_keys_expenses"


class FHERunner:
    LOS_MAX_DAYS = 730
    LOS_MAX_BUCKET = 100

    COST_MAX_DOLLARS = 70_000
    COST_MAX_BUCKET = 150

    MORTALITY_MAX_BUCKET = 50

    EXPENSE_MAX_DOLLARS = 260_000
    EXPENSE_MAX_BUCKET = 50

    def __init__(self, keys_dir: Path = KEYS_DIR) -> None:
        self.keys_dir = Path(keys_dir)
        print("[FHERunner] Initialising …")
        self._load_params()
        self._compile_circuits_and_load_keys()
        self._compile_los_circuit()
        self._compile_cost_circuit()
        self._compile_mortality_circuit()
        self._load_expense_params()
        self._compile_expense_circuits_and_load_keys()
        self._compile_expense_sum_circuit()
        print("[FHERunner] Ready\n")


    def _load_params(self) -> None:
        params_path = self.keys_dir / "circuit_params.json"
        with open(params_path) as f:
            p = json.load(f)

        self.scale = p["scale"]
        self.max_num_val = p["max_num_val"]
        self.max_patient_id = p["max_patient_id"]
        self.rng_seed = p["rng_seed"]
        self.str_max_lens = p["str_max_lens"]
        self.cost_fields = p["cost_fields"]
        self.bool_fields = p["bool_fields"]
        self.id_fields = p["id_fields"]
        self.num_fields = p["num_fields"]
        self.str_fields = p["str_fields"]
        print(f"  [FHERunner] Loaded params  → {params_path}")

    def _compile_circuits_and_load_keys(self) -> None:
        rng = np.random.default_rng(seed=self.rng_seed)

        @fhe.compiler({"x": "encrypted"})
        def fhe_num_identity(x):
            return x

        num_inputset = list(rng.integers(0, self.max_num_val, 300, dtype=np.int64))
        num_inputset += [
            np.int64(0),
            np.int64(self.max_num_val),
            np.int64(self.max_patient_id),
        ]

        print("  [FHERunner] Compiling numeric circuit …")
        self.num_circuit = fhe_num_identity.compile(num_inputset)
        self.num_circuit.client.keys.load(
            str(self.keys_dir / "num_circuit.keys")
        )
        print("  [FHERunner] Numeric circuit — keys loaded")

        self.str_circuits: dict[str, fhe.Circuit] = {}

        for field in self.str_fields:
            max_len = self.str_max_lens[field]

            def _make_compiler():
                @fhe.compiler({"bytes_arr": "encrypted"})
                def _circuit(bytes_arr):
                    return bytes_arr + 0
                return _circuit

            str_inputset = list(
                rng.integers(0, 256, (300, max_len), dtype=np.int64)
            )
            str_inputset += [
                np.zeros(max_len, dtype=np.int64),
                np.full(max_len, 255, dtype=np.int64),
            ]

            print(f"  [FHERunner] Compiling string circuit for '{field}' …")
            c = _make_compiler().compile(str_inputset)
            c.client.keys.load(str(self.keys_dir / f"str_{field}.keys"))
            self.str_circuits[field] = c
            print(f"  [FHERunner] '{field}' circuit — keys loaded")

    def _compile_los_circuit(self) -> None:
        print(f"  [FHERunner] Compiling LOS sum circuit "
              f"(bucket_size={self.LOS_MAX_BUCKET}, max_days={self.LOS_MAX_DAYS}) …")

        rng_los = np.random.default_rng(seed=999)

        @fhe.compiler({"arr": "encrypted"})
        def _fhe_sum_los(arr):
            return np.sum(arr)

        inputset = list(rng_los.integers(0, self.LOS_MAX_DAYS + 1, (300, self.LOS_MAX_BUCKET), dtype=np.int64))
        inputset += [
            np.zeros(self.LOS_MAX_BUCKET, dtype=np.int64),
            np.full(self.LOS_MAX_BUCKET, self.LOS_MAX_DAYS, dtype=np.int64),
        ]

        self.los_circuit = _fhe_sum_los.compile(inputset)
        self.los_circuit.keygen()
        print("  [FHERunner] LOS sum circuit — compiled & keys generated")

    def _compile_cost_circuit(self) -> None:
        print(f"  [FHERunner] Compiling cost sum circuit "
              f"(bucket_size={self.COST_MAX_BUCKET}, "
              f"max_dollars={self.COST_MAX_DOLLARS:,}) …")

        rng_cost = np.random.default_rng(seed=777)

        @fhe.compiler({"arr": "encrypted"})
        def _fhe_sum_cost(arr):
            return np.sum(arr)

        inputset = list(rng_cost.integers(0, self.COST_MAX_DOLLARS + 1, (300, self.COST_MAX_BUCKET), dtype=np.int64))
        inputset += [
            np.zeros(self.COST_MAX_BUCKET, dtype=np.int64),
            np.full(self.COST_MAX_BUCKET, self.COST_MAX_DOLLARS, dtype=np.int64),
        ]

        self.cost_circuit = _fhe_sum_cost.compile(inputset)
        self.cost_circuit.keygen()
        print("  [FHERunner] Cost sum circuit — compiled & keys generated")

    def _compile_mortality_circuit(self) -> None:
        print(f"  [FHERunner] Compiling mortality sum circuit "
              f"(bucket_size={self.MORTALITY_MAX_BUCKET}) …")

        rng_mort = np.random.default_rng(seed=555)

        @fhe.compiler({"arr": "encrypted"})
        def _fhe_sum_mortality(arr):
            return np.sum(arr)

        inputset = list(
            rng_mort.integers(0, 2, (300, self.MORTALITY_MAX_BUCKET), dtype=np.int64)
        )
        inputset += [
            np.zeros(self.MORTALITY_MAX_BUCKET, dtype=np.int64),
            np.ones(self.MORTALITY_MAX_BUCKET,  dtype=np.int64),
        ]

        self.mortality_circuit = _fhe_sum_mortality.compile(inputset)
        self.mortality_circuit.keygen()
        print("  [FHERunner] Mortality sum circuit — compiled & keys generated")

    def _load_expense_params(self) -> None:
        """Read circuit_params.json written by encrypt_expenses.py."""
        params_path = EXPENSE_KEYS_DIR / "circuit_params.json"
        with open(params_path) as f:
            p = json.load(f)
        self.exp_scale = p["scale"]
        self.exp_max_amt_cents = p["max_amount_cents"]
        self.exp_rng_seed = p["rng_seed"]
        self.exp_str_max_lens = p["str_max_lens"]
        self.exp_num_fields = p["num_fields"]
        self.exp_str_fields = p["str_fields"]
        print(f"  [FHERunner] Loaded expense params - {params_path}")

    def _compile_expense_circuits_and_load_keys(self) -> None:
        rng = np.random.default_rng(seed=self.exp_rng_seed)

        @fhe.compiler({"x": "encrypted"})
        def _exp_num_identity(x):
            return x

        exp_num_inputset = list(rng.integers(0, self.exp_max_amt_cents, 300, dtype=np.int64))
        exp_num_inputset += [np.int64(0), np.int64(self.exp_max_amt_cents)]

        print("  [FHERunner] Compiling expense numeric circuit …")
        self.exp_num_circuit = _exp_num_identity.compile(exp_num_inputset)
        self.exp_num_circuit.client.keys.load(str(EXPENSE_KEYS_DIR / "num_circuit.keys"))
        print("  [FHERunner] Expense numeric circuit — keys loaded")

        self.exp_str_circuits: dict[str, fhe.Circuit] = {}
        for field in self.exp_str_fields:
            max_len = self.exp_str_max_lens[field]

            def _make_exp_str_compiler():
                @fhe.compiler({"bytes_arr": "encrypted"})
                def _circuit(bytes_arr):
                    return bytes_arr + 0
                return _circuit

            str_inputset = list(rng.integers(0, 256, (300, max_len), dtype=np.int64))
            str_inputset += [np.zeros(max_len, dtype=np.int64),
                             np.full(max_len, 255, dtype=np.int64)]

            print(f"  [FHERunner] Compiling expense string circuit for '{field}' …")
            c = _make_exp_str_compiler().compile(str_inputset)
            c.client.keys.load(str(EXPENSE_KEYS_DIR / f"str_{field}.keys"))
            self.exp_str_circuits[field] = c
            print(f"  [FHERunner] ✓ Expense '{field}' circuit — keys loaded")

    def _compile_expense_sum_circuit(self) -> None:
        print(f"  [FHERunner] Compiling expense sum circuit "
              f"(bucket_size={self.EXPENSE_MAX_BUCKET}, "
              f"max_dollars={self.EXPENSE_MAX_DOLLARS:,}) …")

        rng_exp = np.random.default_rng(seed=444)

        @fhe.compiler({"arr": "encrypted"})
        def _fhe_sum_expense(arr):
            return np.sum(arr)

        inputset = list(rng_exp.integers(0, self.EXPENSE_MAX_DOLLARS + 1,
                                          (300, self.EXPENSE_MAX_BUCKET), dtype=np.int64))
        inputset += [np.zeros(self.EXPENSE_MAX_BUCKET, dtype=np.int64),
                     np.full(self.EXPENSE_MAX_BUCKET, self.EXPENSE_MAX_DOLLARS, dtype=np.int64)]

        self.expense_sum_circuit = _fhe_sum_expense.compile(inputset)
        self.expense_sum_circuit.keygen()
        print("  [FHERunner] Expense sum circuit — compiled & keys generated")


    def decrypt_entry(self, encrypted_entry: dict) -> dict:
        result: dict = {
            "uuid":           encrypted_entry["uuid"],
            "admission_date": encrypted_entry["admission_date"],
            "discharge_date": encrypted_entry["discharge_date"],
        }

        enc_fields = encrypted_entry["encrypted_fields"]

        for field in self.num_fields:
            info = enc_fields[field]
            raw_bytes = base64.b64decode(info["ciphertext"])
            enc_val = fhe.Value.deserialize(raw_bytes)
            evaluated = self.num_circuit.run(enc_val)
            decrypted = self.num_circuit.decrypt(evaluated)

            if field in self.cost_fields:
                result[field] = round(int(decrypted) / self.scale, 2)
            elif field in self.bool_fields:
                result[field] = bool(int(decrypted))
            else:
                result[field] = int(decrypted)   # patient_id

        for field in self.str_fields:
            info = enc_fields[field]
            raw_bytes = base64.b64decode(info["ciphertext"])
            enc_val = fhe.Value.deserialize(raw_bytes)
            circuit = self.str_circuits[field]
            evaluated = circuit.run(enc_val)
            arr = circuit.decrypt(evaluated)
            orig_len = info["original_length"]
            result[field] = bytes(int(x) for x in arr[:orig_len]).decode("utf-8")

        return result

    def _decrypt_string_field(self, field: str, enc_field_dict: dict) -> str:
        raw_bytes = base64.b64decode(enc_field_dict["ciphertext"])
        enc_val = fhe.Value.deserialize(raw_bytes)
        circuit = self.str_circuits[field]
        evaluated = circuit.run(enc_val)
        arr = circuit.decrypt(evaluated)
        orig_len = enc_field_dict["original_length"]
        return bytes(int(x) for x in arr[:orig_len]).decode("utf-8")

    def generateAverageLengthOfStayStatistics(self, patientHospitalizationMap: dict) -> dict:
        AGE_CATEGORIES = ["under 18", "18 to 65", "over 65"]
        MONTH_NAMES = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}

        total_entries = sum(
            len(entries)
            for months in patientHospitalizationMap.values()
            for entries in months.values()
        )

        print("\n[FHERunner] " + "═"*54)
        print("[FHERunner]   Average Length of Stay — FHE Statistics")
        print("[FHERunner] " + "═"*54)
        print(f"[FHERunner]   Years in map  : {sorted(patientHospitalizationMap)}")
        print(f"[FHERunner]   Total entries : {total_entries}")

        print(f"\n[FHERunner] STEP 1 — Decrypt age categories & compute LOS")
        print(f"[FHERunner]   (decrypting {total_entries} age_category ciphertexts …)\n")

        grouped_los: dict = {}
        processed = 0

        for year, months in patientHospitalizationMap.items():
            grouped_los[year] = {}
            for month, entries in months.items():
                grouped_los[year][month] = {cat: [] for cat in AGE_CATEGORIES}
                for entry in entries:
                    age_cat = self._decrypt_string_field(
                        "age_category", entry.getAgeCategory()
                    )

                    admission = datetime.strptime(entry.getAdmissionDate(), "%d.%m.%Y")
                    discharge = datetime.strptime(entry.getDischargeDate(), "%d.%m.%Y")
                    los = max(1, (discharge - admission).days)

                    if age_cat in grouped_los[year][month]:
                        grouped_los[year][month][age_cat].append(los)

                    processed += 1
                    if processed % 300 == 0 or processed == total_entries:
                        pct = processed / total_entries * 100
                        print(f"[FHERunner]   {processed:>5}/{total_entries}  ({pct:.1f}%)")

        print(f"\n[FHERunner] Step 1 complete — {processed} entries processed")

        all_los_flat: list[int] = [
            v
            for months in grouped_los.values()
            for ag in months.values()
            for los_list in ag.values()
            for v in los_list
        ]

        if not all_los_flat:
            print("[FHERunner] No data available — returning empty result.")
            return {}

        max_los_observed = max(all_los_flat)
        max_bucket_observed = max(
            len(los_list)
            for months in grouped_los.values()
            for ag in months.values()
            for los_list in ag.values()
        )

        print(f"\n[FHERunner] STEP 2 — Using pre-compiled LOS sum circuit")
        print(f"[FHERunner]   Circuit bucket size : {self.LOS_MAX_BUCKET}")
        print(f"[FHERunner]   Circuit max days    : {self.LOS_MAX_DAYS}")
        print(f"[FHERunner]   Observed max LOS    : {max_los_observed} days"
              + (" ! clamped to circuit max" if max_los_observed > self.LOS_MAX_DAYS else " ✓"))
        print(f"[FHERunner]   Observed max bucket : {max_bucket_observed} entries"
              + (" ! will be split" if max_bucket_observed > self.LOS_MAX_BUCKET else " ✓"))

        total_buckets = sum(
            len(ag)
            for months in grouped_los.values()
            for ag in months.values()
        )
        print(f"\n[FHERunner] STEP 3 — FHE summation ({total_buckets} buckets)")

        plain_monthly: dict = {}
        bucket_done = 0

        for year, months in grouped_los.items():
            plain_monthly[year] = {}
            for month, age_groups in months.items():
                plain_monthly[year][month] = {}
                for age_cat, los_list in age_groups.items():
                    bucket_done += 1

                    if not los_list:
                        plain_monthly[year][month][age_cat] = (0, 0)
                        print(f"[FHERunner]   [{bucket_done:>4}/{total_buckets}] "
                              f"{year} {MONTH_NAMES[month]:>3} '{age_cat}' — no data")
                        continue

                    count = len(los_list)
                    clamped = [min(v, self.LOS_MAX_DAYS) for v in los_list]

                    plain_sum = 0
                    for chunk_start in range(0, count, self.LOS_MAX_BUCKET):
                        chunk = clamped[chunk_start: chunk_start + self.LOS_MAX_BUCKET]
                        padded = np.zeros(self.LOS_MAX_BUCKET, dtype=np.int64)
                        padded[:len(chunk)] = chunk
                        enc_arr = self.los_circuit.encrypt(padded)
                        enc_sum = self.los_circuit.run(enc_arr)
                        plain_sum += int(self.los_circuit.decrypt(enc_sum))

                    plain_monthly[year][month][age_cat] = (plain_sum, count)
                    avg = round(plain_sum / count, 2)
                    print(f"[FHERunner]   [{bucket_done:>4}/{total_buckets}] "
                          f"{year} {MONTH_NAMES[month]:>3} '{age_cat}' — "
                          f"Σ={plain_sum} days / {count} entries = {avg} days avg")

        print(f"[FHERunner] Step 3 complete — {bucket_done} buckets computed via FHE")

        print(f"\n[FHERunner] STEP 4 — Assembling result")
        result: dict = {}

        for year, months in plain_monthly.items():
            year_str = str(year)
            yearly_totals = {cat: [0, 0] for cat in AGE_CATEGORIES}   # [sum, count]
            monthly_result: dict = {}

            for month in sorted(months.keys()):
                age_groups = months[month]
                month_name = MONTH_NAMES[month]
                monthly_result[month_name] = {}
                for age_cat in AGE_CATEGORIES:
                    plain_sum, count = age_groups.get(age_cat, (0, 0))
                    monthly_result[month_name][age_cat] = (
                        round(plain_sum / count, 2) if count > 0 else None
                    )
                    yearly_totals[age_cat][0] += plain_sum
                    yearly_totals[age_cat][1] += count

            general = {
                age_cat: (
                    round(yearly_totals[age_cat][0] / yearly_totals[age_cat][1], 2)
                    if yearly_totals[age_cat][1] > 0 else None
                )
                for age_cat in AGE_CATEGORIES
            }

            result[year_str] = {"general": general, **monthly_result}

        output_path = PROJECT_ROOT / "average_length_of_stay_statistics.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"[FHERunner] Results written → {output_path}")

        print(f"\n[FHERunner] ══ Summary ══")
        for year_str, year_data in result.items():
            gen = year_data.get("general", {})
            print(f"\n  {year_str} (overall):")
            for cat, val in gen.items():
                print(f"    {cat:<12} : {val} days avg")

        return result

    def generateCostsPerPatientStatistics(self, patientHospitalizationMap: dict) -> dict:
        COST_FIELD_LABELS = {
            "cost_services": "services",
            "cost_hospitalization": "hospitalization",
            "cost_meds": "meds",
            "cost_meals": "meals",
        }
        MONTH_NAMES = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}

        total_entries = sum(
            len(entries)
            for months in patientHospitalizationMap.values()
            for entries in months.values()
        )

        print("\n[FHERunner] " + "="*54)
        print("[FHERunner]   Costs per Patient -- FHE Statistics")
        print("[FHERunner] " + "="*54)
        print(f"[FHERunner]   Years in map  : {sorted(patientHospitalizationMap)}")
        print(f"[FHERunner]   Total entries : {total_entries}")

        print(f"\n[FHERunner] STEP 1 -- Decrypt cost fields")
        print(f"[FHERunner]   (decrypting {total_entries * len(COST_FIELD_LABELS)}"
              f" cost ciphertexts ...)\n")

        getter_map = {
            "cost_services": lambda e: e.getCostServices(),
            "cost_hospitalization": lambda e: e.getCostHospitalization(),
            "cost_meds": lambda e: e.getCostMeds(),
            "cost_meals": lambda e: e.getCostMeals(),
        }

        grouped_costs: dict = {}
        processed = 0

        for year, months in patientHospitalizationMap.items():
            grouped_costs[year] = {}
            for month, entries in months.items():
                grouped_costs[year][month] = {
                    lbl: [] for lbl in COST_FIELD_LABELS.values()
                }
                for entry in entries:
                    for field, getter in getter_map.items():
                        label = COST_FIELD_LABELS[field]
                        enc_dict = getter(entry)
                        cents_val = self._decrypt_num_field(enc_dict)
                        dollars = int(round(cents_val / self.scale))
                        grouped_costs[year][month][label].append(
                            min(dollars, self.COST_MAX_DOLLARS)
                        )
                    processed += 1
                    if processed % 300 == 0 or processed == total_entries:
                        pct = processed / total_entries * 100
                        print(f"[FHERunner]   {processed:>5}/{total_entries}  ({pct:.1f}%)")

        print(f"\n[FHERunner] Step 1 complete -- {processed} entries decrypted")

        print(f"\n[FHERunner] STEP 2 -- Using pre-compiled cost sum circuit")
        print(f"[FHERunner]   Circuit bucket size : {self.COST_MAX_BUCKET}")
        print(f"[FHERunner]   Circuit max dollars : ${self.COST_MAX_DOLLARS:,}")

        total_buckets = sum(
            len(cost_groups)
            for months in grouped_costs.values()
            for cost_groups in months.values()
        )
        print(f"\n[FHERunner] STEP 3 -- FHE summation ({total_buckets} buckets)")

        plain_monthly: dict = {}
        bucket_done = 0

        for year, months in grouped_costs.items():
            plain_monthly[year] = {}
            for month, cost_groups in months.items():
                plain_monthly[year][month] = {}
                for cost_label, dollar_list in cost_groups.items():
                    bucket_done += 1

                    if not dollar_list:
                        plain_monthly[year][month][cost_label] = (0, 0)
                        print(f"[FHERunner]   [{bucket_done:>4}/{total_buckets}] "
                              f"{year} {MONTH_NAMES[month]:>3} '{cost_label}' -- no data")
                        continue

                    count = len(dollar_list)
                    plain_sum = 0

                    for chunk_start in range(0, count, self.COST_MAX_BUCKET):
                        chunk  = dollar_list[chunk_start: chunk_start + self.COST_MAX_BUCKET]
                        padded = np.zeros(self.COST_MAX_BUCKET, dtype=np.int64)
                        padded[:len(chunk)] = chunk
                        enc_arr = self.cost_circuit.encrypt(padded)
                        enc_sum = self.cost_circuit.run(enc_arr)
                        plain_sum += int(self.cost_circuit.decrypt(enc_sum))

                    plain_monthly[year][month][cost_label] = (plain_sum, count)
                    avg = round(plain_sum / count, 2)
                    print(f"[FHERunner]   [{bucket_done:>4}/{total_buckets}] "
                          f"{year} {MONTH_NAMES[month]:>3} '{cost_label}' -- "
                          f"sum=${plain_sum:,} / {count} entries = ${avg} avg")

        print(f"[FHERunner] Step 3 complete -- {bucket_done} buckets computed via FHE")

        print(f"\n[FHERunner] STEP 4 -- Assembling result")
        all_labels = list(COST_FIELD_LABELS.values())
        result: dict = {}

        for year, months in plain_monthly.items():
            year_str = str(year)
            yearly_totals = {lbl: [0, 0] for lbl in all_labels}  # [sum_$, count]
            monthly_result: dict = {}

            for month in sorted(months.keys()):
                cost_groups = months[month]
                month_name  = MONTH_NAMES[month]
                monthly_result[month_name] = {}
                for lbl in all_labels:
                    s, c = cost_groups.get(lbl, (0, 0))
                    monthly_result[month_name][lbl] = round(s / c, 2) if c > 0 else None
                    yearly_totals[lbl][0] += s
                    yearly_totals[lbl][1] += c

            general = {
                lbl: (round(yearly_totals[lbl][0] / yearly_totals[lbl][1], 2)
                      if yearly_totals[lbl][1] > 0 else None)
                for lbl in all_labels
            }

            # "general" first, then months in calendar order
            result[year_str] = {"general": general, **monthly_result}

        output_path = PROJECT_ROOT / "costs_per_patient_statistics.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"[FHERunner] Results written --> {output_path}")

        print(f"\n[FHERunner] == Summary ==")
        for year_str, year_data in result.items():
            gen = year_data.get("general", {})
            print(f"\n  {year_str} (overall average per patient):")
            for lbl, val in gen.items():
                print(f"    {lbl:<18} : ${val}")

        return result

    def _decrypt_num_field(self, enc_field_dict: dict) -> int:
        raw_bytes = base64.b64decode(enc_field_dict["ciphertext"])
        enc_val = fhe.Value.deserialize(raw_bytes)
        evaluated = self.num_circuit.run(enc_val)
        return int(self.num_circuit.decrypt(evaluated))

    def generateMoralityRateStatistics(self, patientHospitalizationMap: dict) -> dict:
        WARDS = ["ICU", "ER", "surgery", "hospitalization"]
        WARD_KEYS = {w: w.lower() for w in WARDS}   # "ICU" -> "icu", etc.
        AGE_CATEGORIES = ["under 18", "18 to 65", "over 65"]
        MONTH_NAMES = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}

        total_entries = sum(
            len(entries)
            for months in patientHospitalizationMap.values()
            for entries in months.values()
        )

        print("\n[FHERunner] " + "="*54)
        print("[FHERunner]   Mortality Rate -- FHE Statistics")
        print("[FHERunner] " + "="*54)
        print(f"[FHERunner]   Years in map  : {sorted(patientHospitalizationMap)}")
        print(f"[FHERunner]   Total entries : {total_entries}")

        print(f"\n[FHERunner] STEP 1 -- Decrypt ward, age_category, died fields")
        print(f"[FHERunner]   (decrypting {total_entries * 3} ciphertexts ...)\n")

        grouped: dict = {}
        processed = 0

        for year, months in patientHospitalizationMap.items():
            grouped[year] = {}
            for month, entries in months.items():
                grouped[year][month] = {
                    wk: {cat: [] for cat in AGE_CATEGORIES}
                    for wk in WARD_KEYS.values()
                }
                for entry in entries:
                    ward_plain = self._decrypt_string_field("ward", entry.getWard())
                    age_cat_plain = self._decrypt_string_field("age_category", entry.getAgeCategory())
                    died_val = self._decrypt_num_field(entry.getDied())

                    ward_key = WARD_KEYS.get(ward_plain, ward_plain.lower())

                    if ward_key in grouped[year][month] and \
                       age_cat_plain in grouped[year][month][ward_key]:
                        grouped[year][month][ward_key][age_cat_plain].append(int(died_val))

                    processed += 1
                    if processed % 300 == 0 or processed == total_entries:
                        pct = processed / total_entries * 100
                        print(f"[FHERunner]   {processed:>5}/{total_entries}  ({pct:.1f}%)")

        print(f"\n[FHERunner] Step 1 complete -- {processed} entries decrypted")

        print(f"\n[FHERunner] STEP 2 -- Using pre-compiled mortality sum circuit")
        print(f"[FHERunner]   Circuit bucket size : {self.MORTALITY_MAX_BUCKET}")
        print(f"[FHERunner]   Input values        : binary (0=survived, 1=died)")

        total_buckets = sum(
            len(age_groups)
            for months in grouped.values()
            for ward_groups in months.values()
            for age_groups in ward_groups.values()
        )
        print(f"\n[FHERunner] STEP 3 -- FHE summation ({total_buckets} buckets)")

        plain_monthly: dict = {}
        bucket_done = 0

        for year, months in grouped.items():
            plain_monthly[year] = {}
            for month, ward_groups in months.items():
                plain_monthly[year][month] = {}
                for ward_key, age_groups in ward_groups.items():
                    plain_monthly[year][month][ward_key] = {}
                    for age_cat, died_list in age_groups.items():
                        bucket_done += 1
                        total_count = len(died_list)

                        if total_count == 0:
                            plain_monthly[year][month][ward_key][age_cat] = (0, 0)
                            print(f"[FHERunner]   [{bucket_done:>5}/{total_buckets}] "
                                  f"{year} {MONTH_NAMES[month]:>3} {ward_key:<16} "
                                  f"'{age_cat}' -- no data")
                            continue

                        death_count = 0
                        # Split into chunks of MORTALITY_MAX_BUCKET
                        for chunk_start in range(0, total_count, self.MORTALITY_MAX_BUCKET):
                            chunk  = died_list[chunk_start: chunk_start + self.MORTALITY_MAX_BUCKET]
                            padded = np.zeros(self.MORTALITY_MAX_BUCKET, dtype=np.int64)
                            padded[:len(chunk)] = chunk
                            enc_arr = self.mortality_circuit.encrypt(padded)
                            enc_sum = self.mortality_circuit.run(enc_arr)
                            death_count += int(self.mortality_circuit.decrypt(enc_sum))

                        plain_monthly[year][month][ward_key][age_cat] = (death_count, total_count)
                        rate = round(death_count / total_count * 100, 2)
                        print(f"[FHERunner]   [{bucket_done:>5}/{total_buckets}] "
                              f"{year} {MONTH_NAMES[month]:>3} {ward_key:<16} "
                              f"'{age_cat}' -- {death_count}/{total_count} = {rate}%")

        print(f"[FHERunner] Step 3 complete -- {bucket_done} buckets computed via FHE")

        print(f"\n[FHERunner] STEP 4 -- Assembling result")
        all_ward_keys = list(WARD_KEYS.values())
        result: dict = {}

        for year, months in plain_monthly.items():
            year_str = str(year)
            # yearly_totals[ward_key][age_cat] = [death_sum, total_sum]
            yearly_totals = {
                wk: {cat: [0, 0] for cat in AGE_CATEGORIES}
                for wk in all_ward_keys
            }
            monthly_result: dict = {}

            for month in sorted(months.keys()):
                ward_groups = months[month]
                month_name = MONTH_NAMES[month]
                monthly_result[month_name] = {}
                for wk in all_ward_keys:
                    monthly_result[month_name][wk] = {}
                    for age_cat in AGE_CATEGORIES:
                        deaths, total = ward_groups.get(wk, {}).get(age_cat, (0, 0))
                        monthly_result[month_name][wk][age_cat] = (
                            round(deaths / total * 100, 2) if total > 0 else None
                        )
                        yearly_totals[wk][age_cat][0] += deaths
                        yearly_totals[wk][age_cat][1] += total

            general = {
                wk: {
                    age_cat: (
                        round(yearly_totals[wk][age_cat][0] /
                              yearly_totals[wk][age_cat][1] * 100, 2)
                        if yearly_totals[wk][age_cat][1] > 0 else None
                    )
                    for age_cat in AGE_CATEGORIES
                }
                for wk in all_ward_keys
            }

            result[year_str] = {"general": general, **monthly_result}

        output_path = PROJECT_ROOT / "mortality_rate_statistics.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"[FHERunner] ✓ Results written --> {output_path}")

        print(f"\n[FHERunner] == Summary (overall mortality rates) ==")
        for year_str, year_data in result.items():
            gen = year_data.get("general", {})
            print(f"\n  {year_str}:")
            for wk, age_rates in gen.items():
                rates_str = "  ".join(
                    f"{cat}: {val}%" if val is not None else f"{cat}: N/A"
                    for cat, val in age_rates.items()
                )
                print(f"    {wk:<16} | {rates_str}")

        return result

    def generateHospitalExpensesStatistics(self, hospitalExpenseMap: dict) -> dict:
        EXPENSE_TYPES = ["Equipment", "Medicine", "Personnel", "Renovations", "Supplies"]
        TYPE_KEYS = {t: t.lower() for t in EXPENSE_TYPES}
        ALL_TYPE_KEYS = list(TYPE_KEYS.values())
        MONTH_NAMES = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}

        total_entries = sum(
            len(entries)
            for months in hospitalExpenseMap.values()
            for entries in months.values()
        )

        print("\n[FHERunner] " + "="*56)
        print("[FHERunner]   Hospital Expenses -- FHE Statistics")
        print("[FHERunner] " + "="*56)
        print(f"[FHERunner]   Years in map  : {sorted(hospitalExpenseMap)}")
        print(f"[FHERunner]   Total entries : {total_entries}")

        print(f"\n[FHERunner] STEP 1 -- Decrypt expense_type & amount fields")
        print(f"[FHERunner]   (decrypting {total_entries * 2} ciphertexts ...)\n")

        grouped: dict = {}
        processed = 0

        for year, months in hospitalExpenseMap.items():
            grouped[year] = {}
            for month, entries in months.items():
                grouped[year][month] = {tk: [] for tk in ALL_TYPE_KEYS}
                for entry in entries:
                    # Decrypt expense_type (string field)
                    exp_type = self._decrypt_expense_str_field(
                        "expense_type", entry.getExpenseType()
                    )
                    # Decrypt amount (numeric field) -> cents -> dollars
                    cents = self._decrypt_expense_num_field(entry.getAmount())
                    dollars = int(round(cents / self.exp_scale))
                    dollars = min(dollars, self.EXPENSE_MAX_DOLLARS)

                    type_key = TYPE_KEYS.get(exp_type, exp_type.lower())
                    if type_key in grouped[year][month]:
                        grouped[year][month][type_key].append(dollars)

                    processed += 1
                    if processed % 200 == 0 or processed == total_entries:
                        pct = processed / total_entries * 100
                        print(f"[FHERunner]   {processed:>5}/{total_entries}  ({pct:.1f}%)")

        print(f"\n[FHERunner] Step 1 complete -- {processed} entries decrypted")

        print(f"\n[FHERunner] STEP 2 -- Using pre-compiled expense sum circuit")
        print(f"[FHERunner]   Circuit bucket size : {self.EXPENSE_MAX_BUCKET}")
        print(f"[FHERunner]   Circuit max dollars : ${self.EXPENSE_MAX_DOLLARS:,}")

        total_buckets = sum(
            len(type_groups)
            for months in grouped.values()
            for type_groups in months.values()
        )
        print(f"\n[FHERunner] STEP 3 -- FHE summation ({total_buckets} buckets)")

        plain_monthly: dict = {}
        bucket_done = 0

        for year, months in grouped.items():
            plain_monthly[year] = {}
            for month, type_groups in months.items():
                plain_monthly[year][month] = {}
                for type_key, dollar_list in type_groups.items():
                    bucket_done += 1

                    if not dollar_list:
                        plain_monthly[year][month][type_key] = (0, 0)
                        print(f"[FHERunner]   [{bucket_done:>4}/{total_buckets}] "
                              f"{year} {MONTH_NAMES[month]:>3} '{type_key}' -- no data")
                        continue

                    count = len(dollar_list)
                    plain_sum = 0

                    for chunk_start in range(0, count, self.EXPENSE_MAX_BUCKET):
                        chunk = dollar_list[chunk_start: chunk_start + self.EXPENSE_MAX_BUCKET]
                        padded = np.zeros(self.EXPENSE_MAX_BUCKET, dtype=np.int64)
                        padded[:len(chunk)] = chunk
                        enc_arr = self.expense_sum_circuit.encrypt(padded)
                        enc_sum = self.expense_sum_circuit.run(enc_arr)
                        plain_sum += int(self.expense_sum_circuit.decrypt(enc_sum))

                    plain_monthly[year][month][type_key] = (plain_sum, count)
                    avg = round(plain_sum / count, 2)
                    print(f"[FHERunner]   [{bucket_done:>4}/{total_buckets}] "
                          f"{year} {MONTH_NAMES[month]:>3} '{type_key}' -- "
                          f"sum=${plain_sum:,} / {count} entries = ${avg} avg")

        print(f"[FHERunner] Step 3 complete -- {bucket_done} buckets computed via FHE")

        print(f"\n[FHERunner] STEP 4 -- Assembling result")
        result: dict = {}

        for year, months in plain_monthly.items():
            year_str = str(year)
            yearly_totals = {tk: [0, 0] for tk in ALL_TYPE_KEYS}
            monthly_result: dict = {}

            for month in sorted(months.keys()):
                type_groups = months[month]
                month_name = MONTH_NAMES[month]
                monthly_result[month_name] = {}
                for tk in ALL_TYPE_KEYS:
                    s, c = type_groups.get(tk, (0, 0))
                    monthly_result[month_name][tk] = round(s / c, 2) if c > 0 else None
                    yearly_totals[tk][0] += s
                    yearly_totals[tk][1] += c

            general = {
                tk: (round(yearly_totals[tk][0] / yearly_totals[tk][1], 2)
                     if yearly_totals[tk][1] > 0 else None)
                for tk in ALL_TYPE_KEYS
            }

            result[year_str] = {"general": general, **monthly_result}

        output_path = PROJECT_ROOT / "hospital_expenses_statistics.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"[FHERunner] ✓ Results written --> {output_path}")

        print(f"\n[FHERunner] == Summary (overall avg per expense type) ==")
        for year_str, year_data in result.items():
            gen = year_data.get("general", {})
            print(f"\n  {year_str}:")
            for tk, val in gen.items():
                print(f"    {tk:<14} : ${val}")

        return result

    def _decrypt_expense_str_field(self, field: str, enc_field_dict: dict) -> str:
        raw_bytes = base64.b64decode(enc_field_dict["ciphertext"])
        enc_val = fhe.Value.deserialize(raw_bytes)
        circuit = self.exp_str_circuits[field]
        evaluated = circuit.run(enc_val)
        arr = circuit.decrypt(evaluated)
        orig_len = enc_field_dict["original_length"]
        return bytes(int(x) for x in arr[:orig_len]).decode("utf-8")

    def _decrypt_expense_num_field(self, enc_field_dict: dict) -> int:
        raw_bytes = base64.b64decode(enc_field_dict["ciphertext"])
        enc_val = fhe.Value.deserialize(raw_bytes)
        evaluated = self.exp_num_circuit.run(enc_val)
        return int(self.exp_num_circuit.decrypt(evaluated))

    def encryptHospitalExpense(self, hospitalExpense: HospitalExpense) -> HospitalExpense:
        raw_amount = hospitalExpense.getAmount()
        cents = np.int64(min(int(round(raw_amount * self.exp_scale)),
                                  self.exp_max_amt_cents))
        enc_amount = self.exp_num_circuit.encrypt(cents)
        amount_dict = {
            "ciphertext": base64.b64encode(enc_amount.serialize()).decode("utf-8"),
            "scale":      self.exp_scale,
        }

        # ── Encrypt string fields (UTF-8 bytes, zero-padded to max_len) ───────
        enc_str_dicts: dict = {}
        for field, raw_value in [
            ("description",  hospitalExpense.getDescription()),
            ("expense_type", hospitalExpense.getExpenseType()),
        ]:
            encoded = raw_value.encode("utf-8")
            max_len = self.exp_str_max_lens[field]
            if len(encoded) > max_len:
                raise ValueError(
                    f"[FHERunner] encryptHospitalExpense: field '{field}' "
                    f"is {len(encoded)} bytes but circuit max_len is {max_len}."
                )
            arr = np.zeros(max_len, dtype=np.int64)
            arr[:len(encoded)] = list(encoded)
            enc_arr = self.exp_str_circuits[field].encrypt(arr)
            enc_str_dicts[field] = {
                "ciphertext": base64.b64encode(enc_arr.serialize()).decode("utf-8"),
                "original_length": len(encoded),
                "max_len": max_len,
            }

        result = HospitalExpense()
        result.setId(hospitalExpense.getId())
        expense_date = hospitalExpense.getExpenseDate()
        if hasattr(expense_date, "strftime"):
            expense_date = expense_date.strftime("%d.%m.%Y")
        result.setExpenseDate(expense_date)             # stays plaintext
        result.setAmount(amount_dict)
        result.setDescription(enc_str_dicts["description"])
        result.setExpenseType(enc_str_dicts["expense_type"])

        print(f"[FHERunner] encryptHospitalExpense — uuid={hospitalExpense.getId()}")
        return result

    def encryptPatientHospitalization(self, patientHospitalization: PatientHospitalization) -> PatientHospitalization:
        result = PatientHospitalization()

        result.setId(patientHospitalization.getId())

        for date_val, setter in [
            (patientHospitalization.getAdmissionDate(), result.setAdmissionDate),
            (patientHospitalization.getDischargeDate(), result.setDischargeDate),
        ]:
            if date_val is not None and hasattr(date_val, "strftime"):
                date_val = date_val.strftime("%d.%m.%Y")
            setter(date_val)

        pid = patientHospitalization.getPatientId()
        if pid is not None:
            enc = self.num_circuit.encrypt(np.int64(int(pid)))
            result.setPatientId({
                "ciphertext": base64.b64encode(enc.serialize()).decode("utf-8"),
                "scale": 1,
            })

        died = patientHospitalization.getDied()
        if died is not None:
            enc = self.num_circuit.encrypt(np.int64(1 if died else 0))
            result.setDied({
                "ciphertext": base64.b64encode(enc.serialize()).decode("utf-8"),
                "scale": 1,
            })

        for getter, setter in [
            (patientHospitalization.getCostServices, result.setCostServices),
            (patientHospitalization.getCostHospitalization, result.setCostHospitalization),
            (patientHospitalization.getCostMeds, result.setCostMeds),
            (patientHospitalization.getCostMeals, result.setCostMeals),
        ]:
            val = getter()
            if val is not None:
                cents = np.int64(int(round(val * self.scale)))
                enc = self.num_circuit.encrypt(cents)
                setter({
                    "ciphertext": base64.b64encode(enc.serialize()).decode("utf-8"),
                    "scale": self.scale,
                })

        for field, getter, setter in [
            ("name", patientHospitalization.getName, result.setName),
            ("age_category", patientHospitalization.getAgeCategory, result.setAgeCategory),
            ("diagnosis", patientHospitalization.getDiagnosis, result.setDiagnosis),
            ("ward", patientHospitalization.getWard, result.setWard),
        ]:
            val = getter()
            if val is not None:
                encoded = val.encode("utf-8")
                max_len = self.str_max_lens[field]
                if len(encoded) > max_len:
                    raise ValueError(
                        f"[FHERunner] encryptPatientHospitalization: field '{field}' "
                        f"is {len(encoded)} bytes but circuit max_len is {max_len}."
                    )
                arr = np.zeros(max_len, dtype=np.int64)
                arr[:len(encoded)] = list(encoded)
                enc = self.str_circuits[field].encrypt(arr)
                setter({
                    "ciphertext": base64.b64encode(enc.serialize()).decode("utf-8"),
                    "original_length": len(encoded),
                    "max_len": max_len,
                })

        print(f"[FHERunner] encryptPatientHospitalization — uuid={patientHospitalization.getId()}")
        return result

    def checkIfSamePatient(self, openPatientHospitalization: PatientHospitalization, patientHospitalization: PatientHospitalization) -> bool:
        def _resolve_pid(pid_val) -> int:
            if isinstance(pid_val, dict):
                return self._decrypt_num_field(pid_val)
            return int(pid_val)

        open_pid = _resolve_pid(openPatientHospitalization.getPatientId())
        new_pid = _resolve_pid(patientHospitalization.getPatientId())
        return open_pid == new_pid

    def mergeAndEncryptPatientHospitalization(self, openPatientHospitalization: PatientHospitalization, patientHospitalization: PatientHospitalization,) -> PatientHospitalization:
        result = PatientHospitalization()

        result.setId(openPatientHospitalization.getId())
        result.setAdmissionDate(openPatientHospitalization.getAdmissionDate())

        discharge = patientHospitalization.getDischargeDate()
        if discharge is not None:
            if hasattr(discharge, "strftime"):
                discharge = discharge.strftime("%d.%m.%Y")
            result.setDischargeDate(discharge)
        else:
            result.setDischargeDate(openPatientHospitalization.getDischargeDate())

        pid = patientHospitalization.getPatientId()
        if pid is not None:
            enc = self.num_circuit.encrypt(np.int64(int(pid)))
            result.setPatientId({
                "ciphertext": base64.b64encode(enc.serialize()).decode("utf-8"),
                "scale": 1,
            })
        else:
            result.setPatientId(openPatientHospitalization.getPatientId())

        died = patientHospitalization.getDied()
        if died is not None:
            enc = self.num_circuit.encrypt(np.int64(1 if died else 0))
            result.setDied({
                "ciphertext": base64.b64encode(enc.serialize()).decode("utf-8"),
                "scale": 1,
            })
        else:
            result.setDied(openPatientHospitalization.getDied())

        for field, getter_new, getter_open, setter in [
            ("name", patientHospitalization.getName, openPatientHospitalization.getName, result.setName),
            ("age_category", patientHospitalization.getAgeCategory, openPatientHospitalization.getAgeCategory, result.setAgeCategory),
            ("diagnosis", patientHospitalization.getDiagnosis, openPatientHospitalization.getDiagnosis, result.setDiagnosis),
            ("ward", patientHospitalization.getWard, openPatientHospitalization.getWard, result.setWard),
        ]:
            val = getter_new()
            if val is not None:
                encoded = val.encode("utf-8")
                max_len = self.str_max_lens[field]
                if len(encoded) > max_len:
                    raise ValueError(
                        f"[FHERunner] mergeAndEncrypt: field '{field}' "
                        f"is {len(encoded)} bytes but circuit max_len is {max_len}."
                    )
                arr = np.zeros(max_len, dtype=np.int64)
                arr[:len(encoded)] = list(encoded)
                enc = self.str_circuits[field].encrypt(arr)
                setter({
                    "ciphertext": base64.b64encode(enc.serialize()).decode("utf-8"),
                    "original_length": len(encoded),
                    "max_len": max_len,
                })
            else:
                setter(getter_open())

        for getter_new, getter_open, setter in [
            (patientHospitalization.getCostServices, openPatientHospitalization.getCostServices, result.setCostServices),
            (patientHospitalization.getCostHospitalization, openPatientHospitalization.getCostHospitalization, result.setCostHospitalization),
            (patientHospitalization.getCostMeds, openPatientHospitalization.getCostMeds, result.setCostMeds),
            (patientHospitalization.getCostMeals, openPatientHospitalization.getCostMeals, result.setCostMeals),
        ]:
            new_cost = getter_new()
            open_enc = getter_open()

            existing_cents = (self._decrypt_num_field(open_enc)
                              if open_enc is not None else 0)
            new_cents = int(round((new_cost or 0.0) * self.scale))
            total_cents = np.int64(existing_cents + new_cents)

            enc = self.num_circuit.encrypt(total_cents)
            setter({
                "ciphertext": base64.b64encode(enc.serialize()).decode("utf-8"),
                "scale": self.scale,
            })

        print(f"[FHERunner] mergeAndEncryptPatientHospitalization "
              f"— uuid={openPatientHospitalization.getId()}")
        return result

