from datetime import date, datetime, timedelta
from typing import Any

from app.integrations.weather.base import WeatherProvider

DEMO_CITIES = {
    "vijayawada": {"name": "Vijayawada", "district": "NTR", "state": "Andhra Pradesh", "latitude": 16.5062, "longitude": 80.6480},
    "hyderabad": {"name": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "latitude": 17.3850, "longitude": 78.4867},
    "visakhapatnam": {"name": "Visakhapatnam", "district": "Visakhapatnam", "state": "Andhra Pradesh", "latitude": 17.6868, "longitude": 83.2185},
    "new delhi": {"name": "New Delhi", "district": "New Delhi", "state": "Delhi", "latitude": 28.6139, "longitude": 77.2090},
    "mumbai": {"name": "Mumbai", "district": "Mumbai", "state": "Maharashtra", "latitude": 19.0760, "longitude": 72.8777},
}


class DemoWeatherProvider(WeatherProvider):
    """Deterministic labelled demo weather. Never presented as live IMD data."""

    name = "demo"

    async def geocode(self, query: str) -> list[dict[str, Any]]:
        q = query.lower().strip()
        hits = [v | {"country": "India"} for k, v in DEMO_CITIES.items() if q in k or q in v["name"].lower()]
        if hits:
            return hits
        return [DEMO_CITIES["vijayawada"] | {"country": "India"}]

    async def current(self, lat: float, lon: float) -> dict[str, Any]:
        return {
            "temperature": 29.0,
            "feels_like": 32.0,
            "humidity": 78.0,
            "rainfall": 0.4,
            "weather_code": 80,
            "condition": "Slight rain showers",
            "cloud_cover": 72,
            "pressure": 1008.0,
            "wind_speed": 15.0,
            "wind_direction": 210,
            "is_day": 1,
            "sunrise": datetime.utcnow().replace(hour=0, minute=45).isoformat(),
            "sunset": datetime.utcnow().replace(hour=12, minute=50).isoformat(),
            "rain_probability": 80,
            "observed_at": datetime.utcnow().isoformat(),
            "source": "DEMO DATA",
            "is_demo": True,
            "timezone": "Asia/Kolkata",
        }

    async def forecast(self, lat: float, lon: float, days: int = 7) -> dict[str, Any]:
        now = datetime.utcnow()
        hourly = []
        daily = []
        for h in range(24 * min(days, 7)):
            t = now + timedelta(hours=h)
            rain_p = 80 if h < 36 else 35
            hourly.append(
                {
                    "time": t.isoformat(),
                    "temperature": 29 - (h % 8) * 0.4,
                    "humidity": 75,
                    "rain_probability": rain_p,
                    "rainfall": 1.2 if rain_p > 60 else 0.1,
                    "weather_code": 63 if rain_p > 60 else 2,
                    "condition": "Moderate rain" if rain_p > 60 else "Partly cloudy",
                    "wind_speed": 15 + (h % 5),
                    "wind_direction": 210,
                    "pressure": 1008,
                }
            )
        for d in range(min(days, 7)):
            day = (now + timedelta(days=d)).date()
            rain_p = 80 if d == 1 else 40 - d * 4
            daily.append(
                {
                    "date": day.isoformat(),
                    "temp_max": 32 - d * 0.3,
                    "temp_min": 24,
                    "sunrise": datetime.combine(day, datetime.min.time()).replace(hour=6, minute=5).isoformat(),
                    "sunset": datetime.combine(day, datetime.min.time()).replace(hour=18, minute=20).isoformat(),
                    "rainfall": 18.0 if d == 1 else 2.0,
                    "rain_probability": rain_p,
                    "wind_speed": 18 if d == 1 else 12,
                    "wind_direction": 210,
                    "weather_code": 63 if d == 1 else 2,
                    "condition": "Moderate rain" if d == 1 else "Partly cloudy",
                }
            )
        return {
            "hourly": hourly,
            "daily": daily,
            "source": "DEMO DATA",
            "model_name": "demo-adapter",
            "is_demo": True,
            "retrieved_at": now.isoformat(),
        }

    async def historical(
        self, lat: float, lon: float, start: date, end: date
    ) -> list[dict[str, Any]]:
        rows = []
        cur = start
        i = 0
        while cur <= end and i < 4000:
            year_factor = (cur.year - 2000) * 0.8
            monsoon = 12 if cur.month in (6, 7, 8, 9) else 1.5
            rows.append(
                {
                    "date": cur.isoformat(),
                    "temperature": 28 + (cur.month - 6) * 0.4,
                    "rainfall": max(0, monsoon + year_factor * 0.05 + (i % 7) * 0.3),
                    "humidity": 70 + (i % 10),
                    "wind_speed": 10 + (i % 5),
                    "source": "DEMO DATA",
                    "is_demo": True,
                }
            )
            cur = cur + timedelta(days=max(1, (end - start).days // 120 or 1))
            i += 1
        return rows
