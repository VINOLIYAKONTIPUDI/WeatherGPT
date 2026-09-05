from datetime import date
from typing import Any

from app.services.weather_service import WeatherService


class ForecastService:
    def __init__(self, weather: WeatherService | None = None) -> None:
        self.weather = weather or WeatherService()

    async def daily(self, lat: float, lon: float, days: int = 7) -> dict[str, Any]:
        data = await self.weather.forecast(lat, lon, days)
        return {"daily": data.get("daily") or [], "source": data.get("source"), "is_demo": data.get("is_demo")}

    async def for_date(self, lat: float, lon: float, target: date) -> dict[str, Any] | None:
        data = await self.weather.forecast(lat, lon, days=10)
        for row in data.get("daily") or []:
            if str(row.get("date"))[:10] == target.isoformat():
                row = dict(row)
                row["temperature"] = row.get("temp_max")
                row["source"] = data.get("source")
                row["is_demo"] = data.get("is_demo")
                return row
        return None
