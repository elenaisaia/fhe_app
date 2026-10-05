"""
hospital_expenses_plaintext.py
────────────────────────────────
Computes average hospital expense statistics over the PLAINTEXT data
from hospital_expenses.json, grouped by year, month, and expense_type.

Output structure (mirrors the FHE version in FHERunner):
  {
    "2023": {
      "general": {
        "equipment": avg, "medicine": avg, "personnel": avg,
        "renovations": avg, "supplies": avg
      },
      "Jan": { "equipment": avg, ... },
      ...
    },
    ...
  }

Results are written to hospital-expenses-plaintext-statistics.json.
"""

import json
from datetime import datetime
from pathlib import Path

INPUT_FILE  = Path(__file__).parent / "hospital_expenses.json"
OUTPUT_FILE = Path(__file__).parent / "hospital-expenses-plaintext-statistics.json"

EXPENSE_TYPES = ["Equipment", "Medicine", "Personnel", "Renovations", "Supplies"]
TYPE_KEYS     = {t: t.lower() for t in EXPENSE_TYPES}
ALL_TYPE_KEYS = list(TYPE_KEYS.values())

MONTH_NAMES = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr",
               5:"May", 6:"Jun", 7:"Jul", 8:"Aug",
               9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}

# ── Load ──────────────────────────────────────────────────────────────────────
print("\n" + "="*64)
print("  Plaintext  --  Hospital Expenses Statistics")
print("="*64)

with open(INPUT_FILE) as f:
    data = json.load(f)

print(f"\n  Loaded {len(data)} entries from '{INPUT_FILE.name}'")

# ── Group amounts by (expense_year, expense_month, expense_type) ──────────────
# grouped[year][month][type_key] = [amount_values, ...]
grouped: dict = {}
skipped = 0

for entry in data:
    date_str     = entry.get("expense_date")
    expense_type = (entry.get("expense_type") or "").strip()
    amount       = entry.get("amount")

    if not date_str or amount is None:
        skipped += 1
        continue

    date     = datetime.strptime(date_str, "%d.%m.%Y")
    year     = date.year
    month    = date.month
    type_key = TYPE_KEYS.get(expense_type, expense_type.lower())

    grouped.setdefault(year, {})
    grouped[year].setdefault(month, {tk: [] for tk in ALL_TYPE_KEYS})

    if type_key in grouped[year][month]:
        grouped[year][month][type_key].append(float(amount))

if skipped:
    print(f"  Warning: skipped {skipped} entries with missing data")

years_found = sorted(grouped)
print(f"  Years in data : {years_found}\n")

# ── Compute averages & build result dict ──────────────────────────────────────
result: dict = {}

for year in years_found:
    year_str      = str(year)
    monthly_result: dict = {}
    yearly_totals = {tk: [0.0, 0] for tk in ALL_TYPE_KEYS}  # [sum, count]

    for month in sorted(grouped[year].keys()):
        month_name  = MONTH_NAMES[month]
        monthly_result[month_name] = {}

        for tk in ALL_TYPE_KEYS:
            vals = grouped[year][month].get(tk, [])
            if vals:
                s   = sum(vals)
                c   = len(vals)
                avg = round(s / c, 2)
                yearly_totals[tk][0] += s
                yearly_totals[tk][1] += c
            else:
                avg = None
            monthly_result[month_name][tk] = avg

    general = {
        tk: (round(yearly_totals[tk][0] / yearly_totals[tk][1], 2)
             if yearly_totals[tk][1] > 0 else None)
        for tk in ALL_TYPE_KEYS
    }

    result[year_str] = {"general": general, **monthly_result}

# ── Print summary ─────────────────────────────────────────────────────────────
for year_str, year_data in result.items():
    gen = year_data["general"]
    print(f"  -- {year_str}  (full-year averages per expense) --")
    for tk, val in gen.items():
        print(f"    {tk:<14} : ${val}")
    print()

    col_w  = 16
    header = f"  {'Month':<6}" + "".join(f"  {tk:<{col_w}}" for tk in ALL_TYPE_KEYS)
    print(f"  {year_str}  (monthly breakdown):")
    print(header)
    print("  " + "-" * (len(header) - 2))
    for month_name, type_avgs in year_data.items():
        if month_name == "general":
            continue
        row = f"  {month_name:<6}" + "".join(
            f"  {('$'+str(type_avgs.get(tk, '-'))):<{col_w}}" for tk in ALL_TYPE_KEYS
        )
        print(row)
    print()

# ── Write output ──────────────────────────────────────────────────────────────
with open(OUTPUT_FILE, "w") as f:
    json.dump(result, f, indent=2)

print(f"  ✓ Results written --> '{OUTPUT_FILE.name}'")
print("="*64 + "\n")

