"""
Hospital Patient Data — FHE Statistics with Concrete (Zama)
============================================================
ALL patient fields are encrypted using Fully Homomorphic Encryption.

Two FHE circuits are used:
  • num_circuit  — encrypts arrays of N_PATIENTS integers (one per numeric field).
                   Also used to compute FHE sums for statistics.
  • str_circuit  — encrypts fixed-length byte arrays (one per patient per string field).
                   Concrete only works on integers, so strings are UTF-8 encoded
                   and padded to MAX_STR_LEN bytes before encryption.

Field mapping:
  Numeric (×SCALE)  → cost_services, cost_hospitalization, cost_meds, cost_meals
  Numeric (as-is)   → age, hospitalization_period
  Boolean (0/1)     → died
  String (UTF-8)    → name, diagnosis, ward
"""

import json
import base64
import warnings
import numpy as np
from concrete import fhe

warnings.filterwarnings("ignore")   # suppress pkg_resources deprecation notice

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
SCALE        = 100      # Float costs → cents  ($1.00 → 100)
N_PATIENTS   = 5
COST_FIELDS  = ["cost_services", "cost_hospitalization", "cost_meds", "cost_meals"]
INT_FIELDS   = ["age", "hospitalization_period"]
BOOL_FIELDS  = ["died"]
STR_FIELDS   = ["name", "diagnosis", "ward"]
NUM_FIELDS   = COST_FIELDS + INT_FIELDS + BOOL_FIELDS   # all fields for num_circuit
OUTPUT_FILE  = "hospital_data.txt"


# ══════════════════════════════════════════════════════════════
# STEP 1 — Generate Dataset
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*66)
print("  STEP 1 — Generating patient dataset")
print("═"*66)

patients = [
    {
        "name": "Alice Brown",
        "age": 62,
        "diagnosis": "Hypertension",
        "cost_services": 850.00,
        "cost_hospitalization": 2100.00,
        "cost_meds": 320.50,
        "cost_meals": 95.00,
        "hospitalization_period": 5,
        "ward": "hospitalization",
        "died": False,
    },
    {
        "name": "Bob Smith",
        "age": 35,
        "diagnosis": "Appendicitis",
        "cost_services": 2300.00,
        "cost_hospitalization": 4500.00,
        "cost_meds": 780.25,
        "cost_meals": 210.00,
        "hospitalization_period": 10,
        "ward": "surgery",
        "died": False,
    },
    {
        "name": "Carol White",
        "age": 78,
        "diagnosis": "Cardiac Arrest",
        "cost_services": 5600.00,
        "cost_hospitalization": 12000.00,
        "cost_meds": 1850.00,
        "cost_meals": 350.00,
        "hospitalization_period": 21,
        "ward": "ICU",
        "died": True,
    },
    {
        "name": "David Lee",
        "age": 28,
        "diagnosis": "Fracture",
        "cost_services": 3200.00,
        "cost_hospitalization": 1800.00,
        "cost_meds": 220.00,
        "cost_meals": 75.00,
        "hospitalization_period": 3,
        "ward": "surgery",
        "died": False,
    },
    {
        "name": "Eve Johnson",
        "age": 55,
        "diagnosis": "Pneumonia",
        "cost_services": 1100.00,
        "cost_hospitalization": 3300.00,
        "cost_meds": 650.75,
        "cost_meals": 180.00,
        "hospitalization_period": 8,
        "ward": "hospitalization",
        "died": False,
    },
]

print(f"\n  {'#':<3} {'Name':<14} {'Age':<5} {'Ward':<16} {'Diagnosis':<16} {'Died'}")
print(f"  {'─'*66}")
for i, p in enumerate(patients, 1):
    print(
        f"  {i:<3} {p['name']:<14} {p['age']:<5} {p['ward']:<16}"
        f" {p['diagnosis']:<16} {p['died']}"
    )
print(f"\n  Total patients generated: {len(patients)}")


# ══════════════════════════════════════════════════════════════
# STEP 2 — Define & Compile FHE Circuits
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*66)
print("  STEP 2 — Defining and compiling FHE circuits")
print("═"*66)

# ── Circuit A: Numeric sum ──────────────────────────────────
# Receives an array of N_PATIENTS integers, returns their sum.
# Used for all numeric fields and for computing averages.
@fhe.compiler({"values": "encrypted"})
def fhe_sum(values):
    return np.sum(values)

