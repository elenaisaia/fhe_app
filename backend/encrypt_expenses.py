"""
encrypt_expenses.py
────────────────────
Loads hospital_expenses.json, sorts by expense_date ASC, encrypts all
fields except expense_date using Concrete FHE, assigns a UUID to each
entry, and writes the result to hospital_expenses_encrypted.json.

Circuits
--------
  num_circuit          — scalar integer for amount (×100 cents)
  str_circuit[field]   — byte-array identity per string field
                         (description, expense_type), zero-padded

Plaintext field kept  : expense_date, uuid
Keys saved to         : fhe_keys_expenses/
"""

import json, uuid, base64, warnings, os
import numpy as np
from datetime import datetime
from pathlib import Path
from concrete import fhe

warnings.filterwarnings("ignore")

SCALE        = 100                          # float amounts → integer cents
INPUT_FILE   = "hospital_expenses.json"
OUTPUT_FILE  = "hospital_expenses_encrypted.json"
KEYS_DIR     = Path("fhe_keys_expenses")
KEYS_DIR.mkdir(exist_ok=True)

NUM_FIELDS   = ["amount"]
STR_FIELDS   = ["description", "expense_type"]
PLAIN_FIELDS = ["expense_date"]

RNG_SEED     = 42

# ══════════════════════════════════════════════════════════════
# 1. Load & Sort
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*62)
print("  STEP 1 — Loading and sorting hospital expense data")
print("═"*62)

with open(INPUT_FILE) as f:
    data = json.load(f)

data.sort(key=lambda x: datetime.strptime(x["expense_date"], "%d.%m.%Y"))

print(f"  ✓ Loaded  : {len(data)} entries")
print(f"  ✓ Sorted  : by expense_date ASC")
print(f"  First date: {data[0]['expense_date']}")
print(f"  Last  date: {data[-1]['expense_date']}")

# ══════════════════════════════════════════════════════════════
# 2. Compile FHE Circuits
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*62)
print("  STEP 2 — Compiling FHE circuits")
print("═"*62)

rng = np.random.default_rng(seed=RNG_SEED)

# ── Numeric circuit: scalar identity for amount (cents) ───────
max_amount_cents = int(max(d["amount"] for d in data) * SCALE) + 1
print(f"\n  [num_circuit] scalar identity, max value = {max_amount_cents:,} cents "
      f"(${max_amount_cents/SCALE:,.2f})")

@fhe.compiler({"x": "encrypted"})
def fhe_num_identity(x):
    return x

num_inputset  = list(rng.integers(0, max_amount_cents, 300, dtype=np.int64))
num_inputset += [np.int64(0), np.int64(max_amount_cents)]

print("  [num_circuit] Compiling …")
num_circuit = fhe_num_identity.compile(num_inputset)
num_circuit.keygen()
num_circuit.client.keys.save(str(KEYS_DIR / "num_circuit.keys"))
print("  [num_circuit] ✓ Compiled, keys generated & saved")

# ── String circuits: byte-array identity per field ────────────
str_max_lens: dict[str, int] = {
    f: max(len(d[f].encode("utf-8")) for d in data)
    for f in STR_FIELDS
}
str_circuits: dict[str, fhe.Circuit] = {}

def make_str_circuit(max_len: int, rng) -> fhe.Circuit:
    @fhe.compiler({"bytes_arr": "encrypted"})
    def _circuit(bytes_arr):
        return bytes_arr + 0
    inputset  = list(rng.integers(0, 256, (300, max_len), dtype=np.int64))
    inputset += [np.zeros(max_len, dtype=np.int64),
                 np.full(max_len, 255, dtype=np.int64)]
    c = _circuit.compile(inputset)
    c.keygen()
    return c

print()
for field in STR_FIELDS:
    ml = str_max_lens[field]
    print(f"  [str_circuit:{field}] max_len={ml} bytes — compiling …")
    c = make_str_circuit(ml, rng)
    c.client.keys.save(str(KEYS_DIR / f"str_{field}.keys"))
    str_circuits[field] = c
    print(f"  [str_circuit:{field}] ✓ Compiled, keys generated & saved")

