from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str
    userType: str | None = None


class UserResponse(BaseModel):
    userType: str
    message: str

    class Config:
        from_attributes = True