from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai.grounding import SYSTEM_PROMPT, build_grounded_user_prompt
from app.config import get_settings
from app.core.rbac import get_optional_user, require_roles
from app.db.session import get_db
from app.integrations.llm.demo import DemoLLMProvider
from app.integrations.llm.openai_compat import OpenAICompatProvider
from app.models.entities import User, UserRole
from app.services.historical_weather_service import HistoricalWeatherService
from app.services.location_service import LocationService
from app.services.weather_service import WeatherService

router = APIRouter(tags=["climate"])
hist = HistoricalWeatherService()
locations = LocationService()
weather = WeatherService()


@router.get("/historical")
async def historical(
    location: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    parameter: str = Query("rainfall"),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    _guard_range(start_date, end_date)
    loc = await _loc(db, location)
    try:
        rows = await hist.fetch(loc["latitude"], loc["longitude"], start_date, end_date)
    except Exception as exc:
        raise HTTPException(503, "Historical weather data is temporarily unavailable. Please try again.") from exc
    stats = hist.statistics(rows, parameter)
    return {"location": loc, "rows": rows, "statistics": stats, "is_demo": stats.get("is_demo")}


@router.get("/climate/trends")
async def climate_trends(
    location: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    parameter: str = Query("rainfall"),
    language: str = Query("en"),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    _guard_range(start_date, end_date)
    loc = await _loc(db, location)
    rows = await hist.fetch(loc["latitude"], loc["longitude"], start_date, end_date)
    stats = hist.statistics(rows, parameter)
    explanation = None
    try:
        settings = get_settings()
        llm = OpenAICompatProvider() if settings.llm_api_key else DemoLLMProvider()
        parsed = {
            "intent": "climate_trend",
            "language": language,
            "date_label": f"{start_date} to {end_date}",
        }
        retrieved = {
            "location_name": loc["name"],
            "statistics": stats,
            "is_demo": stats.get("is_demo"),
            "source": rows[0]["source"] if rows else None,
            "note": "Explain only these calculated statistics. Do not invent numbers.",
        }
        explanation = await llm.complete(
            SYSTEM_PROMPT,
            build_grounded_user_prompt(
                f"Explain the {parameter} trend for {loc['name']} using only the statistics.",
                parsed,
                retrieved,
            ),
        )
    except Exception:
        change = stats.get("change_pct")
        prefix = "[DEMO DATA] " if stats.get("is_demo") else ""
        if change is None:
            explanation = prefix + "Trend cannot be computed because statistics are incomplete."
        else:
            direction = "increased" if change > 0 else "decreased"
            explanation = (
                f"{prefix}Average {parameter} has {direction} by {abs(change)}% "
                f"during the selected period (first-half mean {stats.get('first_half_mean')} "
                f"vs second-half mean {stats.get('second_half_mean')})."
            )
    return {
        "location": loc,
        "statistics": stats,
        "yearly_mean": stats.get("yearly_mean"),
        "explanation": explanation,
        "grounded": True,
        "is_demo": stats.get("is_demo"),
    }


async def _loc(db, name: str) -> dict:
    hits = locations.search_db(db, name)
    if hits:
        h = hits[0]
        return {"id": h.id, "name": h.name, "latitude": h.latitude, "longitude": h.longitude}
    remote = await weather.search_locations(name)
    if not remote:
        raise HTTPException(404, "Location not found")
    r = remote[0]
    loc = locations.get_or_create(db, r["name"], r["latitude"], r["longitude"], r.get("district"), r.get("state"))
    return {"id": loc.id, "name": loc.name, "latitude": loc.latitude, "longitude": loc.longitude}


def _guard_range(start: date, end: date) -> None:
    if end < start:
        raise HTTPException(400, "end_date must be after start_date")
    if (end - start).days > 365 * 40:
        raise HTTPException(400, "Range too large")