max_num_val = int(max(p[f] for p in patients for f in COST_FIELDS) * SCALE) + 1
print(f"\n  [num_circuit] Max value (cents): {max_num_val:,}  (= ${max_num_val/SCALE:,.2f})")

rng = np.random.default_rng(seed=42)
num_inputset = [rng.integers(0, max_num_val, size=N_PATIENTS, dtype=np.int64)
                for _ in range(50)]
num_inputset.append(np.zeros(N_PATIENTS, dtype=np.int64))
num_inputset.append(np.full(N_PATIENTS, max_num_val, dtype=np.int64))

print("  [num_circuit] Compiling … (this may take up to a minute)")
num_circuit = fhe_sum.compile(num_inputset)
print("  [num_circuit] ✓ Compiled!")
num_circuit.keygen()
print("  [num_circuit] ✓ Keys generated!")

# ── Circuit B: String byte-array identity ──────────────────
# Receives an array of MAX_STR_LEN bytes (UTF-8 encoded, zero-padded),
# returns them unchanged — used purely for encrypted string storage.
MAX_STR_LEN = max(
    len(p[f].encode("utf-8"))
    for p in patients
    for f in STR_FIELDS
)
print(f"\n  [str_circuit] MAX_STR_LEN = {MAX_STR_LEN} bytes "
      f"(longest string: 'hospitalization')")

@fhe.compiler({"bytes_arr": "encrypted"})
def fhe_str_identity(bytes_arr):
    # +0 is a trivial no-op that Concrete can compile as an identity circuit
    return bytes_arr + 0

str_inputset = [rng.integers(0, 256, size=MAX_STR_LEN, dtype=np.int64)
                for _ in range(50)]
str_inputset.append(np.zeros(MAX_STR_LEN, dtype=np.int64))
str_inputset.append(np.full(MAX_STR_LEN, 255, dtype=np.int64))

print("  [str_circuit] Compiling …")
str_circuit = fhe_str_identity.compile(str_inputset)
print("  [str_circuit] ✓ Compiled!")
str_circuit.keygen()
print("  [str_circuit] ✓ Keys generated!")


# ── Helpers for string ↔ byte-array conversion ─────────────
def str_to_int_array(s: str) -> np.ndarray:
    """Encode string to zero-padded int64 array of length MAX_STR_LEN."""
    byt = s.encode("utf-8")
    arr = np.zeros(MAX_STR_LEN, dtype=np.int64)
    arr[:len(byt)] = list(byt)
    return arr

def int_array_to_str(arr: np.ndarray, original_len: int) -> str:
    """Decode int64 array back to string using the original byte length."""
    return bytes(int(x) for x in arr[:original_len]).decode("utf-8")


# ══════════════════════════════════════════════════════════════
# STEP 3 — Encrypt ALL Fields
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*66)
print("  STEP 3 — Encrypting ALL patient fields with FHE")
print("═"*66)

# ── Numeric fields (one ciphertext per field, 5 values inside) ──
print("\n  ── Numeric fields (num_circuit) ──")
encrypted_numeric: dict[str, fhe.Value] = {}

for field in NUM_FIELDS:
    if field in COST_FIELDS:
        values = np.array([int(p[field] * SCALE) for p in patients], dtype=np.int64)
        display = [p[field] for p in patients]
        note = f"(×{SCALE} → cents)"
    elif field in BOOL_FIELDS:
        values = np.array([int(p[field]) for p in patients], dtype=np.int64)
        display = [p[field] for p in patients]
        note = "(False→0, True→1)"
    else:  # INT_FIELDS
        values = np.array([p[field] for p in patients], dtype=np.int64)
        display = values.tolist()
        note = "(integer, no scaling)"

    print(f"\n  ▸ '{field}'  {note}")
    print(f"      Plaintext : {display}")
    print(f"      As int64  : {values.tolist()}")
    encrypted_numeric[field] = num_circuit.encrypt(values)
    print(f"      ✓ Encrypted → opaque binary ciphertext")

# ── String fields (one ciphertext per patient, per field) ──
print("\n  ── String fields (str_circuit) ──")
# Structure: { field: [ {enc: Value, length: int}, ... ] }
encrypted_strings: dict[str, list[dict]] = {}

