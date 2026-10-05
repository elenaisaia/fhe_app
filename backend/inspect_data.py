import json
with open('patient_hospitalizations.json') as f:
    data = json.load(f)

for field in ['age_category', 'ward']:
    vals = sorted(set(d[field] for d in data))
    print(f'{field}: {vals}')

diag_vals = sorted(set(d['diagnosis'] for d in data))
print(f'diagnosis ({len(diag_vals)} distinct), max_len={max(len(v) for v in diag_vals)}, longest: "{max(diag_vals, key=len)}"')

for field in ['cost_services','cost_hospitalization','cost_meds','cost_meals']:
    vals = [d[field] for d in data]
    print(f'{field}: min={min(vals):.2f}  max={max(vals):.2f}')

print(f'patient_id: min={min(d["patient_id"] for d in data)}  max={max(d["patient_id"] for d in data)}')
print(f'name max_len={max(len(d["name"]) for d in data)}  example: "{max((d["name"] for d in data), key=len)}"')
print(f'died distinct: {set(d["died"] for d in data)}')

