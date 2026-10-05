import uuid
from model.HospitalExpense import HospitalExpense
from repository.HospitalExpenseRepository import HospitalExpenseRepository
from service.FHERunner import FHERunner
from datetime import datetime

class HospitalExpenseService:
    def __init__(self, hospitalExpenseRepository: HospitalExpenseRepository, fheRunner: FHERunner):
        self.hospitalExpenseRepository = hospitalExpenseRepository
        self.fheRunner = fheRunner
        self.hospitalExpenseMap = {}

    def generateHospitalExpenseMap(self):
        hospitalExpenseList = self.hospitalExpenseRepository.getAllEntries()
        dict.clear(self.hospitalExpenseMap)
        for hospitalExpense in hospitalExpenseList:
            expenseDate = datetime.strptime(hospitalExpense.getExpenseDate(), '%d.%m.%Y').date()
            expenseYear = self.getYearOfDate(expenseDate)
            expenseMonth = self.getMonthOfDate(expenseDate)
            if expenseYear not in self.hospitalExpenseMap:
                self.hospitalExpenseMap[expenseYear] = {}
            if expenseMonth not in self.hospitalExpenseMap[expenseYear]:
                self.hospitalExpenseMap[expenseYear][expenseMonth] = []
            self.hospitalExpenseMap[expenseYear][expenseMonth].append(hospitalExpense)

    def addHospitalExpense(self, hospitalExpense: HospitalExpense):
        hospitalExpense.setId(uuid.uuid4())

        expenseDate = hospitalExpense.getExpenseDate()
        expenseYear = self.getYearOfDate(expenseDate)
        expenseMonth = self.getMonthOfDate(expenseDate)
        if expenseYear not in self.hospitalExpenseMap:
            self.hospitalExpenseMap[expenseYear] = {}
        if expenseMonth not in self.hospitalExpenseMap[expenseYear]:
            self.hospitalExpenseMap[expenseYear][expenseMonth] = []

        hospitalExpenseEncrypted = self.fheRunner.encryptHospitalExpense(hospitalExpense)
        self.hospitalExpenseMap[expenseYear][expenseMonth].append(hospitalExpenseEncrypted)
        print(hospitalExpense)
        self.hospitalExpenseRepository.addHospitalExpense(hospitalExpenseEncrypted)

    def generateHospitalExpensesStatistics(self):
        return self.fheRunner.generateHospitalExpensesStatistics(self.hospitalExpenseMap)

    def getHospitalExpenseMap(self):
        return self.hospitalExpenseMap

    def getYearOfDate(self, date: datetime.date):
        return date.year

    def getMonthOfDate(self, date: datetime.date):
        return date.month