import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.ai.grounding import ADVISORY_DISCLAIMER, SYSTEM_PROMPT, build_grounded_user_prompt
from app.ai.parser import ParsedQuery, format_simple_answer, parse_weather_query
from app.config import get_settings
from app.integrations.llm.demo import DemoLLMProvider
from app.integrations.llm.openai_compat import OpenAICompatProvider
from app.models.entities import ChatHistory, LanguageCode, User
from app.services.alert_service import AlertService
from app.services.forecast_service import ForecastService
from app.services.location_service import LocationService
from app.services.weather_service import WeatherService

logger = logging.getLogger("weathergpt.ai")


class AIQueryService:
    def __init__(
        self,
        weather: WeatherService | None = None,
        forecast: ForecastService | None = None,
        alerts: AlertService | None = None,
        locations: LocationService | None = None,
    ) -> None:
        self.weather = weather or WeatherService()
        self.forecast = forecast or ForecastService(self.weather)
        self.alerts = alerts or AlertService()
        self.locations = locations or LocationService()

    def _llm(self):
        settings = get_settings()
        if settings.llm_api_key and settings.llm_provider != "demo":
            return OpenAICompatProvider()
        return DemoLLMProvider()

    async def resolve_location(
        self,
        db: Session,
        parsed: ParsedQuery,
        user: User | None,
        latitude: float | None,
        longitude: float | None,
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        if latitude is not None and longitude is not None:
            name = parsed.location_text or "Selected coordinates"
            loc = self.locations.get_or_create(db, name, latitude, longitude)
            return {
                "id": loc.id,
                "name": loc.name,
                "district": loc.district,
                "state": loc.state,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
            }, []
        query = parsed.location_text
        if not query and user and user.locations:
            loc = user.locations[0].location
            return {
                "id": loc.id,
                "name": loc.name,
                "district": loc.district,
                "state": loc.state,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
            }, []
        if not query:
            loc = self.locations.default_vijayawada(db)
            if loc:
                return {
                    "id": loc.id,
                    "name": loc.name,
                    "district": loc.district,
                    "state": loc.state,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                }, []
            return None, []
        db_hits = self.locations.search_db(db, query)
        remote = await self.weather.search_locations(query)
        candidates = []
        for h in db_hits:
            candidates.append(
                {
                    "name": h.name,
                    "district": h.district,
                    "state": h.state,
                    "latitude": h.latitude,
                    "longitude": h.longitude,
                    "source": "db",
                }
            )
        for h in remote:
            if not any(abs(h["latitude"] - c["latitude"]) < 0.05 for c in candidates if h.get("latitude")):
                candidates.append(h)
        if len(candidates) > 1 and parsed.location_text:
            # ambiguous if names differ substantially
            names = {c["name"].lower() for c in candidates[:4]}
            if len(names) > 1:
                return None, candidates[:5]
        if not candidates:
            return None, []
        top = candidates[0]
        loc = self.locations.get_or_create(
            db,
            top["name"],
            top["latitude"],
            top["longitude"],
            top.get("district"),
            top.get("state"),
        )
        return {
            "id": loc.id,
            "name": loc.name,
            "district": loc.district,
            "state": loc.state,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
        }, []

    async def retrieve(self, db: Session, parsed: ParsedQuery, loc: dict[str, Any]) -> dict[str, Any]:
        lat, lon = loc["latitude"], loc["longitude"]
        current = await self.weather.current(lat, lon)
        forecast = await self.weather.forecast(lat, lon, days=7)
        tomorrow = None
        if parsed.target_date:
            tomorrow = await self.forecast.for_date(lat, lon, parsed.target_date)
        elif parsed.date_label == "tomorrow":
            from datetime import date, timedelta

            tomorrow = await self.forecast.for_date(lat, lon, date.today() + timedelta(days=1))
        nearby_alerts = []
        if parsed.intent in ("severe_weather", "disaster_information", "travel_advisory"):
            nearby_alerts = [
                {
                    "title": a.title,
                    "severity": a.severity,
                    "type": a.alert_type,
                    "is_demo": a.is_demo,
                    "source": a.source,
                }
                for a in self.alerts.nearby(db, lat, lon)
            ]
        is_demo = bool(current.get("is_demo") or forecast.get("is_demo"))
        facts: dict[str, Any] = {
            "location_name": loc["name"],
            "current": current,
            "tomorrow": tomorrow,
            "daily_forecast": (forecast.get("daily") or [])[:7],
            "alerts": nearby_alerts,
            "source": current.get("source") or forecast.get("source"),
            "is_demo": is_demo,
            "retrieved_at": datetime.utcnow().isoformat(),
        }
        # flatten common keys for simple prompts
        src = tomorrow or current
        facts["temperature"] = src.get("temperature") or src.get("temp_max")
        facts["rain_probability"] = src.get("rain_probability")
        facts["rainfall"] = src.get("rainfall")
        facts["wind_speed"] = src.get("wind_speed")
        facts["humidity"] = src.get("humidity") or current.get("humidity")
        facts["condition"] = src.get("condition") or current.get("condition")
        return facts

    async def answer(
        self,
        db: Session,
        message: str,
        language: str | None,
        location: str | None,
        user: User | None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict[str, Any]:
        parsed = parse_weather_query(message, language, location)
        loc, candidates = await self.resolve_location(db, parsed, user, latitude, longitude)
        if candidates:
            return {
                "answer": "Several locations match your query. Please select one.",
                "intent": parsed.intent,
                "location": None,
                "data_source": None,
                "timestamp": datetime.utcnow(),
                "grounded": True,
                "used_llm": False,
                "retrieved_data": None,
                "is_demo": False,
                "candidates": candidates,
            }
        if not loc:
            return {
                "answer": "I could not resolve that location. Please name a city or district.",
                "intent": parsed.intent,
                "location": None,
                "data_source": None,
                "timestamp": datetime.utcnow(),
                "grounded": True,
                "used_llm": False,
                "retrieved_data": None,
                "is_demo": False,
                "candidates": None,
            }
        try:
            retrieved = await self.retrieve(db, parsed, loc)
        except Exception:
            logger.exception("weather_retrieve_failed")
            return {
                "answer": "Live weather data is temporarily unavailable. Please try again.",
                "intent": parsed.intent,
                "location": loc["name"],
                "data_source": None,
                "timestamp": datetime.utcnow(),
                "grounded": True,
                "used_llm": False,
                "retrieved_data": None,
                "is_demo": False,
            }

        used_llm = False
        if parsed.needs_llm:
            try:
                llm = self._llm()
                user_prompt = build_grounded_user_prompt(
                    message,
                    parsed.__dict__,
                    retrieved,
                )
                answer = await llm.complete(SYSTEM_PROMPT, user_prompt)
                used_llm = True
                logger.info("llm_completed intent=%s provider=%s", parsed.intent, llm.name)
            except Exception:
                logger.exception("llm_failed_falling_back_to_facts")
                answer = format_simple_answer(parsed, retrieved, loc["name"])
        else:
            answer = format_simple_answer(parsed, retrieved, loc["name"])

        if parsed.intent in ("agricultural_advisory", "travel_advisory") and ADVISORY_DISCLAIMER not in answer:
            answer = answer.rstrip() + " " + ADVISORY_DISCLAIMER

        history = ChatHistory(
            user_id=user.id if user else None,
            question=message,
            intent=parsed.intent,
            retrieved_data=retrieved,
            response=answer,
            language=parsed.language,
            grounded=True,
            used_llm=used_llm,
        )
        db.add(history)
        db.commit()

        return {
            "answer": answer,
            "intent": parsed.intent,
            "location": loc["name"],
            "data_source": retrieved.get("source"),
            "timestamp": datetime.utcnow(),
            "grounded": True,
            "used_llm": used_llm,
            "retrieved_data": retrieved,
            "is_demo": retrieved.get("is_demo", False),
            "candidates": None,
            "disclaimer": ADVISORY_DISCLAIMER
            if parsed.intent in ("agricultural_advisory", "travel_advisory")
            else None,
        }
