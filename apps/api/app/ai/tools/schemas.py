import uuid
from datetime import date

from pydantic import BaseModel, Field


class GetMyTokenStatusArgs(BaseModel):
    public_code: str = Field(..., description="The unguessable public code of the token")


class GetClinicInfoArgs(BaseModel):
    clinic_id: uuid.UUID = Field(..., description="ID of the clinic to query")


class GetPatientHistoryArgs(BaseModel):
    patient_id: uuid.UUID = Field(..., description="ID of the patient")
    clinic_id: uuid.UUID = Field(..., description="Clinic ID context")


class GetDailyStatsArgs(BaseModel):
    clinic_id: uuid.UUID = Field(..., description="Clinic ID context")
    start_date: date = Field(..., description="Start of date range (YYYY-MM-DD)")
    end_date: date = Field(..., description="End of date range (YYYY-MM-DD)")


class DetectAnomaliesArgs(BaseModel):
    clinic_id: uuid.UUID = Field(..., description="Clinic ID context")
    target_date: date = Field(..., description="Date to analyze for anomalies (YYYY-MM-DD)")


class GetConsultDurationsArgs(BaseModel):
    doctor_id: uuid.UUID = Field(..., description="Doctor ID")
    limit: int = Field(default=10, ge=1, le=50, description="Number of recent consult durations")


class SaveWaitPredictionArgs(BaseModel):
    token_id: uuid.UUID = Field(..., description="Token ID")
    clinic_id: uuid.UUID = Field(..., description="Clinic ID context")
    predicted_minutes: int = Field(..., ge=0, le=720, description="Predicted wait time in minutes")
    model_version: str = Field(default="v1", description="Identifier of the model/algorithm used")
