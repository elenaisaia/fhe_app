from fastapi import FastAPI
import json
from pathlib import Path

from starlette.middleware.cors import CORSMiddleware

from model.User import User

from service.FHERunner import FHERunner
from repository.PatientHospitalizationRepository import PatientHospitalizationRepository
from service.PatientHospitalizationService import PatientHospitalizationService
from controller.PatientHospitalizationController import PatientHospitalizationController
from repository.HospitalExpenseRepository import HospitalExpenseRepository
from service.HospitalExpenseService import HospitalExpenseService
from controller.HospitalExpenseController import HospitalExpenseController
from repository.UserRepository import UserRepository
from service.UserService import UserService
from controller.UserController import UserController

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


fheRunner = FHERunner()

patientHospitalizationRepository = PatientHospitalizationRepository()
patientHospitalizationService = PatientHospitalizationService(patientHospitalizationRepository, fheRunner)
patientHospitalizationController = PatientHospitalizationController(patientHospitalizationService)
app.include_router(patientHospitalizationController.router)

hospitalExpenseRepository = HospitalExpenseRepository()
hospitalExpenseService = HospitalExpenseService(hospitalExpenseRepository, fheRunner)
hospitalExpenseController = HospitalExpenseController(hospitalExpenseService)
app.include_router(hospitalExpenseController.router)

userRepository = UserRepository()
userService = UserService(userRepository)
userController = UserController(userService)
app.include_router(userController.router)


ENCRYPTED_FILE = Path(__file__).parent / "patient_hospitalizations_encrypted.json"


def populateDatabase():
    with open("./patient_hospitalizations_encrypted.json", "r") as file:
        entries = json.load(file)

def createUsers():
    user = User()
    repository = UserRepository()
    service = UserService(repository)

    user.setUsername("admin")
    user.setPassword("admin")
    user.setUserType("management")
    service.register(user)

    user.setUsername("manager")
    user.setPassword("manager")
    user.setUserType("management")
    service.register(user)

    user.setUsername("doctor")
    user.setPassword("doctor")
    user.setUserType("medical")
    service.register(user)

    user.setUsername("nurse")
    user.setPassword("nurse")
    user.setUserType("medical")
    service.register(user)

    user.setUsername("accountant")
    user.setPassword("accountant")
    user.setUserType("accounting")
    service.register(user)

    user.setUsername("inventory")
    user.setPassword("inventory")
    user.setUserType("accounting")
    service.register(user)


def main():
    pass
    # patientHospitalizationRepository = PatientHospitalizationRepository()
    # patientHospitalizationService = PatientHospitalizationService(patientHospitalizationRepository)
    # patientHospitalizationController = PatientHospitalizationController(patientHospitalizationService)
    #
    # statistics = patientHospitalizationController.generateAverageLengthOfStayStatistics()
    #
    # for year in statistics:
    #     for month in statistics[year]:
    #         for entry in statistics[year][month]:
    #             print(entry.getDischargeDate())


    # print("=" * 60)
    # print("  FHE Decryption Demo — Patient Hospitalization")
    # print("=" * 60)
    #
    # # 1. Load encrypted dataset
    # print(f"\nLoading encrypted data from:\n  {ENCRYPTED_FILE}\n")
    # with open(ENCRYPTED_FILE) as f:
    #     encrypted_entries = json.load(f)
    # print(f"  ✓ {len(encrypted_entries)} encrypted entries loaded")
    # print(f"  Taking the first entry (uuid: {encrypted_entries[0]['uuid']})\n")
    #
    # # 2. Initialise FHERunner (compiles circuits + loads keys)
    # runner = FHERunner()
    #
    # # 3. Decrypt the first entry
    # first_entry = encrypted_entries[0]
    # print("Decrypting first entry …")
    # decrypted = runner.decrypt_entry(first_entry)
    #
    # # 4. Display result
    # print("\n" + "=" * 60)
    # print("  DECRYPTED PATIENT RECORD")
    # print("=" * 60)
    # field_order = [
    #     "uuid", "patient_id", "name", "age_category", "diagnosis",
    #     "ward", "admission_date", "discharge_date", "died",
    #     "cost_services", "cost_hospitalization", "cost_meds", "cost_meals",
    # ]
    # for field in field_order:
    #     value = decrypted.get(field, "—")
    #     if field.startswith("cost_"):
    #         print(f"  {field:<26}: ${value:>10.2f}")
    #     else:
    #         print(f"  {field:<26}: {value}")
    # print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
