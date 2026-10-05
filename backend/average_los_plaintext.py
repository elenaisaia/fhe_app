import json
from datetime import datetime
from pathlib import Path

INPUT_FILE  = Path(__file__).parent / "patient_hospitalizations.json"
OUTPUT_FILE = Path(__file__).parent / "average-length-of-stay-plaintext-statistics.json"

AGE_CATEGORIES = ["under 18", "18 to 65", "over 65"]
MONTH_NAMES    = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr",
                  5:"May", 6:"Jun", 7:"Jul", 8:"Aug",
                  9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}

# ── Load ──────────────────────────────────────────────────────────────────────
print("\n" + "═"*62)
print("  Plaintext  —  Average Length-of-Stay Statistics")
print("═"*62)

with open(INPUT_FILE) as f:
    data = json.load(f)

print(f"\n  Loaded {len(data)} entries from '{INPUT_FILE.name}'")

# ── Group length-of-stay values by (year, month, age_category) ───────────────
# grouped[year][month][age_category] = [los_days, ...]
grouped: dict = {}
skipped = 0

for entry in data:
    discharge_str = entry.get("discharge_date")
    admission_str = entry.get("admission_date")
    age_cat = (entry.get("age_category") or "").strip()

    if not discharge_str or not admission_str:
        skipped += 1
        continue

    discharge = datetime.strptime(discharge_str, "%d.%m.%Y")
    admission = datetime.strptime(admission_str,  "%d.%m.%Y")
    los = max(1, (discharge - admission).days)

    year = discharge.year
    month = discharge.month

    grouped.setdefault(year, {})
    grouped[year].setdefault(month, {cat: [] for cat in AGE_CATEGORIES})

    if age_cat in grouped[year][month]:
        grouped[year][month][age_cat].append(los)

if skipped:
    print(f"  Skipped {skipped} entries with missing dates")

years_found = sorted(grouped)
print(f"  Years in data : {years_found}\n")

# ── Compute averages & build result dict ──────────────────────────────────────
result: dict = {}

for year in years_found:
    year_str = str(year)
    monthly_result: dict = {}
    yearly_totals = {cat: [0, 0] for cat in AGE_CATEGORIES}

    for month in sorted(grouped[year].keys()):
        month_name = MONTH_NAMES[month]
        monthly_result[month_name] = {}

        for age_cat in AGE_CATEGORIES:
            los_list = grouped[year][month].get(age_cat, [])
            if los_list:
                s   = sum(los_list)
                c   = len(los_list)
                avg = round(s / c, 2)
                yearly_totals[age_cat][0] += s
                yearly_totals[age_cat][1] += c
            else:
                avg = None
            monthly_result[month_name][age_cat] = avg

    general = {
        age_cat: (round(yearly_totals[age_cat][0] / yearly_totals[age_cat][1], 2)
                  if yearly_totals[age_cat][1] > 0 else None)
        for age_cat in AGE_CATEGORIES
    }

    result[year_str] = {"general": general, **monthly_result}

for year_str, year_data in result.items():
    gen = year_data["general"]
    print(f"  ── {year_str}  (full-year averages) ──")
    for cat, val in gen.items():
        print(f"    {cat:<12} : {val} days")
    print()

    header = f"  {'Month':<6}" + "".join(f"  {cat:<14}" for cat in AGE_CATEGORIES)
    print(f"  {year_str}  (monthly breakdown):")
    print(header)
    print("  " + "─" * (len(header) - 2))
    for month_name, age_avgs in year_data.items():
        if month_name == "general":
            continue
        row = f"  {month_name:<6}" + "".join(
            f"  {str(age_avgs.get(cat, '-')):<14}" for cat in AGE_CATEGORIES
        )
        print(row)
    print()

# ── Write output ──────────────────────────────────────────────────────────────
with open(OUTPUT_FILE, "w") as f:
    json.dump(result, f, indent=2)

print("═"*62 + "\n")

