import bcrypt
from model.User import User
from repository.UserRepository import UserRepository

class UserService:
    def __init__(self, userRepository: UserRepository):
        self.userRepository = userRepository

    def login(self, user: User):
        userFromDB = self.userRepository.getUserByUsername(user.getUsername())
        if userFromDB is None:
            raise ValueError("Invalid credentials.")
        if not bcrypt.checkpw(user.getPassword().encode("utf-8"), userFromDB.getPassword().encode("utf-8")):
            raise ValueError("Invalid credentials.")
        return userFromDB.getUserType()

    def register(self, user: User):
        hashedPassword = self.hash_password(user.getPassword())
        user.setPassword(hashedPassword)
        self.userRepository.addUser(user)

    def hash_password(self, password: str) -> str:
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)

        return hashed_password.decode("utf-8")
