"""
encrypt_hospitalizations.py
────────────────────────────
Loads patient_hospitalizations.json, sorts by admission_date ASC,
encrypts all fields except admission_date and discharge_date using
Concrete FHE, assigns a UUID to each entry, and writes the result
to patient_hospitalizations_encrypted.json.

Circuits:
  num_circuit          — scalar integer (patient_id, died, all costs ×100)
  str_circuit[field]   — byte array, field-specific length (name, age_category,
                         diagnosis, ward), zero-padded

Plaintext fields kept:  admission_date, discharge_date, uuid
"""

import json
import uuid
import base64
import warnings
import numpy as np
import os
from datetime import datetime
from concrete import fhe

warnings.filterwarnings("ignore")

SCALE        = 100   # float costs → integer cents
INPUT_FILE   = "patient_hospitalizations.json"
OUTPUT_FILE  = "patient_hospitalizations_encrypted.json"
KEYS_DIR     = "fhe_keys"          # directory where all circuit keys are saved

COST_FIELDS  = ["cost_services", "cost_hospitalization", "cost_meds", "cost_meals"]
BOOL_FIELDS  = ["died"]
ID_FIELDS    = ["patient_id"]
NUM_FIELDS   = COST_FIELDS + BOOL_FIELDS + ID_FIELDS
STR_FIELDS   = ["name", "age_category", "diagnosis", "ward"]
PLAIN_FIELDS = ["admission_date", "discharge_date"]


# ══════════════════════════════════════════════════════════════
# 1. Load & Sort
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*60)
print("  STEP 1 — Loading and sorting patient data")
print("═"*60)

with open(INPUT_FILE) as f:
    data = json.load(f)

data.sort(key=lambda x: datetime.strptime(x["admission_date"], "%d.%m.%Y"))

print(f"  ✓ Loaded {len(data)} entries")
print(f"  ✓ Sorted by admission_date ASC")
print(f"  First entry date : {data[0]['admission_date']}")
print(f"  Last  entry date : {data[-1]['admission_date']}")


# ══════════════════════════════════════════════════════════════
# 2. Compile FHE Circuits
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*60)
print("  STEP 2 — Compiling FHE circuits")
print("═"*60)

rng = np.random.default_rng(seed=42)

# ── Numeric circuit: scalar identity ──────────────────────────
# Handles: patient_id (1–2300), died (0/1), costs (×100 cents)
max_num_val = int(max(d["cost_hospitalization"] for d in data) * SCALE) + 1
print(f"\n  [num_circuit] scalar identity, max value = {max_num_val:,}")

@fhe.compiler({"x": "encrypted"})
def fhe_num_identity(x):
    return x

num_inputset = list(rng.integers(0, max_num_val, 300, dtype=np.int64))
num_inputset += [np.int64(0), np.int64(max_num_val),
                 np.int64(max(d["patient_id"] for d in data))]

os.makedirs(KEYS_DIR, exist_ok=True)

# Save circuit compilation parameters so FHERunner can reconstruct circuits later
circuit_params = {
    "scale": SCALE,
    "max_num_val": max_num_val,
    "max_patient_id": int(max(d["patient_id"] for d in data)),
    "rng_seed": 42,
    "num_inputset_random_count": 300,
    "str_inputset_random_count": 300,
    "str_max_lens": str_max_len,
    "cost_fields": COST_FIELDS,
    "bool_fields": BOOL_FIELDS,
    "id_fields": ID_FIELDS,
    "num_fields": NUM_FIELDS,
    "str_fields": STR_FIELDS,
}
with open(os.path.join(KEYS_DIR, "circuit_params.json"), "w") as f:
    json.dump(circuit_params, f, indent=2)
print(f"  ✓ Circuit params saved → {KEYS_DIR}/circuit_params.json")

print("  [num_circuit] Compiling … (this may take a minute)")
num_circuit = fhe_num_identity.compile(num_inputset)
num_circuit.keygen()
num_key_path = os.path.join(KEYS_DIR, "num_circuit.keys")
num_circuit.client.keys.save(num_key_path)
print(f"  [num_circuit] ✓ Compiled, keys generated and saved → {num_key_path}")


# ── String circuits: field-specific byte-array identity ───────
def make_str_circuit(field: str, max_len: int, rng) -> fhe.Circuit:
    """Compile and key-generate a string identity circuit for arrays of max_len bytes.
       Keys are saved to KEYS_DIR/str_<field>.keys for later decryption."""
    @fhe.compiler({"bytes_arr": "encrypted"})
    def _circuit(bytes_arr):
        return bytes_arr + 0   # trivial identity

    inputset = list(rng.integers(0, 256, (300, max_len), dtype=np.int64))
    inputset += [np.zeros(max_len, dtype=np.int64),
                 np.full(max_len, 255, dtype=np.int64)]
    c = _circuit.compile(inputset)
    c.keygen()
    key_path = os.path.join(KEYS_DIR, f"str_{field}.keys")
    c.client.keys.save(key_path)
    return c

