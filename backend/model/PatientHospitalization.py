from schemas.PatientHospitalizationSchema import PatientHospitalizationCreate


class PatientHospitalization:
    def __init__(self):
        self.__id = None
        self.__patientId = None
        self.__name = None
        self.__ageCategory = None
        self.__diagnosis = None
        self.__ward = None
        self.__admissionDate = None
        self.__dischargeDate = None
        self.__died = None
        self.__costServices = None
        self.__costHospitalization = None
        self.__costMeds = None
        self.__costMeals = None

    def setId(self, id):
        self.__id = id

    def setPatientId(self, patient_id):
        self.__patientId = patient_id

    def setName(self, name):
        self.__name = name

    def setAgeCategory(self, age_category):
        self.__ageCategory = age_category

    def setDiagnosis(self, diagnosis):
        self.__diagnosis = diagnosis

    def setWard(self, ward):
        self.__ward = ward

    def setAdmissionDate(self, admission_date):
        self.__admissionDate = admission_date

    def setDischargeDate(self, discharge_date):
        self.__dischargeDate = discharge_date

    def setDied(self, died):
        self.__died = died

    def setCostServices(self, cost_services):
        self.__costServices = cost_services

    def setCostHospitalization(self, cost_hospitalization):
        self.__costHospitalization = cost_hospitalization

    def setCostMeds(self, cost_meds):
        self.__costMeds = cost_meds

    def setCostMeals(self, cost_meals):
        self.__costMeals = cost_meals

    def getId(self):
        return self.__id

    def getPatientId(self):
        return self.__patientId

    def getName(self):
        return self.__name

    def getAgeCategory(self):
        return self.__ageCategory

    def getDiagnosis(self):
        return self.__diagnosis

    def getWard(self):
        return self.__ward

    def getAdmissionDate(self):
        return self.__admissionDate

    def getDischargeDate(self):
        return self.__dischargeDate

    def getDied(self):
        return self.__died

    def getCostServices(self):
        return self.__costServices

    def getCostHospitalization(self):
        return self.__costHospitalization

    def getCostMeds(self):
        return self.__costMeds

    def getCostMeals(self):
        return self.__costMeals

    def createPatientHospitalization(self, request: PatientHospitalizationCreate):
        self.__patientId = request.patientId
        self.__name = request.name
        self.__ageCategory = request.ageCategory
        self.__diagnosis = request.diagnosis
        self.__ward = request.ward
        self.__admissionDate = request.admissionDate
        self.__dischargeDate = request.dischargeDate
        self.__died = request.died
        self.__costServices = request.costServices
        self.__costHospitalization = request.costHospitalization
        self.__costMeds = request.costMeds
        self.__costMeals = request.costMeals


    def __str__(self):
        return (f"PatientHospitalization(id={self.__id}, "
                f"patientId={self.__patientId}, "
                f"name={self.__name}, "
                f"ageCategory={self.__ageCategory}, "
                f"diagnosis={self.__diagnosis}, "
                f"ward={self.__ward}, "
                f"admissionDate={self.__admissionDate}, "
                f"dischargeDate={self.__dischargeDate}, "
                f"died={self.__died}, "
                f"costServices={self.__costServices}, "
                f"costHospitalization={self.__costHospitalization}, "
                f"costMeds={self.__costMeds}, "
                f"costMeals={self.__costMeals})")
