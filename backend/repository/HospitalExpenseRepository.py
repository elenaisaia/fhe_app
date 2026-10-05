import json
from model.HospitalExpense import HospitalExpense

class HospitalExpenseRepository:
    def getAllEntries(self):
        hospitalExpenseList = []
        with open("./hospital_expenses_encrypted.json", "r") as file:
            entries = json.load(file)
            for entry in entries:
                hospitalExpense = HospitalExpense()
                encryptedFields = entry.get("encrypted_fields")
                hospitalExpense.setId(entry.get("uuid"))
                hospitalExpense.setDescription(encryptedFields.get("description"))
                hospitalExpense.setExpenseDate(entry.get("expense_date"))
                hospitalExpense.setExpenseType(encryptedFields.get("expense_type"))
                hospitalExpense.setAmount(encryptedFields.get("amount"))

                hospitalExpenseList.append(hospitalExpense)
        return hospitalExpenseList

    def addHospitalExpense(self, hospitalExpense: HospitalExpense):
        encrypted_entry = {
            "uuid": str(hospitalExpense.getId()),
            "expense_date": hospitalExpense.getExpenseDate(),
            "encrypted_fields": {
                "amount": hospitalExpense.getAmount(),
                "description": hospitalExpense.getDescription(),
                "expense_type": hospitalExpense.getExpenseType(),
            },
        }

        file_path = "./hospital_expenses_encrypted.json"
        with open(file_path, "r") as f:
            entries = json.load(f)

        entries.append(encrypted_entry)

        with open(file_path, "w") as f:
            json.dump(entries, f, indent=2)

        print(f"[Repository] addHospitalExpense — appended uuid={encrypted_entry['uuid']} "
              f"({len(entries)} total entries)")
