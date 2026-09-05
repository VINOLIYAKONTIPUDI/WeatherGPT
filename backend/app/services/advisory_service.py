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
        return AlertsResponse(
            location=weather_data.location,
            alerts=advisories,
            count=len(advisories)
        )

    @classmethod
    def generate_crop_advisory(
        cls,
        crop: str = "Paddy",
        stage: str = "Vegetative",
        weather_data: dict | None = None
    ) -> dict:
        cur = {}
        if weather_data and isinstance(weather_data, dict):
            cur = weather_data.get("current") or weather_data

        temp = float(cur.get("temperature", 28.0))
        humidity = float(cur.get("humidity", 65.0))
        rain_prob = float(cur.get("rain_probability", cur.get("pop", 20.0)))
        rainfall = float(cur.get("precipitation", 0.0))
        wind_speed = float(cur.get("wind_speed", 10.0))

        # 1. Irrigation Advice
        if rain_prob >= 50 or rainfall >= 5.0:
            irrigation = f"Avoid irrigation today. Adequate moisture expected from incoming rainfall ({rain_prob:.0f}% rain chance)."
        elif temp >= 35.0 and humidity < 50:
            irrigation = f"Provide light, frequent irrigation during early morning or late evening to relieve heat stress ({temp:.1f}°C)."
        else:
            irrigation = f"Provide normal scheduled irrigation suitable for the {stage} stage of {crop}."

        # 2. Fertilizer Advice
        if rain_prob >= 60 or rainfall >= 5.0:
            fertilizer = f"Postpone fertilizer application. High risk of rain-induced nutrient leaching and surface runoff ({rain_prob:.0f}% rain chance)."
        elif wind_speed >= 20.0:
            fertilizer = f"Delay top-dressing fertilizer due to strong gusty winds ({wind_speed:.1f} km/h)."
        else:
            fertilizer = f"Favorable calm window for soil fertilizer and nutrient top-dressing application."

        # 3. Spraying Advice
        if wind_speed >= 15.0:
            spraying = f"Avoid pesticide/fungicide spraying due to chemical drift risk (wind speed {wind_speed:.1f} km/h exceeds 15 km/h threshold)."
        elif rain_prob >= 50 or rainfall >= 2.0:
            spraying = f"Postpone crop spraying. Expected rain ({rain_prob:.0f}% chance) will wash away applied chemicals."
        else:
            spraying = f"Favorable weather conditions for pesticide and fungicide application."

        # 4. Pest & Disease Risk
        disease_risks = {
            "Paddy": "Blast and Sheath Blight",
            "Cotton": "Boll Rot and Leaf Curl Virus",
            "Maize": "Fall Armyworm and Turcicum Leaf Blight",
            "Groundnut": "Tikka Leaf Spot and Rust",
            "Wheat": "Stripe Rust and Powdery Mildew",
        }
        target_disease = disease_risks.get(crop, "Fungal and Pest attack")

        if humidity >= 75 and 20.0 <= temp <= 33.0:
            pest_disease = f"HIGH Risk of {target_disease} due to high humidity ({humidity:.0f}%) and warm temperatures ({temp:.1f}°C). Monitor fields closely."
        else:
            pest_disease = f"Low to Moderate disease risk for {crop}. Maintain routine crop field surveillance."

        # 5. Harvesting Advice
        if stage.lower() == "harvest":
            if rain_prob >= 40 or rainfall >= 2.0:
                harvesting = f"Delay crop harvesting and threshing due to rain risk ({rain_prob:.0f}% chance). Store harvested produce in dry shelter."
            else:
                harvesting = f"Optimal clear weather window for harvesting, threshing, and sun-drying {crop}."
        else:
            harvesting = f"Crop is currently in {stage} stage. Ensure good field drainage and timely weed control."

        # Determine Overall Risk Level
        if rain_prob >= 70 or rainfall >= 10.0 or wind_speed >= 30.0 or (humidity >= 80 and temp >= 25.0):
            overall_risk = "High"
            summary = f"Severe weather factors present for {crop} ({stage} stage). Exercise caution with spraying, irrigation, and harvesting."
        elif rain_prob >= 40 or rainfall >= 3.0 or wind_speed >= 18.0 or humidity >= 70:
            overall_risk = "Moderate"
            summary = f"Moderate rain or wind conditions for {crop}. Follow targeted advisory recommendations below."
        else:
            overall_risk = "Low"
            summary = f"Favorable agricultural weather for {crop} during {stage} stage."

        return {
            "crop": crop,
            "stage": stage,
            "overall_risk": overall_risk,
            "summary": summary,
            "recommendations": {
                "irrigation": irrigation,
                "fertilizer": fertilizer,
                "spraying": spraying,
                "pest_disease_risk": pest_disease,
                "harvesting": harvesting,
            },
            "weather_factors": {
                "rain_probability": round(rain_prob, 1),
                "rainfall_mm": round(rainfall, 1),
                "temperature_c": round(temp, 1),
                "humidity_percent": round(humidity, 1),
                "wind_speed_kmh": round(wind_speed, 1),
            },
            "disclaimer": "Agricultural advice is calculated based on live meteorological data and general agronomic guidelines. Local field conditions may vary.",
        }

