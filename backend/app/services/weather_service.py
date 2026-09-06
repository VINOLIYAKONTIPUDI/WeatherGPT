import httpx
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
from app.models.schemas import (
    LocationCoordinates, WeatherCurrent, HourlyForecastItem,
    DailyForecastItem, WeatherForecastResponse
)

logger = logging.getLogger(__name__)

# WMO Weather Interpretation Codes (WW)
WMO_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

def get_weather_condition(code: int) -> str:
    return WMO_CODE_MAP.get(code, "Partly Cloudy")

# In-memory LRU Cache with composite keys: "location_lat_lon|start_date|end_date|type"
_WEATHER_CACHE: Dict[str, Tuple[datetime, Any]] = {}
CACHE_TTL_SECONDS = 600  # 10 minutes

class WeatherService:
    @staticmethod
    def get_fallback_data(location: LocationCoordinates) -> WeatherForecastResponse:
        """Returns realistic fallback weather data if live API fails or network is offline."""
        current = WeatherCurrent(
            temperature=31.5,
            apparent_temperature=34.2,
            relative_humidity=68,
            wind_speed=14.5,
            wind_direction=180,
            precipitation=0.0,
            rain_probability=20,
            weather_code=2,
            condition="Partly Cloudy",
            is_day=1,
            uv_index=6.8,
            sunrise="06:05",
            sunset="18:35"
        )
        
        hourly = []
        for day in range(7):
            for i in range(24):
                hour_str = f"{i:02d}:00"
                temp = round(26 + (day % 3) + 7 * (1 - abs(i - 14) / 10), 1)
                pop = 70 if (7 <= i <= 11 and day == 1) else (30 if 13 <= i <= 17 else 10)
                hourly.append(HourlyForecastItem(
                    time=hour_str,
                    temperature=temp,
                    apparent_temperature=round(temp + 2.5, 1),
                    precipitation_probability=pop,
                    precipitation=2.5 if pop > 50 else 0.0,
                    weather_code=61 if pop > 50 else 2,
                    condition="Slight Rain" if pop > 50 else "Partly Cloudy",
                    wind_speed=12.0 + (i % 5),
                    uv_index=round(max(0, 8 - abs(i - 13) * 1.5), 1)
                ))
            
        daily = []
        days = ["Today", "Tomorrow", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
        for idx, day_name in enumerate(days):
            daily.append(DailyForecastItem(
                date=day_name,
                temperature_max=33.0 + (idx % 3),
                temperature_min=24.0 + (idx % 2),
                precipitation_probability_max=75 if idx == 1 else 30,
                precipitation_sum=8.2 if idx == 1 else 0.5,
                weather_code=63 if idx == 1 else 2,
                condition="Moderate Rain" if idx == 1 else "Partly Cloudy",
                uv_index_max=7.5,
                sunrise="06:05",
                sunset="18:35"
            ))
            
        return WeatherForecastResponse(
            location=location,
            current=current,
            hourly=hourly,
            daily=daily,
            is_fallback=True
        )

    @classmethod
    async def get_forecast(cls, latitude: float, longitude: float, location_name: str = "Selected Location") -> WeatherForecastResponse:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "is_day", "precipitation", "weather_code", "wind_speed_10m", "wind_direction_10m"
            ],
            "hourly": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "precipitation_probability", "precipitation", "weather_code",
                "wind_speed_10m", "uv_index"
            ],
            "daily": [
                "weather_code", "temperature_2m_max", "temperature_2m_min",
                "precipitation_sum", "precipitation_probability_max",
                "uv_index_max", "sunrise", "sunset"
            ],
            "timezone": "auto"
        }
        
        location_obj = LocationCoordinates(latitude=latitude, longitude=longitude, name=location_name)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    logger.warning(f"Open-Meteo API returned status {response.status_code}. Using fallback data.")
                    return cls.get_fallback_data(location_obj)

                data = response.json()
                
                # Parse current weather
                cur = data.get("current", {})
                current_uv = 5.0
                if "hourly" in data and "uv_index" in data["hourly"] and len(data["hourly"]["uv_index"]) > 0:
                    current_uv = data["hourly"]["uv_index"][0] or 5.0

                current_pop = 0
                if "hourly" in data and "precipitation_probability" in data["hourly"] and len(data["hourly"]["precipitation_probability"]) > 0:
                    current_pop = data["hourly"]["precipitation_probability"][0] or 0

                sunrise_val = "06:00"
                sunset_val = "18:30"
                if "daily" in data and "sunrise" in data["daily"] and len(data["daily"]["sunrise"]) > 0:
                    sunrise_val = data["daily"]["sunrise"][0].split("T")[-1][:5]
                if "daily" in data and "sunset" in data["daily"] and len(data["daily"]["sunset"]) > 0:
                    sunset_val = data["daily"]["sunset"][0].split("T")[-1][:5]

                weather_code = int(cur.get("weather_code", 0))
                current_obj = WeatherCurrent(
                    temperature=float(cur.get("temperature_2m", 25.0)),
                    apparent_temperature=float(cur.get("apparent_temperature", 26.0)),
                    relative_humidity=int(cur.get("relative_humidity_2m", 60)),
                    wind_speed=float(cur.get("wind_speed_10m", 10.0)),
                    wind_direction=int(cur.get("wind_direction_10m", 0)),
                    precipitation=float(cur.get("precipitation", 0.0)),
                    rain_probability=int(current_pop),
                    weather_code=weather_code,
                    condition=get_weather_condition(weather_code),
                    is_day=int(cur.get("is_day", 1)),
                    uv_index=float(current_uv),
                    sunrise=sunrise_val,
                    sunset=sunset_val
                )

                # Parse hourly forecast (all 7 days / 168 hours)
                hourly_list = []
                h_data = data.get("hourly", {})
                times = h_data.get("time", [])
                temps = h_data.get("temperature_2m", [])
                app_temps = h_data.get("apparent_temperature", [])
                pops = h_data.get("precipitation_probability", [])
                precips = h_data.get("precipitation", [])
                codes = h_data.get("weather_code", [])
                winds = h_data.get("wind_speed_10m", [])
                uvs = h_data.get("uv_index", [])

                for i in range(len(times)):
                    t_str = times[i].split("T")[-1][:5] if "T" in times[i] else f"{i:02d}:00"
                    code = int(codes[i]) if i < len(codes) else 0
                    hourly_list.append(HourlyForecastItem(
                        time=t_str,
                        temperature=float(temps[i]) if i < len(temps) else 25.0,
                        apparent_temperature=float(app_temps[i]) if i < len(app_temps) else 26.0,
                        precipitation_probability=int(pops[i]) if (i < len(pops) and pops[i] is not None) else 0,
                        precipitation=float(precips[i]) if (i < len(precips) and precips[i] is not None) else 0.0,
                        weather_code=code,
                        condition=get_weather_condition(code),
                        wind_speed=float(winds[i]) if i < len(winds) else 10.0,
                        uv_index=float(uvs[i]) if (i < len(uvs) and uvs[i] is not None) else 0.0
                    ))

                # Parse 7-day daily forecast
                daily_list = []
                d_data = data.get("daily", {})
                d_dates = d_data.get("time", [])[:7]
                d_codes = d_data.get("weather_code", [])
                d_max_temps = d_data.get("temperature_2m_max", [])
                d_min_temps = d_data.get("temperature_2m_min", [])
                d_precip_sums = d_data.get("precipitation_sum", [])
                d_pop_maxs = d_data.get("precipitation_probability_max", [])
                d_uv_maxs = d_data.get("uv_index_max", [])
                d_sunrises = d_data.get("sunrise", [])
                d_sunsets = d_data.get("sunset", [])

                for idx in range(len(d_dates)):
                    date_val = d_dates[idx]
                    try:
                        date_obj = datetime.strptime(date_val, "%Y-%m-%d")
                        if idx == 0:
                            display_date = "Today"
                        elif idx == 1:
                            display_date = "Tomorrow"
                        else:
                            display_date = date_obj.strftime("%a, %b %d")
                    except Exception:
                        display_date = date_val

                    code = int(d_codes[idx]) if idx < len(d_codes) else 0
                    daily_list.append(DailyForecastItem(
                        date=display_date,
                        temperature_max=float(d_max_temps[idx]) if idx < len(d_max_temps) else 30.0,
                        temperature_min=float(d_min_temps[idx]) if idx < len(d_min_temps) else 22.0,
                        precipitation_probability_max=int(d_pop_maxs[idx]) if (idx < len(d_pop_maxs) and d_pop_maxs[idx] is not None) else 0,
                        precipitation_sum=float(d_precip_sums[idx]) if (idx < len(d_precip_sums) and d_precip_sums[idx] is not None) else 0.0,
                        weather_code=code,
                        condition=get_weather_condition(code),
                        uv_index_max=float(d_uv_maxs[idx]) if (idx < len(d_uv_maxs) and d_uv_maxs[idx] is not None) else 5.0,
                        sunrise=d_sunrises[idx].split("T")[-1][:5] if idx < len(d_sunrises) else "06:00",
                        sunset=d_sunsets[idx].split("T")[-1][:5] if idx < len(d_sunsets) else "18:30"
                    ))

                return WeatherForecastResponse(
                    location=location_obj,
                    current=current_obj,
                    hourly=hourly_list,
                    daily=daily_list,
                    is_fallback=False
                )

        except httpx.TimeoutException:
            logger.warning("Open-Meteo API connection timed out. Falling back to demo data.")
            return cls.get_fallback_data(location_obj)
        except Exception as e:
            logger.warning(f"Error fetching live forecast: {e}. Falling back to demo data.")
            return cls.get_fallback_data(location_obj)

    @classmethod
    async def get_weather_for_date_range(
        cls,
        latitude: float,
        longitude: float,
        start_date: str, # YYYY-MM-DD
        end_date: Optional[str] = None, # YYYY-MM-DD
        timezone: str = "Asia/Kolkata",
        location_name: str = "Selected Location"
    ) -> Dict[str, Any]:
        """
        Fetches exact Open-Meteo weather data (historical or forecast) for explicit date or date range.
        Enforces strict date matching & composite caching key.
        """
        if not end_date:
            end_date = start_date

        cache_key = f"{round(latitude,3)}_{round(longitude,3)}|{start_date}|{end_date}|{timezone}"
        now_time = datetime.now()
        if cache_key in _WEATHER_CACHE:
            ts, cached_data = _WEATHER_CACHE[cache_key]
            if (now_time - ts).total_seconds() < CACHE_TTL_SECONDS:
                logger.info(f"Returning cached Open-Meteo date range data for {cache_key}")
                return cached_data

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "precipitation_probability", "precipitation", "weather_code",
                "wind_speed_10m", "uv_index"
            ],
            "daily": [
                "weather_code", "temperature_2m_max", "temperature_2m_min",
                "precipitation_sum", "precipitation_probability_max",
                "uv_index_max", "wind_speed_10m_max", "sunrise", "sunset"
            ],
            "timezone": timezone
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    logger.warning(f"Open-Meteo API status {response.status_code} for {start_date} to {end_date}.")
                    return {"error": f"Open-Meteo returned status {response.status_code}", "is_available": False}

                data = response.json()
                
                d_data = data.get("daily", {})
                d_dates = d_data.get("time", [])

                # VALIDATION: Check that returned dates match requested start_date
                if not d_dates or start_date not in d_dates:
                    logger.warning(f"Returned dates {d_dates} do not contain requested start_date {start_date}")
                    return {"error": "Weather data unavailable for requested date", "is_available": False}

                # Extract daily metrics
                daily_items = []
                for idx, dt_str in enumerate(d_dates):
                    code = int(d_data["weather_code"][idx]) if "weather_code" in d_data and idx < len(d_data["weather_code"]) else 0
                    daily_items.append({
                        "date": dt_str,
                        "temperature_max": float(d_data["temperature_2m_max"][idx]) if "temperature_2m_max" in d_data else 30.0,
                        "temperature_min": float(d_data["temperature_2m_min"][idx]) if "temperature_2m_min" in d_data else 22.0,
                        "precipitation_sum": float(d_data["precipitation_sum"][idx]) if "precipitation_sum" in d_data else 0.0,
                        "precipitation_probability_max": int(d_data["precipitation_probability_max"][idx]) if ("precipitation_probability_max" in d_data and d_data["precipitation_probability_max"][idx] is not None) else 0,
                        "weather_code": code,
                        "condition": get_weather_condition(code),
                        "uv_index_max": float(d_data["uv_index_max"][idx]) if ("uv_index_max" in d_data and d_data["uv_index_max"][idx] is not None) else 5.0,
                        "wind_speed_max": float(d_data["wind_speed_10m_max"][idx]) if ("wind_speed_10m_max" in d_data and d_data["wind_speed_10m_max"][idx] is not None) else 10.0,
                    })

                # Extract hourly metrics
                hourly_items = []
                h_data = data.get("hourly", {})
                h_times = h_data.get("time", [])
                h_temps = h_data.get("temperature_2m", [])
                h_app_temps = h_data.get("apparent_temperature", [])
                h_pops = h_data.get("precipitation_probability", [])
                h_precips = h_data.get("precipitation", [])
                h_humids = h_data.get("relative_humidity_2m", [])
                h_winds = h_data.get("wind_speed_10m", [])
                h_codes = h_data.get("weather_code", [])

                for i in range(len(h_times)):
                    dt_full = h_times[i] # YYYY-MM-DDTHH:MM
                    time_only = dt_full.split("T")[-1][:5] if "T" in dt_full else f"{i:02d}:00"
                    hour_num = int(time_only.split(":")[0])
                    code = int(h_codes[i]) if i < len(h_codes) else 0

                    hourly_items.append({
                        "datetime": dt_full,
                        "time": time_only,
                        "hour": hour_num,
                        "temperature": float(h_temps[i]) if i < len(h_temps) else 25.0,
                        "apparent_temperature": float(h_app_temps[i]) if i < len(h_app_temps) else 26.0,
                        "precipitation_probability": int(h_pops[i]) if (i < len(h_pops) and h_pops[i] is not None) else 0,
                        "precipitation": float(h_precips[i]) if (i < len(h_precips) and h_precips[i] is not None) else 0.0,
                        "humidity": int(h_humids[i]) if (i < len(h_humids) and h_humids[i] is not None) else 60,
                        "wind_speed": float(h_winds[i]) if i < len(h_winds) else 10.0,
                        "condition": get_weather_condition(code)
                    })

                result = {
                    "location_name": location_name,
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_available": True,
                    "daily": daily_items,
                    "hourly": hourly_items
                }

                _WEATHER_CACHE[cache_key] = (now_time, result)
                return result

        except Exception as e:
            logger.error(f"Failed to fetch date range weather: {e}")
            return {"error": str(e), "is_available": False}
