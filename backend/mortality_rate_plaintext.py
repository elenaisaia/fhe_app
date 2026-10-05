"""
mortality_rate_plaintext.py
────────────────────────────
Computes mortality rate statistics (%) over the PLAINTEXT data from
patient_hospitalizations.json.

Output structure (mirrors the FHE version in FHERunner):
  {
    "2023": {
      "general": {
        "icu":             {"under 18": rate%, "18 to 65": rate%, "over 65": rate%},
        "er":              {...},
        "surgery":         {...},
        "hospitalization": {...}
      },
      "Jan": { "icu": {...}, "er": {...}, "surgery": {...}, "hospitalization": {...} },
      ...
    },
    ...
  }

Mortality rate = (deaths / total patients in bucket) * 100, rounded to 2 dp.

Results are written to mortality-rate-plaintext-statistics.json.
"""

import json
from datetime import datetime
from pathlib import Path

INPUT_FILE  = Path(__file__).parent / "patient_hospitalizations.json"
OUTPUT_FILE = Path(__file__).parent / "mortality-rate-plaintext-statistics.json"

WARDS          = ["ICU", "ER", "surgery", "hospitalization"]
WARD_KEYS      = {w: w.lower() for w in WARDS}   # "ICU" -> "icu"
ALL_WARD_KEYS  = list(WARD_KEYS.values())
AGE_CATEGORIES = ["under 18", "18 to 65", "over 65"]
MONTH_NAMES    = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr",
                  5:"May", 6:"Jun", 7:"Jul", 8:"Aug",
                  9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}

# ── Load ──────────────────────────────────────────────────────────────────────
print("\n" + "="*62)
print("  Plaintext  --  Mortality Rate Statistics")
print("="*62)

with open(INPUT_FILE) as f:
    data = json.load(f)

print(f"\n  Loaded {len(data)} entries from '{INPUT_FILE.name}'")

# ── Group (discharge_year, discharge_month, ward_key, age_category) ───────────
# grouped[year][month][ward_key][age_cat] = [died_0_or_1, ...]
grouped: dict = {}
skipped = 0

for entry in data:
    discharge_str = entry.get("discharge_date")
    ward_raw      = (entry.get("ward") or "").strip()
    age_cat       = (entry.get("age_category") or "").strip()
    died          = entry.get("died", False)

    if not discharge_str:
        skipped += 1
        continue

    discharge = datetime.strptime(discharge_str, "%d.%m.%Y")
    year      = discharge.year
    month     = discharge.month
    ward_key  = WARD_KEYS.get(ward_raw, ward_raw.lower())

    grouped.setdefault(year, {})
    grouped[year].setdefault(month, {
        wk: {cat: [] for cat in AGE_CATEGORIES}
        for wk in ALL_WARD_KEYS
    })

    if ward_key in grouped[year][month] and age_cat in grouped[year][month][ward_key]:
        grouped[year][month][ward_key][age_cat].append(1 if died else 0)

if skipped:
    print(f"  Warning: skipped {skipped} entries with missing discharge_date")

years_found = sorted(grouped)
print(f"  Years in data : {years_found}\n")

# ── Compute mortality rates & build result dict ───────────────────────────────
result: dict = {}

for year in years_found:
    year_str      = str(year)
    monthly_result: dict = {}
    # yearly_totals[ward_key][age_cat] = [death_sum, total_count]
    yearly_totals = {wk: {cat: [0, 0] for cat in AGE_CATEGORIES} for wk in ALL_WARD_KEYS}

    for month in sorted(grouped[year].keys()):
        month_name  = MONTH_NAMES[month]
        ward_groups = grouped[year][month]
        monthly_result[month_name] = {}

        for wk in ALL_WARD_KEYS:
            monthly_result[month_name][wk] = {}
            for age_cat in AGE_CATEGORIES:
                died_list   = ward_groups.get(wk, {}).get(age_cat, [])
                total_count = len(died_list)
                death_count = sum(died_list)

                if total_count > 0:
                    rate = round(death_count / total_count * 100, 2)
                    yearly_totals[wk][age_cat][0] += death_count
                    yearly_totals[wk][age_cat][1] += total_count
                else:
                    rate = None

                monthly_result[month_name][wk][age_cat] = rate

    # Yearly "general"
    general = {
        wk: {
            age_cat: (
                round(yearly_totals[wk][age_cat][0] /
                      yearly_totals[wk][age_cat][1] * 100, 2)
                if yearly_totals[wk][age_cat][1] > 0 else None
            )
            for age_cat in AGE_CATEGORIES
        }
        for wk in ALL_WARD_KEYS
    }

    # "general" first, then months in calendar order
    result[year_str] = {"general": general, **monthly_result}

# ── Print summary ─────────────────────────────────────────────────────────────
for year_str, year_data in result.items():
    gen = year_data["general"]
    print(f"  -- {year_str}  (full-year mortality rates) --")
    col_w = 12
    header = f"  {'Ward':<18}" + "".join(f"  {cat:<{col_w}}" for cat in AGE_CATEGORIES)
    print(header)
    print("  " + "-" * (len(header) - 2))
    for wk in ALL_WARD_KEYS:
        row = f"  {wk:<18}" + "".join(
            f"  {(str(gen[wk].get(cat, '-'))+'%'):<{col_w}}" for cat in AGE_CATEGORIES
        )
        print(row)
    print()

    print(f"  {year_str}  (monthly breakdown — deaths/total):")
    for month_name, ward_groups in year_data.items():
        if month_name == "general":
            continue
        print(f"\n    {month_name}:")
        for wk in ALL_WARD_KEYS:
            row = f"      {wk:<18}" + "".join(
                f"  {(str(ward_groups[wk].get(cat, '-'))+'%') if ward_groups[wk].get(cat) is not None else '  N/A':<14}"
                for cat in AGE_CATEGORIES
            )
            print(row)
    print()

# ── Write output ──────────────────────────────────────────────────────────────
with open(OUTPUT_FILE, "w") as f:
    json.dump(result, f, indent=2)

print(f"  ✓ Results written --> '{OUTPUT_FILE.name}'")
print("="*62 + "\n")

