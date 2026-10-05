import uuid
from model.PatientHospitalization import PatientHospitalization
from repository.PatientHospitalizationRepository import PatientHospitalizationRepository
from service.FHERunner import FHERunner
from datetime import datetime


class PatientHospitalizationService:
    def __init__(self, patientHospitalizationRepository: PatientHospitalizationRepository, fheRunner: FHERunner):
        self.patientHospitalizationRepository = patientHospitalizationRepository
        self.fheRunner = fheRunner
        self.patientHospitalizationMap = {}
        self.openPatientHospitalizationList = []

    def generatePatientHospitalizationMap(self):
        patientHospitalizationList = self.patientHospitalizationRepository.getAllEntries()
        dict.clear(self.patientHospitalizationMap)
        for patientHospitalization in patientHospitalizationList:
            if patientHospitalization.getDischargeDate() is not None:
                dischargeDate = datetime.strptime(patientHospitalization.getDischargeDate(), '%d.%m.%Y').date()
                dischargeYear = self.getYearOfDate(dischargeDate)
                dischargeMonth = self.getMonthOfDate(dischargeDate)
                if dischargeYear not in self.patientHospitalizationMap:
                    self.patientHospitalizationMap[dischargeYear] = {}
                if dischargeMonth not in self.patientHospitalizationMap[dischargeYear]:
                    self.patientHospitalizationMap[dischargeYear][dischargeMonth] = []
                self.patientHospitalizationMap[dischargeYear][dischargeMonth].append(patientHospitalization)
            else:
                self.openPatientHospitalizationList.append(patientHospitalization)

    def addPatientHospitalization(self, patientHospitalization: PatientHospitalization):
        for openPatientHospitalization in self.openPatientHospitalizationList:
            # if openPatientHospitalization.getPatientId() == patientHospitalization.getPatientId():
            if self.fheRunner.checkIfSamePatient(openPatientHospitalization, patientHospitalization):
                print("An open file already exists for this patient.\nThe patient has already been admitted.\n")
                raise ValueError("An open file already exists for this patient. The patient has already been admitted.")

        patientHospitalization.setId(uuid.uuid4())
        patientHospitalizationEncrypted = self.fheRunner.encryptPatientHospitalization(patientHospitalization)
        self.openPatientHospitalizationList.append(patientHospitalizationEncrypted)
        print(patientHospitalization)
        print(self.openPatientHospitalizationList)
        self.patientHospitalizationRepository.addPatientHospitalization(patientHospitalizationEncrypted)
        print("Successfully added new patient file.\nPatient has been admitted.\n")
        return "Successfully added new patient file. Patient has been admitted."

    def updatePatientHospitalization(self, patientHospitalization: PatientHospitalization):
        for index in range(self.openPatientHospitalizationList.__len__()):
            openPatientHospitalization = self.openPatientHospitalizationList[index]
            # if openPatientHospitalization.getPatientId() == patientHospitalization.getPatientId():
            if self.fheRunner.checkIfSamePatient(openPatientHospitalization, patientHospitalization):
                patientHospitalization.setId(openPatientHospitalization.getId())

                mergedEncrypted = self.fheRunner.mergeAndEncryptPatientHospitalization(openPatientHospitalization, patientHospitalization)

                if patientHospitalization.getDischargeDate() is None:
                    self.openPatientHospitalizationList[index] = mergedEncrypted
                else:
                    dischargeDate = datetime.strptime(mergedEncrypted.getDischargeDate(), '%d.%m.%Y').date()
                    dischargeYear  = self.getYearOfDate(dischargeDate)
                    dischargeMonth = self.getMonthOfDate(dischargeDate)
                    if dischargeYear not in self.patientHospitalizationMap:
                        self.patientHospitalizationMap[dischargeYear] = {}
                    if dischargeMonth not in self.patientHospitalizationMap[dischargeYear]:
                        self.patientHospitalizationMap[dischargeYear][dischargeMonth] = []
                    self.patientHospitalizationMap[dischargeYear][dischargeMonth].append(mergedEncrypted)
                    self.openPatientHospitalizationList.remove(openPatientHospitalization)

                self.patientHospitalizationRepository.updatePatientHospitalization(mergedEncrypted)
                print("Successfully updated patient file.\n")
                return "Successfully updated patient file."

        print("Patient doesn't have an open file.\nPlease admit the patient first.\n")
        raise ValueError("Patient doesn't have an open file. Please admit the patient first.")


    def generateAverageLengthOfStayStatistics(self):
        return self.fheRunner.generateAverageLengthOfStayStatistics(self.patientHospitalizationMap)

    def generateCostsPerPatientStatistics(self):
        return self.fheRunner.generateCostsPerPatientStatistics(self.patientHospitalizationMap)

    def generateMoralityRateStatistics(self):
        return self.fheRunner.generateMoralityRateStatistics(self.patientHospitalizationMap)

    def getYearOfDate(self, date: datetime.date):
        return date.year

    def getMonthOfDate(self, date: datetime.date):
        return date.month

    def getMap(self):
        return self.patientHospitalizationMap