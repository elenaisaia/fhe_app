from fastapi import APIRouter
from model.HospitalExpense import HospitalExpense
from service.HospitalExpenseService import HospitalExpenseService
from schemas.HospitalExpenseSchema import HospitalExpenseCreate, HospitalExpenseResponse

class HospitalExpenseController:
    def __init__(self, hospitalExpenseService: HospitalExpenseService):
        self.router = APIRouter(
            prefix="/expenses",
            tags=["Expenses"]
        )
        self.hospitalExpenseService = hospitalExpenseService
        self.hospitalExpenseService.generateHospitalExpenseMap()

        self.router.add_api_route(
            "/add",
            self.addHospitalExpense,
            methods=["POST"]
        )

        self.router.add_api_route(
            "/generate-hospital-expenses",
            self.generateHospitalExpensesStatistics,
            methods=["GET"]
        )

    def addHospitalExpense(self, request: HospitalExpenseCreate):
        hospitalExpense = HospitalExpense()
        hospitalExpense.createHospitalExpense(request)
        self.hospitalExpenseService.addHospitalExpense(hospitalExpense)

    def generateHospitalExpensesStatistics(self):
        return self.hospitalExpenseService.generateHospitalExpensesStatistics()