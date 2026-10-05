from pydantic import BaseModel
from datetime import date
from typing import Optional


class HospitalExpenseCreate(BaseModel):
    description: str
    expenseDate: date
    expenseType: str
    amount: float


class HospitalExpenseResponse(BaseModel):
    message: str

    class Config:
        from_attributes = True

