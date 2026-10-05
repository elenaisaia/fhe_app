from pydantic import BaseModel
from datetime import date
from typing import Optional


class PatientHospitalizationCreate(BaseModel):
    patientId: str | None = None
    name: str | None = None
    ageCategory: str |None = None
    diagnosis: str | None = None
    ward: str | None = None
    admissionDate: date | None = None
    dischargeDate: date | None = None
    died: bool | None = False
    costServices: float | None = 0.0
    costHospitalization: float | None = 0.0
    costMeds: float | None = 0.0
    costMeals: float | None = 0.0


class PatientHospitalizationResponse(BaseModel):
    message: str

    class Config:
        from_attributes = True