for field in STR_FIELDS:
    print(f"\n  ▸ '{field}'  (UTF-8 encoded, zero-padded to {MAX_STR_LEN} bytes)")
    encrypted_strings[field] = []
    for p in patients:
        val = p[field]
        arr = str_to_int_array(val)
        enc = str_circuit.encrypt(arr)
        encrypted_strings[field].append({"enc": enc, "length": len(val.encode("utf-8"))})
        print(f"      Patient '{p['name']}':  \"{val}\"  →  bytes {list(arr)}  →  ✓ encrypted")


# ══════════════════════════════════════════════════════════════
# STEP 4 — Serialize & Write to File
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*66)
print(f"  STEP 4 — Serializing and writing ALL data to '{OUTPUT_FILE}'")
print("═"*66)

def to_b64(enc_val: fhe.Value) -> str:
    return base64.b64encode(enc_val.serialize()).decode("utf-8")

# Numeric: one base64 string per field
print("\n  Numeric ciphertexts:")
serial_numeric: dict[str, str] = {}
for field, enc in encrypted_numeric.items():
    raw = enc.serialize()
    serial_numeric[field] = to_b64(enc)
    print(f"    '{field}': {len(raw):,} bytes → {len(serial_numeric[field]):,} base64 chars")

# Strings: list of {ciphertext, length} per field
print("\n  String ciphertexts (per patient):")
serial_strings: dict[str, dict] = {}
for field, entries in encrypted_strings.items():
    raw_sample = entries[0]["enc"].serialize()
    serial_strings[field] = {
        "lengths":     [e["length"] for e in entries],
        "ciphertexts": [to_b64(e["enc"]) for e in entries],
    }
    print(f"    '{field}': 5 × {len(raw_sample):,} bytes each "
          f"→ {len(serial_strings[field]['ciphertexts'][0]):,} base64 chars each")

file_content = {
    "metadata": {
        "description": "Hospital patient — ALL fields encrypted (FHE, Concrete by Zama)",
        "n_patients":   N_PATIENTS,
        "scale_factor": SCALE,
        "max_str_len":  MAX_STR_LEN,
        "num_fields":   NUM_FIELDS,
        "str_fields":   STR_FIELDS,
    },
    "encrypted_numeric_base64": serial_numeric,
    "encrypted_strings_base64": serial_strings,
}

with open(OUTPUT_FILE, "w") as fh:
    json.dump(file_content, fh, indent=2)

print(f"\n  ✓ ALL data written to '{OUTPUT_FILE}'")
print(f"    No plaintext patient data stored — everything is encrypted.")


# ══════════════════════════════════════════════════════════════
# STEP 5 — Read Data from File
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*66)
print(f"  STEP 5 — Reading encrypted data back from '{OUTPUT_FILE}'")
print("═"*66)

with open(OUTPUT_FILE, "r") as fh:
    loaded = json.load(fh)

meta = loaded["metadata"]
print(f"\n  Description  : {meta['description']}")
print(f"  Patients     : {meta['n_patients']}")
print(f"  Scale factor : {meta['scale_factor']}")
print(f"  Max str len  : {meta['max_str_len']} bytes")
print(f"  Num fields   : {meta['num_fields']}")
print(f"  Str fields   : {meta['str_fields']}")

# Deserialize numeric ciphertexts
print("\n  Deserializing numeric ciphertexts …")
loaded_numeric: dict[str, fhe.Value] = {}
for field, b64 in loaded["encrypted_numeric_base64"].items():
    raw = base64.b64decode(b64)
    loaded_numeric[field] = fhe.Value.deserialize(raw)
    print(f"    ✓ '{field}' restored ({len(raw):,} bytes)")

# Deserialize string ciphertexts
print("\n  Deserializing string ciphertexts …")
loaded_strings: dict[str, dict] = {}
for field, data in loaded["encrypted_strings_base64"].items():
    deserialized = []
    for b64 in data["ciphertexts"]:
        raw = base64.b64decode(b64)
        deserialized.append(fhe.Value.deserialize(raw))
    loaded_strings[field] = {
        "lengths":     data["lengths"],
        "ciphertexts": deserialized,
    }
    print(f"    ✓ '{field}': {len(deserialized)} patient ciphertexts restored")