# ══════════════════════════════════════════════════════════════
# 3. Persist circuit parameters (needed for decryption later)
# ══════════════════════════════════════════════════════════════
params = {
    "scale":                       SCALE,
    "max_amount_cents":            max_amount_cents,
    "rng_seed":                    RNG_SEED,
    "num_inputset_random_count":   300,
    "str_inputset_random_count":   300,
    "str_max_lens":                str_max_lens,
    "num_fields":                  NUM_FIELDS,
    "str_fields":                  STR_FIELDS,
    "plain_fields":                PLAIN_FIELDS,
}
with open(KEYS_DIR / "circuit_params.json", "w") as f:
    json.dump(params, f, indent=2)
print(f"\n  ✓ circuit_params.json saved to {KEYS_DIR}/")

# ══════════════════════════════════════════════════════════════
# Helper utilities
# ══════════════════════════════════════════════════════════════
def to_b64(enc_val: fhe.Value) -> str:
    return base64.b64encode(enc_val.serialize()).decode("utf-8")

def str_to_bytes_arr(s: str, max_len: int) -> np.ndarray:
    byt = s.encode("utf-8")
    arr = np.zeros(max_len, dtype=np.int64)
    arr[:len(byt)] = list(byt)
    return arr

# ══════════════════════════════════════════════════════════════
# 4. Encrypt all entries
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*62)
print(f"  STEP 3 — Encrypting {len(data)} entries")
print("═"*62)
print("  (plaintext fields kept: expense_date, uuid)\n")

encrypted_entries = []
report_every = max(1, len(data) // 20)   # progress every 5%

for i, entry in enumerate(data):
    if i == 0 or (i + 1) % report_every == 0 or i == len(data) - 1:
        pct = (i + 1) / len(data) * 100
        print(f"  [{i+1:>4}/{len(data)}]  {pct:5.1f}%  "
              f"({entry['expense_date']}  {entry.get('expense_type','?')})")

    enc_fields: dict = {}

    # Numeric fields (amount → cents)
    for field in NUM_FIELDS:
        val = np.int64(int(round(entry[field] * SCALE)))
        enc = num_circuit.encrypt(val)
        enc_fields[field] = {
            "ciphertext": to_b64(enc),
            "scale":      SCALE,
        }

    # String fields
    for field in STR_FIELDS:
        ml  = str_max_lens[field]
        arr = str_to_bytes_arr(entry[field], ml)
        enc = str_circuits[field].encrypt(arr)
        enc_fields[field] = {
            "ciphertext":      to_b64(enc),
            "original_length": len(entry[field].encode("utf-8")),
            "max_len":         ml,
        }

    encrypted_entries.append({
        "uuid":         str(uuid.uuid4()),
        "expense_date": entry["expense_date"],
        "encrypted_fields": enc_fields,
    })

print(f"\n  ✓ All {len(encrypted_entries)} entries encrypted")

# ══════════════════════════════════════════════════════════════
# 5. Write output
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*62)
print(f"  STEP 4 — Writing '{OUTPUT_FILE}'")
print("═"*62)

with open(OUTPUT_FILE, "w") as f:
    json.dump(encrypted_entries, f, indent=2)

size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
sample  = encrypted_entries[0]

print(f"\n  ✓ Written successfully")
print(f"  Entries   : {len(encrypted_entries)}")
print(f"  File size : {size_mb:.1f} MB")
print(f"\n  Structure of one entry:")
print(f"    uuid          : {sample['uuid']}")
print(f"    expense_date  : {sample['expense_date']}  (plaintext)")
for field, info in sample["encrypted_fields"].items():
    ct_len  = len(info["ciphertext"])
    raw_kb  = ct_len * 3 // 4 // 1024
    detail  = (f"scale={info['scale']}" if "scale" in info
               else f"orig_len={info['original_length']}")
    print(f"    {field:<16}: ciphertext ~{raw_kb} KB  ({detail})")

print("\n" + "═"*62)
print("  ✓ Done!  hospital_expenses_encrypted.json is ready.")
print(f"  Keys saved in: {KEYS_DIR}/")
print("═"*62 + "\n")

