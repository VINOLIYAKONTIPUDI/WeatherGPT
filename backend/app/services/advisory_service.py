from typing import List
from app.models.schemas import WeatherForecastResponse, AdvisoryItem, AlertsResponse, SmartAlertData

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
    def calculate_smart_alert(cls, weather_data: WeatherForecastResponse) -> SmartAlertData:
        cur = weather_data.current
        hourly = weather_data.hourly
        loc_name = weather_data.location.name or weather_data.location.city or "your area"

        hazards = []
        risk_score = 10  # Base pleasant weather baseline

        # 1. Rain & Flood Assessment
        max_precip = max([h.precipitation for h in hourly[:24]], default=cur.precipitation)
        max_pop = max([h.precipitation_probability for h in hourly[:24]], default=cur.rain_probability)

        if max_precip >= 25.0 or cur.precipitation >= 25.0:
            risk_score += 45
            hazards.append("Flood Risk & Torrential Downpour")
        elif max_precip >= 10.0 or cur.precipitation >= 10.0:
            risk_score += 30
            hazards.append("Heavy Rainfall")
        elif max_pop >= 70 or cur.rain_probability >= 70:
            risk_score += 20
            hazards.append("High Precipitation Probability")

        # 2. Thunderstorm & Hail Assessment
        has_hail = any(h.weather_code in [96, 99] for h in hourly[:24]) or cur.weather_code in [96, 99]
        has_storm = any(h.weather_code == 95 for h in hourly[:24]) or cur.weather_code == 95

        if has_hail:
            risk_score += 40
            hazards.append("Severe Thunderstorm with Hail")
        elif has_storm:
            risk_score += 25
            hazards.append("Lightning & Thunderstorm Activity")

        # 3. Extreme Temperature Assessment
        max_temp = max([h.temperature for h in hourly[:24]], default=cur.temperature)
        min_temp = min([h.temperature for h in hourly[:24]], default=cur.temperature)

        if max_temp >= 42.0 or cur.temperature >= 42.0:
            risk_score += 35
            hazards.append("Extreme Heatwave (>42°C)")
        elif max_temp >= 38.0 or cur.temperature >= 38.0:
            risk_score += 20
            hazards.append("High Temperature Stress (>38°C)")
        elif min_temp <= 4.0 or cur.temperature <= 4.0:
            risk_score += 30
            hazards.append("Freezing Temperature / Frost Risk")

        # 4. Wind Hazard Assessment
        max_wind = max([h.wind_speed for h in hourly[:24]], default=cur.wind_speed)
        if max_wind >= 45.0 or cur.wind_speed >= 45.0:
            risk_score += 35
            hazards.append("Dangerous Storm Wind Gusts (>45 km/h)")
        elif max_wind >= 30.0 or cur.wind_speed >= 30.0:
            risk_score += 15
            hazards.append("Strong Wind Gusts")

        # Cap score between 0 and 100
        risk_score = max(0, min(100, risk_score))

        # Determine Risk Level Category
        if risk_score >= 76:
            risk_level = "Severe Risk"
        elif risk_score >= 51:
            risk_level = "High Risk"
        elif risk_score >= 26:
            risk_level = "Advisory"
        else:
            risk_level = "Normal"

        # Formulate Descriptions & Recommendations based on actual data
        if hazards:
            event_desc = f"Active hazards detected in {loc_name}: {', '.join(hazards)}. Peak temp: {max_temp:.1f}°C, Max rain chance: {max_pop}%, Max wind: {max_wind:.1f} km/h."
        else:
            event_desc = f"Weather conditions in {loc_name} are mild and normal. Current temperature is {cur.temperature:.1f}°C with {cur.condition.lower()} skies."

        # Actionable Safety Advice
        if risk_level == "Severe Risk":
            safety_advice = "🔴 CRITICAL SAFETY STEP: Stay indoors immediately. Move to structurally secure shelter away from trees, glass windows, and low-lying flood channels. Keep mobile devices charged."
            travel_warning = "🔴 SEVERE TRAVEL HAZARD: Do NOT travel! Highways and urban roads present severe flooding, lightning, and fallen tree hazards."
        elif risk_level == "High Risk":
            safety_advice = "🟠 HIGH SAFETY CAUTION: Avoid unnecessary outdoor exposure. Carry emergency rain gear, stay hydrated, and secure outdoor property."
            travel_warning = "🟠 TRAVEL WARNING: Exercise extreme caution on roads due to slippery conditions, waterlogging, or reduced visibility."
        elif risk_level == "Advisory":
            safety_advice = "🟡 ADVISORY: Carry an umbrella or sunscreen. Keep updated with live WeatherGPT hourly forecasts."
            travel_warning = "🟡 TRAVEL ADVISORY: Allow extra commute time for potential light rain or afternoon sun."
        else:
            safety_advice = "🟢 SAFE CONDITIONS: No active weather hazards. Standard daily routines and outdoor activities are safe."
            travel_warning = "🟢 TRAVEL SAFE: Road and flight travel conditions are clear and favorable."

        return SmartAlertData(
            risk_score=risk_score,
            risk_level=risk_level,
            event_description=event_desc,
            safety_advice=safety_advice,
            travel_warning=travel_warning,
            detected_hazards=hazards
        )

    @classmethod
    def get_alerts_response(cls, weather_data: WeatherForecastResponse) -> AlertsResponse:
        advisories = cls.generate_advisories(weather_data)
        smart_alert = cls.calculate_smart_alert(weather_data)
        return AlertsResponse(
            location=weather_data.location,
            alerts=advisories,
            count=len(advisories),
            smart_alert=smart_alert
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

        # 1. Irrigation Advice (Short & Simple)
        if rain_prob >= 50 or rainfall >= 2.0:
            irrigation = f"Do not water today. Rain is expected ({rain_prob:.0f}% rain chance)."
        elif temp >= 35.0 and humidity < 50:
            irrigation = f"Water crops in early morning or evening to protect against heat ({temp:.1f}°C)."
        else:
            irrigation = f"Provide normal watering suitable for {crop} in {stage} stage."

        # 2. Fertilizer Advice (Short & Simple)
        if rain_prob >= 50 or rainfall >= 2.0:
            fertilizer = f"Delay fertilizer today. Rain ({rain_prob:.0f}% chance) will wash away nutrients."
        elif wind_speed >= 20.0:
            fertilizer = f"Wait for calm wind before applying fertilizer (current wind: {wind_speed:.1f} km/h)."
        else:
            fertilizer = f"Good clear weather to apply soil fertilizer for {crop}."

        # 3. Spraying Advice (Short & Simple)
        if rain_prob >= 50 or rainfall >= 2.0:
            spraying = f"Do not spray today. Incoming rain ({rain_prob:.0f}% chance) will wash away chemicals."
        elif wind_speed >= 15.0:
            spraying = f"Postpone spraying due to strong wind drift ({wind_speed:.1f} km/h)."
        else:
            spraying = f"Safe weather window for pesticide and fungicide spraying."

        # 4. Pest & Disease Risk (Short & Simple)
        disease_risks = {
            "Paddy": "Blast / Sheath Blight",
            "Cotton": "Bollworm / Leaf Curl",
            "Maize": "Armyworm / Leaf Blight",
            "Groundnut": "Tikka Leaf Spot",
            "Wheat": "Rust / Blight",
        }
        target_disease = disease_risks.get(crop, "Fungal & Pest Attack")

        if humidity >= 75 and 20.0 <= temp <= 33.0:
            pest_disease = f"High risk of {target_disease} due to high humidity ({humidity:.0f}%). Inspect fields."
        else:
            pest_disease = f"Low disease risk for {crop} today under current weather."

        # 5. Harvesting Advice (Short & Simple)
        if stage.lower() == "harvest":
            if rain_prob >= 40 or rainfall >= 1.0:
                harvesting = f"Pause harvesting and store produce in dry shelter (rain chance: {rain_prob:.0f}%)."
            else:
                harvesting = f"Ideal clear weather for harvesting and sun-drying {crop}."
        else:
            harvesting = f"Maintain clean field drainage for {crop} during the {stage} stage."

        # Practical Overall Summary
        if rain_prob >= 60 or rainfall >= 5.0 or wind_speed >= 25.0:
            overall_risk = "High"
            summary = f"Rain/wind alert for {crop} ({stage} stage). Hold spraying and irrigation today."
        elif rain_prob >= 35 or wind_speed >= 15.0 or humidity >= 70:
            overall_risk = "Moderate"
            summary = f"Moderate weather for {crop}. Check watering and spraying tips below."
        else:
            overall_risk = "Low"
            summary = f"Clear & favorable weather today for {crop} in {stage} stage."

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
            "disclaimer": "Advice based on live local weather data and standard agronomic guidelines.",
        }

