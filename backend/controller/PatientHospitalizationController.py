from fastapi import APIRouter, HTTPException
from model.PatientHospitalization import PatientHospitalization
from service.PatientHospitalizationService import PatientHospitalizationService
from schemas.PatientHospitalizationSchema import PatientHospitalizationCreate, PatientHospitalizationResponse


class PatientHospitalizationController:
    def __init__(self, patientHospitalizationService: PatientHospitalizationService):
        self.router = APIRouter(
            prefix="/hospitalizations",
            tags=["Hospitalizations"]
        )
        self.patientHospitalizationService = patientHospitalizationService
        self.patientHospitalizationService.generatePatientHospitalizationMap()

        self.router.add_api_route(
            "/add",
            self.addPatientHospitalization,
            methods=["POST"]
        )

        self.router.add_api_route(
            "/update",
            self.updatePatientHospitalization,
            methods=["POST"]
        )

        self.router.add_api_route(
            "/generate-average-length-of-stay",
            self.generateAverageLengthOfStayStatistics,
                methods=["GET"]
        )

        self.router.add_api_route(
            "/generate-costs-per-patient",
            self.generateCostsPerPatientStatistics,
            methods=["GET"]
        )

        self.router.add_api_route(
            "/generate-mortality-rate",
            self.generateMoralityRateStatistics,
            methods=["GET"]
        )

    def addPatientHospitalization(self, request: PatientHospitalizationCreate):
        try:
            patientHospitalization = PatientHospitalization()
            patientHospitalization.createPatientHospitalization(request)
            message = self.patientHospitalizationService.addPatientHospitalization(patientHospitalization)
            return PatientHospitalizationResponse(message=message)
        except ValueError as error:
            raise HTTPException(status_code=401, detail=str(error))

    def updatePatientHospitalization(self, request: PatientHospitalizationCreate):
        try:
            patientHospitalization = PatientHospitalization()
            patientHospitalization.createPatientHospitalization(request)
            message = self.patientHospitalizationService.updatePatientHospitalization(patientHospitalization)
            return PatientHospitalizationResponse(message=message)
        except ValueError as error:
            raise HTTPException(status_code=401, detail=str(error))

    def generateAverageLengthOfStayStatistics(self):
        return self.patientHospitalizationService.generateAverageLengthOfStayStatistics()

    def generateCostsPerPatientStatistics(self):
        return self.patientHospitalizationService.generateCostsPerPatientStatistics()

    def generateMoralityRateStatistics(self):
        return self.patientHospitalizationService.generateMoralityRateStatistics()
