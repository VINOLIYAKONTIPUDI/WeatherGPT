from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field

from app.models.entities import LanguageCode, UserRole


class OTPSendRequest(BaseModel):
    identifier: str = Field(..., min_length=5, max_length=255, description="Phone or email")
    name: str | None = Field(default=None, max_length=120)
    role: UserRole = UserRole.public
    preferred_language: LanguageCode = LanguageCode.en


class OTPVerifyRequest(BaseModel):
    identifier: str
    otp: str = Field(..., min_length=4, max_length=8)
    name: str | None = None
    role: UserRole = UserRole.public
    preferred_language: LanguageCode = LanguageCode.en


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]
    demo: bool = False


class ProfileUpdate(BaseModel):
    name: str | None = None
    preferred_language: LanguageCode | None = None
    location_id: int | None = None
    location_name: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    language: LanguageCode | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    location: str | None
    data_source: str | None
    timestamp: datetime
    grounded: bool
    used_llm: bool
    retrieved_data: dict[str, Any] | None = None
    is_demo: bool = False
    candidates: list[dict[str, Any]] | None = None
    disclaimer: str | None = None


class AdvisoryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    advisory_type: Literal["agriculture", "travel", "general"] = "agriculture"
    location: str | None = None
    language: LanguageCode = LanguageCode.en


class CropAdvisoryRequest(BaseModel):
    crop: Literal["Paddy", "Cotton", "Maize", "Groundnut", "Wheat"] = "Paddy"
    stage: Literal["Sowing", "Vegetative", "Flowering", "Harvest"] = "Vegetative"
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    weather_data: dict[str, Any] | None = None


class CropAdvisoryResponse(BaseModel):
    crop: str
    stage: str
    overall_risk: Literal["Low", "Moderate", "High"]
    summary: str
    recommendations: dict[str, str]
    weather_factors: dict[str, Any]
    disclaimer: str



class HistoricalQuery(BaseModel):
    location: str
    start_date: date
    end_date: date
    parameter: Literal["temperature", "rainfall", "humidity", "wind_speed"] = "rainfall"
    compare_year: int | None = None


class VoiceTranscribeRequest(BaseModel):
    text: str | None = None
    language: LanguageCode = LanguageCode.en
    mock_audio: bool = True


class DemoAlertRequest(BaseModel):
    alert_type: str = "cyclone"
    location: str = "Vijayawada"
    severity: str = "severe"
