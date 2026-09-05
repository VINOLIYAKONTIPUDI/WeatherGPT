from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LocationCoordinates(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = "Selected Location"
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    admin1: Optional[str] = None  # State / Region
    displayName: Optional[str] = None
    display_name: Optional[str] = None
    source: Optional[str] = "search" # 'gps' | 'search'

class WeatherCurrent(BaseModel):
    temperature: float
    apparent_temperature: float
    relative_humidity: int
    wind_speed: float
    wind_direction: int
    precipitation: float
    rain_probability: int
    weather_code: int
    condition: str
    is_day: int = 1
    uv_index: float
    sunrise: Optional[str] = None
    sunset: Optional[str] = None

class HourlyForecastItem(BaseModel):
    time: str
    temperature: float
    apparent_temperature: float
    precipitation_probability: int
    precipitation: float
    weather_code: int
    condition: str
    wind_speed: float
    uv_index: float

class DailyForecastItem(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    precipitation_probability_max: int
    precipitation_sum: float
    weather_code: int
    condition: str
    uv_index_max: float
    sunrise: str
    sunset: str

class WeatherForecastResponse(BaseModel):
    location: LocationCoordinates
    current: WeatherCurrent
    hourly: List[HourlyForecastItem]
    daily: List[DailyForecastItem]
    is_fallback: bool = False

class AdvisoryItem(BaseModel):
    id: str
    severity: str  # 'danger', 'warning', 'advisory', 'info', 'safe'
    title: str
    description: str
    recommendation: str
    timeframe: str
    icon: str

class AlertsResponse(BaseModel):
    location: LocationCoordinates
    alerts: List[AdvisoryItem]
    count: int
    has_critical_hazard: bool = False

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    location: Optional[LocationCoordinates] = None
    language: str = "en-IN"  # 'en-IN', 'hi-IN', 'te-IN'
    conversation: List[ChatMessage] = []

class ChatResponse(BaseModel):
    answer: str
    language: str
    intent: str
    location: Optional[LocationCoordinates] = None
    weather: Optional[Dict[str, Any]] = None
    advisory: Optional[AdvisoryItem] = None
    suggested_followups: List[str] = []
    is_fallback: bool = False
    is_location_required: bool = False
    explicit_override: bool = False

class LocationSearchResult(BaseModel):
    id: Optional[int] = None
    name: str
    latitude: float
    longitude: float
    country: Optional[str] = None
    admin1: Optional[str] = None
    display_name: str

# Authentication Schemas
class UserSignupRequest(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: str

class UserVerifyOTPRequest(BaseModel):
    email: str
    otp: str

class UserResendOTPRequest(BaseModel):
    email: str

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    is_verified: bool

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class SMSBroadcastRequest(BaseModel):
    phone_numbers: Optional[List[str]] = None
    alert_type: str = "Severe Weather Warning"
    location_name: str = "Selected Location"
    recommendation: str = "Seek immediate indoor shelter and follow emergency safety guidelines."
    severity: str = "danger"

class SMSBroadcastResponse(BaseModel):
    success: bool
    alert_type: str
    location: str
    severity: str
    recipient_count: int
    recipients: List[str]
    dispatched_at: str
    message_preview: str
    broadcast_mode: str
    dispatch_receipts: List[Dict[str, Any]]


