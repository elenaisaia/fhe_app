from fastapi import APIRouter, HTTPException
from model.User import User
from service.UserService import UserService
from schemas.UserSchema import UserCreate, UserResponse

class UserController:
    def __init__(self, userService: UserService):
        self.router = APIRouter(
            prefix="/login",
            tags=["Login"]
        )
        self.userService = userService

        self.router.add_api_route(
            "",
            self.login,
            methods=["POST"]
        )

    def login(self, request: UserCreate):
        try:
            user = User()
            user.createUserFromUserCreate(request)
            userType = self.userService.login(user)
            return UserResponse(userType=userType, message="Login successful.")
        except ValueError as error:
            raise HTTPException(status_code=401, detail=str(error))