from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import HistoricalWeather, Location
from app.services.weather_service import WeatherService


class HistoricalWeatherService:
    def __init__(self, weather: WeatherService | None = None) -> None:
        self.weather = weather or WeatherService()

    async def fetch(
        self, lat: float, lon: float, start: date, end: date
    ) -> list[dict[str, Any]]:
        if (end - start).days > 365 * 30:
            raise ValueError("Date range too large")
        return await self.weather.provider.historical(lat, lon, start, end)

    def persist(self, db: Session, location: Location, rows: list[dict[str, Any]]) -> int:
        n = 0
        for row in rows:
            db.add(
                HistoricalWeather(
                    location_id=location.id,
                    date=date.fromisoformat(str(row["date"])[:10]),
                    temperature=row.get("temperature"),
                    rainfall=row.get("rainfall"),
                    humidity=row.get("humidity"),
                    wind_speed=row.get("wind_speed"),
                    source=row.get("source") or "unknown",
                    is_demo=bool(row.get("is_demo")),
                )
            )
            n += 1
        db.commit()
        return n

    def statistics(self, rows: list[dict[str, Any]], parameter: str) -> dict[str, Any]:
        values = [r.get(parameter) for r in rows if r.get(parameter) is not None]
        if not values:
            return {
                "parameter": parameter,
                "count": 0,
                "mean": None,
                "min": None,
                "max": None,
                "change_pct": None,
                "error": "No values available for this parameter",
            }
        half = max(1, len(values) // 2)
        first = sum(values[:half]) / half
        second = sum(values[half:]) / (len(values) - half)
        change = None if first == 0 else ((second - first) / abs(first)) * 100
        yearly: dict[str, list[float]] = {}
        for r in rows:
            if r.get(parameter) is None:
                continue
            y = str(r["date"])[:4]
            yearly.setdefault(y, []).append(float(r[parameter]))
        yearly_mean = {y: sum(vs) / len(vs) for y, vs in sorted(yearly.items())}
        return {
            "parameter": parameter,
            "count": len(values),
            "mean": round(sum(values) / len(values), 3),
            "min": round(min(values), 3),
            "max": round(max(values), 3),
            "sum": round(sum(values), 3) if parameter == "rainfall" else None,
            "change_pct": round(change, 2) if change is not None else None,
            "first_half_mean": round(first, 3),
            "second_half_mean": round(second, 3),
            "yearly_mean": yearly_mean,
            "is_demo": any(r.get("is_demo") for r in rows),
        }
