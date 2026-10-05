from schemas.UserSchema import UserCreate, UserResponse

class User:
    def __init__(self):
        self.__username = None
        self.__password = None
        self.__userType = None

    def setUsername(self,username):
        self.__username = username

    def setPassword(self,password):
        self.__password = password

    def setUserType(self, userType):
        self.__userType = userType

    def getUsername(self):
        return self.__username

    def getPassword(self):
        return self.__password

    def getUserType(self):
        return self.__userType

    def createUserFromUserCreate(self, request: UserCreate):
        self.__username = request.username
        self.__password = request.password
        self.__userType = request.userType

    def createUserFromDB(self, res):
        self.__username = res['username']
        self.__password = res['password']
        self.__userType = res['userType']

    def __str__(self):
        return (f"User(id={self.__username}, "
                f"password={self.__password}, "
                f"userType={self.__userType})")