"""
costs_per_patient_plaintext.py
───────────────────────────────
Computes average costs per patient statistics over the PLAINTEXT data
from patient_hospitalizations.json.

Output structure (mirrors the FHE version in FHERunner):
  {
    "2023": {
      "general": {
        "services": avg, "hospitalization": avg, "meds": avg, "meals": avg
      },
      "Jan": {"services": avg, "hospitalization": avg, "meds": avg, "meals": avg},
      ...
    },
    ...
  }

Results are written to costs-per-patient-plaintext-statistics.json.
"""

import json
from datetime import datetime
from pathlib import Path

INPUT_FILE  = Path(__file__).parent / "patient_hospitalizations.json"
OUTPUT_FILE = Path(__file__).parent / "costs-per-patient-plaintext-statistics.json"

COST_FIELD_LABELS = {
    "cost_services":        "services",
    "cost_hospitalization": "hospitalization",
    "cost_meds":            "meds",
    "cost_meals":           "meals",
}
ALL_LABELS = list(COST_FIELD_LABELS.values())

MONTH_NAMES = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr",
               5:"May", 6:"Jun", 7:"Jul", 8:"Aug",
               9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}

# ── Load ──────────────────────────────────────────────────────────────────────
print("\n" + "="*62)
print("  Plaintext  --  Costs per Patient Statistics")
print("="*62)

with open(INPUT_FILE) as f:
    data = json.load(f)

print(f"\n  Loaded {len(data)} entries from '{INPUT_FILE.name}'")

# ── Group cost values by (discharge_year, discharge_month, cost_label) ────────
# grouped[year][month][cost_label] = [cost_values, ...]
grouped: dict = {}
skipped = 0

for entry in data:
    discharge_str = entry.get("discharge_date")
    if not discharge_str:
        skipped += 1
        continue

    discharge = datetime.strptime(discharge_str, "%d.%m.%Y")
    year      = discharge.year
    month     = discharge.month

    grouped.setdefault(year, {})
    grouped[year].setdefault(month, {lbl: [] for lbl in ALL_LABELS})

    for field, label in COST_FIELD_LABELS.items():
        val = entry.get(field)
        if val is not None:
            grouped[year][month][label].append(float(val))

if skipped:
    print(f"  Warning: skipped {skipped} entries with missing discharge_date")

years_found = sorted(grouped)
print(f"  Years in data : {years_found}\n")

# ── Compute averages & build result dict ──────────────────────────────────────
result: dict = {}

for year in years_found:
    year_str      = str(year)
    monthly_result: dict = {}
    yearly_totals = {lbl: [0.0, 0] for lbl in ALL_LABELS}  # [sum, count]

    for month in sorted(grouped[year].keys()):
        month_name = MONTH_NAMES[month]
        monthly_result[month_name] = {}

        for lbl in ALL_LABELS:
            vals = grouped[year][month].get(lbl, [])
            if vals:
                s   = sum(vals)
                c   = len(vals)
                avg = round(s / c, 2)
                yearly_totals[lbl][0] += s
                yearly_totals[lbl][1] += c
            else:
                avg = None
            monthly_result[month_name][lbl] = avg

    # Yearly "general" averages
    general = {
        lbl: (round(yearly_totals[lbl][0] / yearly_totals[lbl][1], 2)
              if yearly_totals[lbl][1] > 0 else None)
        for lbl in ALL_LABELS
    }

    # "general" first, then months in calendar order
    result[year_str] = {"general": general, **monthly_result}

# ── Print summary ─────────────────────────────────────────────────────────────
for year_str, year_data in result.items():
    gen = year_data["general"]
    print(f"  -- {year_str}  (full-year averages per patient) --")
    for lbl, val in gen.items():
        print(f"    {lbl:<18} : ${val}")
    print()

    col_w  = 14
    header = f"  {'Month':<6}" + "".join(f"  {lbl:<{col_w}}" for lbl in ALL_LABELS)
    print(f"  {year_str}  (monthly breakdown):")
    print(header)
    print("  " + "-" * (len(header) - 2))
    for month_name, cost_avgs in year_data.items():
        if month_name == "general":
            continue
        row = f"  {month_name:<6}" + "".join(
            f"  {('$'+str(cost_avgs.get(lbl, '-'))):<{col_w}}" for lbl in ALL_LABELS
        )
        print(row)
    print()

# ── Write output ──────────────────────────────────────────────────────────────
with open(OUTPUT_FILE, "w") as f:
    json.dump(result, f, indent=2)

print(f"  ✓ Results written --> '{OUTPUT_FILE.name}'")
print("="*62 + "\n")

