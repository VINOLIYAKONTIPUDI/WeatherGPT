from typing import List
from app.models.schemas import WeatherForecastResponse, AdvisoryItem, AlertsResponse

class AdvisoryService:
    @classmethod
    def generate_advisories(cls, weather_data: WeatherForecastResponse) -> List[AdvisoryItem]:
        advisories: List[AdvisoryItem] = []
        cur = weather_data.current
        hourly = weather_data.hourly
        daily = weather_data.daily
        loc_name = weather_data.location.name or "your area"

        # 1. Check Rain / Heavy Rain (Current + Next 24 hours)
        max_pop_24h = max([h.precipitation_probability for h in hourly[:24]], default=cur.rain_probability)
        max_precip_24h = max([h.precipitation for h in hourly[:24]], default=cur.precipitation)
        
        # Check tomorrow's rain probability
        tomorrow_pop = daily[1].precipitation_probability_max if len(daily) > 1 else max_pop_24h

        if max_precip_24h >= 8.0 or cur.precipitation >= 8.0:
            advisories.append(AdvisoryItem(
                id="heavy-rain-alert",
                severity="danger",
                title="🔴 Heavy Rain Warning",
                description=f"Heavy rainfall expected in {loc_name} with up to {max_precip_24h:.1f} mm precipitation expected.",
                recommendation="Carry an umbrella/raincoat, allow extra travel time, and stay clear of waterlogged areas.",
                timeframe="Today / Tomorrow",
                icon="cloud-rain"
            ))
        elif max_pop_24h >= 60 or cur.rain_probability >= 60 or tomorrow_pop >= 60:
            advisories.append(AdvisoryItem(
                id="rain-advisory",
                severity="warning",
                title="🟠 Rain Advisory",
                description=f"High probability of rain ({max(max_pop_24h, tomorrow_pop)}% chance) in {loc_name}.",
                recommendation="Recommend carrying an umbrella or raincoat when heading outdoors, especially for college/work commute.",
                timeframe="Today & Tomorrow",
                icon="umbrella"
            ))

        # 2. Extreme Heat Advisory
        max_temp_24h = max([h.temperature for h in hourly[:24]], default=cur.temperature)
        if max_temp_24h >= 40.0 or cur.temperature >= 40.0:
            advisories.append(AdvisoryItem(
                id="heat-wave-alert",
                severity="danger",
                title="🔴 Extreme Heat Wave Advisory",
                description=f"Scorching temperatures reaching {max_temp_24h:.1f}°C (feels like {cur.apparent_temperature:.1f}°C).",
                recommendation="Stay indoors during peak afternoon hours (12 PM - 4 PM), drink plenty of water, and wear lightweight cotton clothing.",
                timeframe="Peak Afternoon",
                icon="sun"
            ))
        elif max_temp_24h >= 36.0 or cur.temperature >= 36.0:
            advisories.append(AdvisoryItem(
                id="hot-weather-advisory",
                severity="advisory",
                title="🟡 High Temperature Notice",
                description=f"Warm weather ahead with temperatures peaking at {max_temp_24h:.1f}°C.",
                recommendation="Keep a water bottle handy and wear sunscreen when stepping outside.",
                timeframe="Afternoon",
                icon="thermometer"
            ))

        # 3. High UV Advisory
        max_uv_24h = max([h.uv_index for h in hourly[:24]], default=cur.uv_index)
        if max_uv_24h >= 7.0:
            advisories.append(AdvisoryItem(
                id="uv-index-alert",
                severity="warning",
                title="🟠 High UV Radiation Warning",
                description=f"Very high UV Index expected ({max_uv_24h:.1f}). Sun exposure risks skin & eye strain.",
                recommendation="Avoid prolonged direct sunlight between 11 AM and 3 PM. Apply SPF 30+ sunscreen and wear sunglasses.",
                timeframe="11 AM – 3 PM",
                icon="sun-medium"
            ))

        # 4. Thunderstorm Warning
        has_thunderstorm = any(h.weather_code in [95, 96, 99] for h in hourly[:24]) or (cur.weather_code in [95, 96, 99])
        if has_thunderstorm:
            advisories.append(AdvisoryItem(
                id="thunderstorm-warning",
                severity="danger",
                title="🔴 Thunderstorm & Lightning Alert",
                description="Thunderstorms accompanied by lightning strikes expected in your area.",
                recommendation="Avoid open fields, tall trees, and metal structures. Stay indoors until storms pass.",
                timeframe="Evening / Night",
                icon="zap"
            ))

        # 5. Strong Wind Advisory
        max_wind_24h = max([h.wind_speed for h in hourly[:24]], default=cur.wind_speed)
        if max_wind_24h >= 35.0:
            advisories.append(AdvisoryItem(
                id="strong-wind-advisory",
                severity="advisory",
                title="🟡 Strong Gusty Winds",
                description=f"Wind speeds expected to reach {max_wind_24h:.1f} km/h.",
                recommendation="Secure loose outdoor items and exercise caution while driving two-wheelers.",
                timeframe="Today",
                icon="wind"
            ))

        # 6. Fallback Safe Weather Notification
        if not advisories:
            advisories.append(AdvisoryItem(
                id="pleasant-weather-info",
                severity="safe",
                title="🟢 Pleasant Weather Conditions",
                description=f"Weather in {loc_name} is currently {cur.condition.lower()} with comfortable temperature ({cur.temperature:.1f}°C).",
                recommendation="Great day for outdoor activities, morning walks, and travel!",
                timeframe="All Day",
                icon="smile"
            ))

        return advisories

    @classmethod
    def get_alerts_response(cls, weather_data: WeatherForecastResponse) -> AlertsResponse:
        advisories = cls.generate_advisories(weather_data)
        has_critical = any(a.severity == "danger" for a in advisories)
        return AlertsResponse(
            location=weather_data.location,
            alerts=advisories,
            count=len(advisories),
            has_critical_hazard=has_critical
        )
