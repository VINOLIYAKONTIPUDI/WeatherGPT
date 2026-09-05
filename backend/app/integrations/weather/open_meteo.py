from datetime import date, datetime
from typing import Any

import httpx

from app.config import get_settings
from app.integrations.weather.base import WeatherProvider

WMO = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def describe_weather(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return WMO.get(int(code), f"Weather code {code}")


class OpenMeteoProvider(WeatherProvider):
    name = "open-meteo"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def geocode(self, query: str) -> list[dict[str, Any]]:
        params = {"name": query, "count": 6, "language": "en", "format": "json"}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(self.settings.weather_geocode_url, params=params)
            resp.raise_for_status()
            data = resp.json()
        results = []
        for item in data.get("results") or []:
            results.append(
                {
                    "name": item.get("name"),
                    "district": item.get("admin2") or item.get("admin1"),
                    "state": item.get("admin1"),
                    "country": item.get("country"),
                    "latitude": item.get("latitude"),
                    "longitude": item.get("longitude"),
                }
            )
        return results

    async def current(self, lat: float, lon: float) -> dict[str, Any]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "rain",
                    "weather_code",
                    "cloud_cover",
                    "pressure_msl",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "is_day",
                ]
            ),
            "daily": "sunrise,sunset,precipitation_probability_max",
            "forecast_days": 1,
            "timezone": "auto",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{self.settings.weather_api_base_url}/forecast", params=params)
            resp.raise_for_status()
            data = resp.json()
        cur = data.get("current") or {}
        daily = data.get("daily") or {}
        sunrise = (daily.get("sunrise") or [None])[0]
        sunset = (daily.get("sunset") or [None])[0]
        rain_p = (daily.get("precipitation_probability_max") or [None])[0]
        return {
            "temperature": cur.get("temperature_2m"),
            "feels_like": cur.get("apparent_temperature"),
            "humidity": cur.get("relative_humidity_2m"),
            "rainfall": cur.get("rain") or cur.get("precipitation"),
            "weather_code": cur.get("weather_code"),
            "condition": describe_weather(cur.get("weather_code")),
            "cloud_cover": cur.get("cloud_cover"),
            "pressure": cur.get("pressure_msl"),
            "wind_speed": cur.get("wind_speed_10m"),
            "wind_direction": cur.get("wind_direction_10m"),
            "is_day": cur.get("is_day"),
            "sunrise": sunrise,
            "sunset": sunset,
            "rain_probability": rain_p,
            "observed_at": cur.get("time"),
            "source": self.name,
            "is_demo": False,
            "timezone": data.get("timezone"),
        }

    async def forecast(self, lat: float, lon: float, days: int = 7) -> dict[str, Any]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "precipitation_probability",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "pressure_msl",
                ]
            ),
            "daily": ",".join(
                [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "sunrise",
                    "sunset",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                    "wind_direction_10m_dominant",
                ]
            ),
            "forecast_days": min(days, 16),
            "timezone": "auto",
        }
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.get(f"{self.settings.weather_api_base_url}/forecast", params=params)
            resp.raise_for_status()
            data = resp.json()
        hourly = data.get("hourly") or {}
        daily = data.get("daily") or {}
        hours = []
        times = hourly.get("time") or []
        for i, t in enumerate(times[: 24 * days]):
            hours.append(
                {
                    "time": t,
                    "temperature": _idx(hourly.get("temperature_2m"), i),
                    "humidity": _idx(hourly.get("relative_humidity_2m"), i),
                    "rain_probability": _idx(hourly.get("precipitation_probability"), i),
                    "rainfall": _idx(hourly.get("precipitation"), i),
                    "weather_code": _idx(hourly.get("weather_code"), i),
                    "condition": describe_weather(_idx(hourly.get("weather_code"), i)),
                    "wind_speed": _idx(hourly.get("wind_speed_10m"), i),
                    "wind_direction": _idx(hourly.get("wind_direction_10m"), i),
                    "pressure": _idx(hourly.get("pressure_msl"), i),
                }
            )
        days_out = []
        dtimes = daily.get("time") or []
        for i, t in enumerate(dtimes):
            days_out.append(
                {
                    "date": t,
                    "temp_max": _idx(daily.get("temperature_2m_max"), i),
                    "temp_min": _idx(daily.get("temperature_2m_min"), i),
                    "sunrise": _idx(daily.get("sunrise"), i),
                    "sunset": _idx(daily.get("sunset"), i),
                    "rainfall": _idx(daily.get("precipitation_sum"), i),
                    "rain_probability": _idx(daily.get("precipitation_probability_max"), i),
                    "wind_speed": _idx(daily.get("wind_speed_10m_max"), i),
                    "wind_direction": _idx(daily.get("wind_direction_10m_dominant"), i),
                    "weather_code": _idx(daily.get("weather_code"), i),
                    "condition": describe_weather(_idx(daily.get("weather_code"), i)),
                }
            )
        return {
            "hourly": hours,
            "daily": days_out,
            "source": self.name,
            "model_name": "open-meteo ensemble/default",
            "is_demo": False,
            "retrieved_at": datetime.utcnow().isoformat(),
        }

    async def historical(
        self, lat: float, lon: float, start: date, end: date
    ) -> list[dict[str, Any]]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": "temperature_2m_mean,precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_max",
            "timezone": "auto",
        }
        async with httpx.AsyncClient(timeout=40) as client:
            resp = await client.get(self.settings.weather_archive_url, params=params)
            resp.raise_for_status()
            data = resp.json()
        daily = data.get("daily") or {}
        rows = []
        for i, d in enumerate(daily.get("time") or []):
            rows.append(
                {
                    "date": d,
                    "temperature": _idx(daily.get("temperature_2m_mean"), i),
                    "rainfall": _idx(daily.get("precipitation_sum"), i),
                    "humidity": _idx(daily.get("relative_humidity_2m_mean"), i),
                    "wind_speed": _idx(daily.get("wind_speed_10m_max"), i),
                    "source": self.name,
                    "is_demo": False,
                }
            )
        return rows


def _idx(arr: list | None, i: int):
    if not arr or i >= len(arr):
        return None
    return arr[i]