str_max_len  = {f: max(len(d[f].encode("utf-8")) for d in data) for f in STR_FIELDS}
str_circuits: dict[str, fhe.Circuit] = {}

print()
for field in STR_FIELDS:
    ml = str_max_len[field]
    print(f"  [str_circuit:{field}] max_len={ml} bytes — compiling …")
    str_circuits[field] = make_str_circuit(field, ml, rng)
    key_path = os.path.join(KEYS_DIR, f"str_{field}.keys")
    print(f"  [str_circuit:{field}] ✓ Compiled, keys saved → {key_path}")


# ══════════════════════════════════════════════════════════════
# 3. Helper utilities
# ══════════════════════════════════════════════════════════════

def encode_num(entry: dict, field: str) -> np.int64:
    if field in COST_FIELDS:
        return np.int64(int(round(entry[field] * SCALE)))
    return np.int64(int(entry[field]))   # patient_id and died (bool→int)

def str_to_bytes_arr(s: str, max_len: int) -> np.ndarray:
    byt = s.encode("utf-8")
    arr = np.zeros(max_len, dtype=np.int64)
    arr[:len(byt)] = list(byt)
    return arr

def to_b64(enc_val: fhe.Value) -> str:
    return base64.b64encode(enc_val.serialize()).decode("utf-8")


# ══════════════════════════════════════════════════════════════
# 4. Encrypt all entries
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*60)
print(f"  STEP 3 — Encrypting {len(data)} entries")
print("═"*60)
print("  (plaintext fields kept: admission_date, discharge_date, uuid)\n")

encrypted_entries = []
report_every = max(1, len(data) // 20)   # progress every 5 %

for i, entry in enumerate(data):
    if i == 0 or (i + 1) % report_every == 0 or i == len(data) - 1:
        pct = (i + 1) / len(data) * 100
        print(f"  [{i+1:>4}/{len(data)}]  {pct:5.1f}%  "
              f"({entry['admission_date']}  {entry.get('name','?')})")

    enc_fields: dict = {}

    # Numeric fields
    for field in NUM_FIELDS:
        val = encode_num(entry, field)
        enc  = num_circuit.encrypt(val)
        enc_fields[field] = {
            "ciphertext": to_b64(enc),
            "scale": SCALE if field in COST_FIELDS else 1,
        }

    # String fields
    for field in STR_FIELDS:
        ml  = str_max_len[field]
        arr = str_to_bytes_arr(entry[field], ml)
        enc = str_circuits[field].encrypt(arr)
        enc_fields[field] = {
            "ciphertext":       to_b64(enc),
            "original_length":  len(entry[field].encode("utf-8")),
            "max_len":          ml,
        }

    encrypted_entries.append({
        "uuid":           str(uuid.uuid4()),
        "admission_date": entry["admission_date"],
        "discharge_date": entry["discharge_date"],
        "encrypted_fields": enc_fields,
    })

print(f"\n  ✓ All {len(encrypted_entries)} entries encrypted")


# ══════════════════════════════════════════════════════════════
# 5. Write output
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*60)
print(f"  STEP 4 — Writing to '{OUTPUT_FILE}'")
print("═"*60)

with open(OUTPUT_FILE, "w") as f:
    json.dump(encrypted_entries, f, indent=2)

size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
print(f"\n  ✓ Written successfully")
print(f"  Entries  : {len(encrypted_entries)}")
print(f"  File size: {size_mb:.1f} MB")
print(f"\n  Structure of one entry:")
sample = encrypted_entries[0]
print(f"    uuid           : {sample['uuid']}")
print(f"    admission_date : {sample['admission_date']}  (plaintext)")
print(f"    discharge_date : {sample['discharge_date']}  (plaintext)")
for field, info in sample["encrypted_fields"].items():
    ct_len = len(info["ciphertext"])
    raw_kb = ct_len * 3 // 4 // 1024
    print(f"    {field:<24}: ciphertext ~{raw_kb} KB  "
          f"{'scale='+str(info.get('scale','')) if 'scale' in info else 'orig_len='+str(info.get('original_length',''))}")

print("\n" + "═"*60)
print("  ✓ Done! patient_hospitalizations_encrypted.json is ready.")
print("═"*60)

print("\n  ⚠️  KEY FILES (required for any future decryption):")
print(f"  Directory: ./{KEYS_DIR}/")
for fname in sorted(os.listdir(KEYS_DIR)):
    fpath = os.path.join(KEYS_DIR, fname)
    size_kb = os.path.getsize(fpath) / 1024
    print(f"    {fname:<30} {size_kb:>8.1f} KB")
print()
print("  🔒 Keep these key files SECRET and backed up.")
print("     Without them, the encrypted data CANNOT be decrypted.\n")