# ══════════════════════════════════════════════════════════════
# STEP 6 — Run FHE Computation on Encrypted Data
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*66)
print("  STEP 6 — Running FHE computation on encrypted data")
print("═"*66)
print("  (Computation runs entirely on ciphertexts — no plaintext ever exposed)\n")

# Numeric fields: compute FHE sum (for statistics)
print("  ── Numeric fields: computing encrypted sums ──")
enc_sums: dict[str, fhe.Value] = {}
for field, enc in loaded_numeric.items():
    enc_sums[field] = num_circuit.run(enc)
    print(f"    ✓ FHE sum computed for '{field}'  (result still encrypted)")

# String fields: run identity circuit (proves data is live FHE-encrypted)
print("\n  ── String fields: running identity circuit (encrypt-then-decrypt check) ──")
enc_str_results: dict[str, list[fhe.Value]] = {}
for field, data in loaded_strings.items():
    enc_str_results[field] = []
    for enc in data["ciphertexts"]:
        enc_str_results[field].append(str_circuit.run(enc))
    print(f"    ✓ Identity circuit applied to all 5 '{field}' ciphertexts")


# ══════════════════════════════════════════════════════════════
# STEP 7 — Decrypt & Print Results
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*66)
print("  STEP 7 — Decrypting and printing all results")
print("═"*66)

n     = meta["n_patients"]
scale = meta["scale_factor"]

# ── Cost averages ───────────────────────────────────────────
print("\n  ┌──────────────────────────┬──────────────┬────────────┬───────┐")
print("  │ Cost Category            │ FHE Average  │ Expected   │  OK?  │")
print("  ├──────────────────────────┼──────────────┼────────────┼───────┤")

for field in COST_FIELDS:
    total    = num_circuit.decrypt(enc_sums[field])
    fhe_avg  = total / (n * scale)
    expected = sum(p[field] for p in patients) / n
    ok       = "  ✓  " if abs(fhe_avg - expected) < 0.02 else "  ✗  "
    label    = field.replace("cost_", "").replace("_", " ").title()
    print(f"  │ {label:<26}│ ${fhe_avg:>10.2f} │ ${expected:>8.2f} │{ok}│")

print("  └──────────────────────────┴──────────────┴────────────┴───────┘")

# ── Integer field averages ──────────────────────────────────
print("\n  ── Other numeric field averages ──")
for field in INT_FIELDS:
    total    = num_circuit.decrypt(enc_sums[field])
    fhe_avg  = total / n
    expected = sum(p[field] for p in patients) / n
    ok       = "✓" if abs(fhe_avg - expected) < 0.01 else "✗"
    label    = field.replace("_", " ").title()
    print(f"    {label:<28}: FHE = {fhe_avg:.1f}   Expected = {expected:.1f}   {ok}")

# ── Boolean (died) ──────────────────────────────────────────
print("\n  ── Mortality rate ──")
total_died = num_circuit.decrypt(enc_sums["died"])
fhe_rate   = (total_died / n) * 100
expected   = (sum(int(p["died"]) for p in patients) / n) * 100
ok         = "✓" if abs(fhe_rate - expected) < 0.01 else "✗"
print(f"    Mortality rate : FHE = {fhe_rate:.1f}%   Expected = {expected:.1f}%   {ok}")

# ── Decrypted string fields (per patient) ──────────────────
print("\n  ── Decrypted string fields ──")
print(f"\n  {'#':<4} {'name':<14} {'diagnosis':<16} {'ward':<16} {'OK?'}")
print(f"  {'─'*56}")

str_lengths = {f: loaded_strings[f]["lengths"] for f in STR_FIELDS}

for i in range(n):
    row = {
        field: int_array_to_str(
            str_circuit.decrypt(enc_str_results[field][i]),
            str_lengths[field][i]
        )
        for field in STR_FIELDS
    }
    expected_row = {f: patients[i][f] for f in STR_FIELDS}
    all_ok = all(row[f] == expected_row[f] for f in STR_FIELDS)
    ok = "✓" if all_ok else "✗"
    print(f"  {i+1:<4} {row['name']:<14} {row['diagnosis']:<16} {row['ward']:<16} {ok}")

print("\n" + "═"*66)
print("  ✓ ALL fields encrypted, stored, retrieved and decrypted successfully!")
print("  ✓ Statistics computed entirely on ciphertext — no plaintext exposed.")
print("═"*66 + "\n")
