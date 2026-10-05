from schemas.HospitalExpenseSchema import HospitalExpenseCreate, HospitalExpenseResponse

class HospitalExpense:
    def __init__(self):
        self.__id = None
        self.__description = None
        self.__expenseDate = None
        self.__expenseType = None
        self.__amount = None

    def setId(self, id):
        self.__id = id

    def setDescription(self, description):
        self.__description = description

    def setExpenseDate(self, expenseDate):
        self.__expenseDate = expenseDate

    def setExpenseType(self, expenseType):
        self.__expenseType = expenseType

    def setAmount(self, amount):
        self.__amount = amount

    def getId(self):
        return self.__id

    def getDescription(self):
        return self.__description

    def getExpenseDate(self):
        return self.__expenseDate

    def getExpenseType(self):
        return self.__expenseType

    def getAmount(self):
        return self.__amount

    def createHospitalExpense(self, request: HospitalExpenseCreate):
        self.__description = request.description
        self.__expenseDate = request.expenseDate
        self.__expenseType = request.expenseType
        self.__amount = request.amount

    def __str__(self):
        return (f"HospitalExpense(id={self.__id}, "
                f"description={self.__description}, "
                f"expense_date={self.__expenseDate}, "
                f"expense_type={self.__expenseType}, "
                f"amount={self.__amount})")