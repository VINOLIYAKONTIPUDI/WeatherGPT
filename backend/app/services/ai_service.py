import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.models.schemas import ChatRequest, ChatResponse, WeatherForecastResponse, LocationCoordinates, AdvisoryItem
from app.services.weather_service import WeatherService
from app.services.geocoding_service import GeocodingService
from app.services.advisory_service import AdvisoryService

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def extract_location_from_text(text: str) -> Optional[str]:
        text_lower = text.lower()
        
        # Check standard Indian city names directly in text
        cities = ["Hyderabad", "Vijayawada", "Delhi", "Mumbai", "Bengaluru", "Bangalore", "Tadepalligudem", "Chennai", "Kolkata", "Visakhapatnam", "Vizag", "Pune", "Jaipur", "Ahmedabad", "Lucknow"]
        for c in cities:
            if c.lower() in text_lower:
                return "Bengaluru" if c.lower() == "bangalore" else ("Visakhapatnam" if c.lower() == "vizag" else c)
        
        # Pattern match "in <City>", "at <City>", "for <City>"
        in_match = re.search(r'\b(?:in|at|for|near|of)\s+([a-zA-Z\s]+?)(?:\s+today|\s+tomorrow|\s+this|\s+now|\?|\.|$)', text, re.IGNORECASE)
        if in_match:
            candidate = in_match.group(1).strip()
            ignored = ["the", "my area", "here", "college", "work", "office", "home", "india", "my location"]
            if candidate and candidate.lower() not in ignored:
                return candidate.title()
                
        return None

    @staticmethod
    def detect_intent(text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["umbrella", "raincoat", "rain coat", "need rain", "గొడుగు", "రెయిన్‌కోట్", "छाता"]):
            return "umbrella"
        if any(w in t for w in ["rain", "raining", "rainfall", "drizzle", "shower", "వర్షం", "వర్షపాతం", "बारिश", "बरसात"]):
            return "precipitation"
        if any(w in t for w in ["compare", "difference", "versus", "vs", "పోల్చండి", "తారతమ్యం", "तुलना"]):
            return "comparison"
        if any(w in t for w in ["hot", "cold", "temperature", "degree", "heat", "లేదా", "వేడి", "ఉష్ణోగ్రత", "गर्मी", "तापमान", "ठंड"]):
            return "temperature"
        if any(w in t for w in ["humidity", "humid", "moisture", "తేమ", "నమస్కారం", "नमी"]):
            return "humidity"
        if any(w in t for w in ["wind", "storm", "blow", "breeze", "గాలి", "హవా", "हवा", "आंधी"]):
            return "wind"
        if any(w in t for w in ["uv", "sun", "sunscreen", "ultraviolet", "ఎండ", "धूप"]):
            return "uv_index"
        if any(w in t for w in ["thunder", "lightning", "storm", "ఉరుములు", "మెరుపులు", "तूफान", "बिजली"]):
            return "thunderstorm"
        if any(w in t for w in ["college", "school", "travel", "drive", "trip", "going to", "outside", "safe to", "పయనం", "ప్రయాణం", "यात्रा"]):
            return "travel_advisory"
        if any(w in t for w in ["run", "jog", "walk", "outdoor", "picnic", "cricket", "match", "వాకింగ్", "ఆరుబయట", "सैर"]):
            return "outdoor_activity"
        if any(w in t for w in ["tomorrow", "weekend", "next week", "day after", "రేపు", "కల్", "कल"]):
            return "forecast"
        return "current_weather"

    @classmethod
    async def process_chat(cls, request: ChatRequest) -> ChatResponse:
        user_msg = request.message.strip()
        lang = request.language or "en-IN"

        # 1. Session context & location resolution
        extracted_city = cls.extract_location_from_text(user_msg)
        
        target_location: LocationCoordinates
        if extracted_city:
            search_results = await GeocodingService.search_location(extracted_city)
            if search_results:
                best = search_results[0]
                target_location = LocationCoordinates(
                    latitude=best.latitude,
                    longitude=best.longitude,
                    name=best.name,
                    country=best.country,
                    admin1=best.admin1
                )
            else:
                target_location = request.location or LocationCoordinates(latitude=17.3850, longitude=78.4867, name=extracted_city, country="India", admin1="")
        elif request.location and request.location.latitude != 0:
            target_location = request.location
        else:
            target_location = LocationCoordinates(latitude=17.3850, longitude=78.4867, name="Hyderabad", country="India", admin1="Telangana")

        # 2. Get Live Weather Data for target location
        weather_data = await WeatherService.get_forecast(
            latitude=target_location.latitude,
            longitude=target_location.longitude,
            location_name=target_location.name or "Selected Location"
        )

        # 3. Advisories
        advisories = AdvisoryService.generate_advisories(weather_data)
        top_advisory = advisories[0] if advisories else None

        # 4. Intent detection
        intent = cls.detect_intent(user_msg)

        # 5. Extract weather parameters
        cur = weather_data.current
        hourly = weather_data.hourly
        daily = weather_data.daily
        loc_name = weather_data.location.name or "your location"
        
        today = daily[0] if len(daily) > 0 else None
        tomorrow = daily[1] if len(daily) > 1 else daily[0]
        
        # Calculate afternoon & night telemetry
        afternoon_temps = [h.temperature for h in hourly[12:17]] if len(hourly) >= 17 else [cur.temperature]
        afternoon_max = max(afternoon_temps, default=cur.temperature)
        
        night_thunders = any(h.weather_code in [95, 96, 99] for h in hourly[18:24]) if len(hourly) >= 24 else False
        max_pop_24h = max([h.precipitation_probability for h in hourly[:24]], default=cur.rain_probability)

        answer = ""
        suggested_followups: List[str] = []

        if lang == "te-IN":
            # Telugu Response Generation
            if intent in ["umbrella", "precipitation"]:
                pop = max(tomorrow.precipitation_probability_max, max_pop_24h)
                if pop >= 50:
                    answer = f"అవును, {loc_name}లో {pop}% వర్షం పడే అవకాశం ఉంది. ఖచ్చితంగా గొడుగు లేదా రెయిన్‌కోట్ తీసుకెళ్లడం మంచిది."
                else:
                    answer = f"నేడు/రేపు {loc_name}లో వర్షం పడే అవకాశం తక్కువ ({pop}%). గొడుగు అవసరం లేదు."
            elif intent == "travel_advisory":
                if tomorrow.precipitation_probability_max >= 70 or tomorrow.temperature_max >= 40:
                    answer = f"{loc_name}కు ప్రయాణం చేసేటప్పుడు జాగ్రత్త వహించండి. వర్ష సూచన {tomorrow.precipitation_probability_max}% మరియు గరిష్ట ఉష్ణోగ్రత {tomorrow.temperature_max}°C."
                else:
                    answer = f"{loc_name}లో రేపటి ఉష్ణోగ్రత {tomorrow.temperature_max}°C గా ఉంటుంది. ప్రయాణం చేయడానికి వాతావరణం చాలా అనుకూలంగా ఉంది."
            elif intent == "temperature":
                answer = f"{loc_name}లో ప్రస్తుత ఉష్ణోగ్రత {cur.temperature}°C (అనుభూతి {cur.apparent_temperature}°C). నేటి గరిష్ట ఉష్ణోగ్రత {afternoon_max}°C వరకు ఉంటుంది."
            elif intent == "humidity":
                answer = f"{loc_name}లో ప్రస్తుత గాలి తేమ శాతం {cur.relative_humidity}%."
            elif intent == "wind":
                answer = f"{loc_name}లో గాలి వేగం ప్రస్తుతం గంటకు {cur.wind_speed} కిలోమీటర్లు."
            elif intent == "uv_index":
                answer = f"{loc_name}లో యూవీ ఇండెక్స్ {cur.uv_index}. మధ్యాహ్నం 11 నుండి 3 గంటల మధ్య ఎండలో జాగ్రత్తగా ఉండండి."
            elif intent == "comparison":
                answer = f"{loc_name}లో నేటి గరిష్ట ఉష్ణోగ్రత {today.temperature_max if today else cur.temperature}°C, కానీ రేపు {tomorrow.temperature_max}°C ఉంటుంది."
            else:
                answer = f"{loc_name}లో ప్రస్తుతం వాతావరణం {cur.condition}గా ఉంది. ఉష్ణోగ్రత {cur.temperature}°C, తేమ {cur.relative_humidity}% మరియు గాలి వేగం {cur.wind_speed} కి.మీ/గం."
            
            suggested_followups = [
                "రేపు వర్షం పడుతుందా?",
                "గొడుగు అవసరమా?",
                "ఉష్ణోగ్రత ఎంత ఉంటుంది?"
            ]

        elif lang == "hi-IN":
            # Hindi Response Generation
            if intent in ["umbrella", "precipitation"]:
                pop = max(tomorrow.precipitation_probability_max, max_pop_24h)
                if pop >= 50:
                    answer = f"हां, {loc_name} में बारिश की {pop}% संभावना है। छाता या रेनकोट साथ रखना बेहतर रहेगा।"
                else:
                    answer = f"{loc_name} में बारिश की संभावना केवल {pop}% है। छाते की आवश्यकता नहीं है।"
            elif intent == "travel_advisory":
                if tomorrow.precipitation_probability_max >= 70 or tomorrow.temperature_max >= 40:
                    answer = f"{loc_name} की यात्रा में सावधानी बरतें। भारी बारिश की संभावना ({tomorrow.precipitation_probability_max}%) और तापमान {tomorrow.temperature_max}°C रहेगा।"
                else:
                    answer = f"{loc_name} में कल का तापमान {tomorrow.temperature_max}°C रहेगा। यात्रा के लिए मौसम सामान्य और अनुकूल है।"
            elif intent == "temperature":
                answer = f"{loc_name} में अभी तापमान {cur.temperature}°C (महसूस {cur.apparent_temperature}°C) है। दोपहर में {afternoon_max}°C तक पहुंच सकता है।"
            elif intent == "humidity":
                answer = f"{loc_name} में वर्तमान नमी (Humidity) {cur.relative_humidity}% है।"
            elif intent == "wind":
                answer = f"{loc_name} में हवा की गति {cur.wind_speed} किमी/घंटा है।"
            elif intent == "uv_index":
                answer = f"{loc_name} में यूवी इंडेक्स {cur.uv_index} है। दोपहर में धूप से बचाव रखें।"
            elif intent == "comparison":
                answer = f"{loc_name} में आज का अधिकतम तापमान {today.temperature_max if today else cur.temperature}°C है, जबकि कल {tomorrow.temperature_max}°C रहने का अनुमान है।"
            else:
                answer = f"{loc_name} में वर्तमान में {cur.condition} मौसम है। तापमान {cur.temperature}°C, आर्द्रता {cur.relative_humidity}% और हवा {cur.wind_speed} किमी/घंटा है।"

            suggested_followups = [
                "क्या कल बारिश होगी?",
                "क्या छाता चाहिए?",
                "आज का तापमान कितना है?"
            ]

        else:
            # English Response Generation
            if intent in ["umbrella", "precipitation"]:
                pop_val = max(tomorrow.precipitation_probability_max, max_pop_24h)
                precip_val = max(tomorrow.precipitation_sum, cur.precipitation)
                if pop_val >= 50:
                    answer = f"Yes, I'd recommend carrying an umbrella or raincoat in {loc_name}. There is a {pop_val}% chance of rain with around {precip_val:.1f} mm expected precipitation."
                else:
                    answer = f"No umbrella needed for {loc_name} right now. Rain probability is low at only {pop_val}% with {cur.condition.lower()} conditions."
            
            elif intent == "travel_advisory":
                if tomorrow.precipitation_probability_max >= 70 or tomorrow.temperature_max >= 40:
                    answer = f"Travel advisory for {loc_name}: Exercise caution. High rain probability ({tomorrow.precipitation_probability_max}%) and temperature peaking at {tomorrow.temperature_max}°C."
                else:
                    answer = f"Yes, it's generally safe to travel in {loc_name}! Expect pleasant weather with a high of {tomorrow.temperature_max}°C and moderate wind speed of {cur.wind_speed} km/h."

            elif intent == "temperature":
                if "afternoon" in user_msg.lower():
                    answer = f"In {loc_name}, afternoon temperatures will peak around {afternoon_max:.1f}°C (feels like {afternoon_max + 2:.1f}°C)."
                else:
                    answer = f"Current temperature in {loc_name} is {cur.temperature:.1f}°C (feels like {cur.apparent_temperature:.1f}°C). Tomorrow's maximum high will reach {tomorrow.temperature_max:.1f}°C."

            elif intent == "humidity":
                answer = f"Relative humidity in {loc_name} is currently {cur.relative_humidity}% with a dew point suited for comfortable transpiration."

            elif intent == "wind":
                answer = f"Wind speed in {loc_name} is currently {cur.wind_speed:.1f} km/h blowing from {cur.wind_direction}°."

            elif intent == "uv_index":
                answer = f"The UV index in {loc_name} is currently {cur.uv_index:.1f} (Peak daily UV: {tomorrow.uv_index_max:.1f}). Consider sunscreen if outdoors between 11 AM and 3 PM."

            elif intent == "thunderstorm":
                if night_thunders or cur.weather_code in [95, 96, 99]:
                    answer = f"Warning: Thunderstorm activity is expected in {loc_name}. Stay indoors and avoid open fields."
                else:
                    answer = f"No immediate thunderstorm threat for {loc_name}. Thunderstorm probability is low."

            elif intent == "outdoor_activity":
                if cur.rain_probability > 60 or cur.temperature > 38:
                    answer = f"Outdoor activity notice for {loc_name}: Outdoor plans may be affected by elevated rain chance ({cur.rain_probability}%) or high heat ({cur.temperature}°C)."
                else:
                    answer = f"Conditions in {loc_name} are great for outdoor activities, runs, or walks! Temperature is {cur.temperature:.1f}°C with light breeze."

            elif intent == "comparison":
                t_today = today.temperature_max if today else cur.temperature
                answer = f"In {loc_name}, today's maximum temperature is {t_today:.1f}°C compared to tomorrow's expected high of {tomorrow.temperature_max:.1f}°C with a {tomorrow.precipitation_probability_max}% chance of rain."

            else:
                answer = f"Weather in {loc_name} is currently {cur.condition.lower()} at {cur.temperature:.1f}°C (feels like {cur.apparent_temperature:.1f}°C). Humidity is {cur.relative_humidity}% with {cur.wind_speed} km/h wind."

            suggested_followups = [
                "Will it rain today?",
                "Do I need an umbrella?",
                "How hot will tomorrow be?",
                "Is it safe to travel?"
            ]

        weather_summary = {
            "temperature": cur.temperature,
            "apparent_temperature": cur.apparent_temperature,
            "condition": cur.condition,
            "humidity": cur.relative_humidity,
            "wind_speed": cur.wind_speed,
            "rain_probability": max_pop_24h,
            "uv_index": cur.uv_index
        }

        return ChatResponse(
            answer=answer,
            language=lang,
            intent=intent,
            location=weather_data.location,
            weather=weather_summary,
            advisory=top_advisory,
            suggested_followups=suggested_followups,
            is_fallback=weather_data.is_fallback
        )
