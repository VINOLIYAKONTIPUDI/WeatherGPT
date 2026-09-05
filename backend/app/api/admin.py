from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.rbac import require_roles
from app.db.session import get_db
from app.integrations.models.forecast_model import ForecastModelService, SatelliteDataService
from app.models.entities import Alert, User, UserRole, WeatherObservation
from app.services.weather_service import get_weather_provider

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/system-status")
def system_status(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.disaster_manager)),
):
    settings = get_settings()
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    models = ForecastModelService()
    sat = SatelliteDataService()
    return {
        "app": settings.app_name,
        "env": settings.app_env,
        "demo_mode": settings.demo_mode,
        "time": datetime.utcnow().isoformat(),
        "database": "ok" if db_ok else "error",
        "weather_provider": get_weather_provider().name,
        "llm_configured": bool(settings.llm_api_key),
        "alerts_count": db.query(Alert).count(),
        "observations_count": db.query(WeatherObservation).count(),
        "forecast_models": models.available_models(),
        "satellite": {"status": "adapter-only"},
        "requested_by": user.email or user.phone,
    }


@router.get("/models")
async def models_placeholder(user: User = Depends(require_roles(UserRole.admin, UserRole.researcher))):
    svc = ForecastModelService()
    sat = SatelliteDataService()
    return {
        "gfs": await svc.fetch_gfs(16.5, 80.6),
        "wrf": await svc.fetch_wrf(16.5, 80.6),
        "satellite": await sat.latest_scene("andhra-pradesh"),
        "available": svc.available_models(),
    }
