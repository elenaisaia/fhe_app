import json
import os
import tempfile
from model.PatientHospitalization import PatientHospitalization

class PatientHospitalizationRepository:
    def getAllEntries(self):
        patientHospitalizationList = []
        with open("./patient_hospitalizations_encrypted.json", "r") as file:
            entries = json.load(file)
            for entry in entries:
                patientHospitalization = PatientHospitalization()
                encryptedFields = entry.get("encrypted_fields")
                patientHospitalization.setId(entry.get("uuid"))
                patientHospitalization.setPatientId(encryptedFields.get("patient_id"))
                patientHospitalization.setName(encryptedFields.get("name"))
                patientHospitalization.setAgeCategory(encryptedFields.get("age_category"))
                patientHospitalization.setDiagnosis(encryptedFields.get("diagnosis"))
                patientHospitalization.setWard(encryptedFields.get("ward"))
                patientHospitalization.setAdmissionDate(entry.get("admission_date"))
                patientHospitalization.setDischargeDate(entry.get("discharge_date"))
                patientHospitalization.setDied(encryptedFields.get("died"))
                patientHospitalization.setCostServices(encryptedFields.get("cost_services"))
                patientHospitalization.setCostHospitalization(encryptedFields.get("cost_hospitalization"))
                patientHospitalization.setCostMeds(encryptedFields.get("cost_meds"))
                patientHospitalization.setCostMeals(encryptedFields.get("cost_meals"))

                patientHospitalizationList.append(patientHospitalization)
        return patientHospitalizationList

    def addPatientHospitalization(self, patientHospitalization):
        enc_fields: dict = {}

        for json_key, getter in [
            ("patient_id", patientHospitalization.getPatientId),
            ("died", patientHospitalization.getDied),
            ("cost_services", patientHospitalization.getCostServices),
            ("cost_hospitalization", patientHospitalization.getCostHospitalization),
            ("cost_meds", patientHospitalization.getCostMeds),
            ("cost_meals", patientHospitalization.getCostMeals),
            ("name", patientHospitalization.getName),
            ("age_category", patientHospitalization.getAgeCategory),
            ("diagnosis", patientHospitalization.getDiagnosis),
            ("ward", patientHospitalization.getWard),
        ]:
            val = getter()
            if val is not None:
                enc_fields[json_key] = val

        new_entry: dict = {"uuid": str(patientHospitalization.getId())}

        admission = patientHospitalization.getAdmissionDate()
        discharge = patientHospitalization.getDischargeDate()
        if admission is not None:
            new_entry["admission_date"] = admission
        if discharge is not None:
            new_entry["discharge_date"] = discharge

        new_entry["encrypted_fields"] = enc_fields

        file_path = "./patient_hospitalizations_encrypted.json"
        new_entry_str = json.dumps(new_entry, indent=2)

        with open(file_path, "r+b") as f:
            f.seek(0, 2)
            file_size = f.tell()

            search_size = min(128, file_size)
            f.seek(file_size - search_size)
            tail = f.read(search_size)

            idx = tail.rfind(b"]")
            if idx == -1:
                raise ValueError("addPatientHospitalization: cannot find closing ] in JSON file")

            bracket_pos = (file_size - search_size) + idx

            f.seek(bracket_pos - min(bracket_pos, 20))
            before_bracket = f.read(min(bracket_pos, 20))
            needs_comma = before_bracket.strip() not in (b"", b"[")

            f.seek(bracket_pos)
            f.truncate()
            if needs_comma:
                f.write(b",\n")
            else:
                f.write(b"\n")
            f.write(new_entry_str.encode("utf-8"))
            f.write(b"\n]")

        print(f"[Repository] addPatientHospitalization — uuid={new_entry['uuid']}")

    def updatePatientHospitalization(self, patientHospitalization):
        target_uuid = str(patientHospitalization.getId())

        enc_fields: dict = {}
        for json_key, getter in [
            ("patient_id",            patientHospitalization.getPatientId),
            ("died",                  patientHospitalization.getDied),
            ("cost_services",         patientHospitalization.getCostServices),
            ("cost_hospitalization",  patientHospitalization.getCostHospitalization),
            ("cost_meds",             patientHospitalization.getCostMeds),
            ("cost_meals",            patientHospitalization.getCostMeals),
            ("name",                  patientHospitalization.getName),
            ("age_category",          patientHospitalization.getAgeCategory),
            ("diagnosis",             patientHospitalization.getDiagnosis),
            ("ward",                  patientHospitalization.getWard),
        ]:
            val = getter()
            if val is not None:
                enc_fields[json_key] = val

        new_entry: dict = {"uuid": target_uuid}
        admission = patientHospitalization.getAdmissionDate()
        discharge = patientHospitalization.getDischargeDate()
        if admission is not None:
            new_entry["admission_date"] = admission
        if discharge is not None:
            new_entry["discharge_date"] = discharge
        new_entry["encrypted_fields"] = enc_fields

        raw_json    = json.dumps(new_entry, indent=2)
        indented    = "\n".join("  " + line for line in raw_json.split("\n"))
        replacement = indented.encode("utf-8")

        file_path = "./patient_hospitalizations_encrypted.json"

        with open(file_path, "rb") as f:
            data = f.read()

        search_bytes = f'"uuid": "{target_uuid}"'.encode("utf-8")
        uuid_pos = data.find(search_bytes)
        if uuid_pos == -1:
            raise ValueError(
                f"[Repository] updatePatientHospitalization: "
                f"UUID '{target_uuid}' not found in file."
            )

        entry_nl_pos = data.rfind(b"\n  {", 0, uuid_pos)
        if entry_nl_pos == -1:
            raise ValueError(
                f"[Repository] updatePatientHospitalization: "
                f"cannot find entry start for UUID '{target_uuid}'."
            )
        entry_start = entry_nl_pos + 1   # skip the leading '\n'

        depth     = 0
        in_string = False
        escaped   = False
        entry_end = -1

        for i in range(entry_start, len(data)):
            ch = data[i]
            if escaped:
                escaped = False
                continue
            if in_string:
                if ch == ord("\\"):
                    escaped = True
                elif ch == ord('"'):
                    in_string = False
            else:
                if ch == ord('"'):
                    in_string = True
                elif ch == ord("{"):
                    depth += 1
                elif ch == ord("}"):
                    depth -= 1
                    if depth == 0:
                        entry_end = i + 1
                        break

        if entry_end == -1:
            raise ValueError(
                f"[Repository] updatePatientHospitalization: "
                f"cannot find closing brace for UUID '{target_uuid}'."
            )

        new_data = data[:entry_start] + replacement + data[entry_end:]

        dir_name = os.path.dirname(os.path.abspath(file_path))
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=dir_name, delete=False, suffix=".tmp"
        ) as tmp:
            tmp.write(new_data)
            tmp_path = tmp.name

        os.replace(tmp_path, file_path)

        print(f"[Repository] updatePatientHospitalization — uuid={target_uuid}")
