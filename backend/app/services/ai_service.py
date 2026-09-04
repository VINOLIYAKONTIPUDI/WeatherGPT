import re
import logging
from typing import Dict, Any, List, Optional
from app.models.schemas import ChatRequest, ChatResponse, WeatherForecastResponse, LocationCoordinates, AdvisoryItem
from app.services.weather_service import WeatherService
from app.services.geocoding_service import GeocodingService
from app.services.advisory_service import AdvisoryService

logger = logging.getLogger(__name__)

# Multilingual keyword mappings & translations
INTENTS = [
    "current_weather", "forecast", "precipitation", "umbrella", "temperature",
    "humidity", "wind", "uv_index", "thunderstorm", "travel_advisory",
    "outdoor_activity", "comparison", "location_weather"
]

class AIService:
    @staticmethod
    def extract_location_from_text(text: str) -> Optional[str]:
        text_lower = text.lower()
        # Common city patterns
        in_match = re.search(r'\b(?:in|at|for|near|of)\s+([a-zA-Z\s]+?)(?:\s+today|\s+tomorrow|\s+this|\s+now|\?|\.|$)', text, re.IGNORECASE)
        if in_match:
            candidate = in_match.group(1).strip()
            if candidate and candidate.lower() not in ["the", "my area", "here", "college", "work"]:
                return candidate.title()
        
        # Check standard Indian city names directly in text
        cities = ["Hyderabad", "Vijayawada", "Delhi", "Mumbai", "Bengaluru", "Bangalore", "Tadepalligudem", "Chennai", "Kolkata", "Visakhapatnam", "Vizag", "Pune"]
        for c in cities:
            if c.lower() in text_lower:
                return c
        return None

    @staticmethod
    def detect_intent(text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["umbrella", "raincoat", "rain coat", "need rain"]):
            return "umbrella"
        if any(w in t for w in ["rain", "raining", "rainfall", "drizzle", "shower", "వర్షం", "వర్షపాతం", "గొడుగు", "बारिश", "छाता"]):
            return "precipitation"
        if any(w in t for w in ["hot", "cold", "temperature", "degree", "heat", "లేదా", "వేడి", "ఉష్ణోగ్రత", "गर्मी", "तापमान"]):
            return "temperature"
        if any(w in t for w in ["college", "school", "travel", "drive", "trip", "going to", "outside", "safe to", "పయనం", "ప్రయాణం", "यात्रा"]):
            return "travel_advisory"
        if any(w in t for w in ["uv", "sun", "sunscreen", "ultraviolet", "ఎండ"]):
            return "uv_index"
        if any(w in t for w in ["wind", "storm", "blow", "breeze", "గాలి"]):
            return "wind"
        if any(w in t for w in ["thunder", "lightning", "storm", "ఉరిములు"]):
            return "thunderstorm"
        if any(w in t for w in ["compare", "difference", "versus", "vs", "పోల్చండి"]):
            return "comparison"
        if any(w in t for w in ["tomorrow", "weekend", "next week", "day after", "రేపు", "కల్"]):
            return "forecast"
        return "current_weather"

    @classmethod
    async def process_chat(cls, request: ChatRequest) -> ChatResponse:
        user_msg = request.message.strip()
        lang = request.language or "en-IN"

        # 1. Session context resolution (Check if location was mentioned in previous turn or current msg)
        extracted_city = cls.extract_location_from_text(user_msg)
        
        # Resolve target location
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
                target_location = request.location or LocationCoordinates(latitude=17.3850, longitude=78.4867, name="Hyderabad", country="India", admin1="Telangana")
        elif request.location and request.location.latitude != 0:
            target_location = request.location
        else:
            # Default to Hyderabad if no location is available
            target_location = LocationCoordinates(latitude=17.3850, longitude=78.4867, name="Hyderabad", country="India", admin1="Telangana")

        # 2. Get Live Weather Data for resolved location
        weather_data = await WeatherService.get_forecast(
            latitude=target_location.latitude,
            longitude=target_location.longitude,
            location_name=target_location.name or "Selected Location"
        )

        # 3. Advisory Check
        advisories = AdvisoryService.generate_advisories(weather_data)
        top_advisory = advisories[0] if advisories else None

        # 4. Intent detection
        intent = cls.detect_intent(user_msg)

        # 5. Generate Grounded Response based on language & intent
        cur = weather_data.current
        loc_name = weather_data.location.name or "your location"
        tomorrow = weather_data.daily[1] if len(weather_data.daily) > 1 else weather_data.daily[0]
        max_pop_24h = max([h.precipitation_probability for h in weather_data.hourly[:24]], default=cur.rain_probability)

        answer = ""
        suggested_followups: List[str] = []

        if lang == "te-IN":
            # Telugu Response
            if intent in ["umbrella", "precipitation"]:
                if tomorrow.precipitation_probability_max >= 50 or cur.rain_probability >= 50:
                    answer = f"అవును, {loc_name}లో {tomorrow.precipitation_probability_max}% వర్షం పడే అవకాశం ఉంది. ఖచ్చితంగా గొడుగు లేదా రెయిన్‌కోట్ తీసుకెళ్లడం మంచిది."
                else:
                    answer = f"నేడు/రేపు {loc_name}లో వర్షం పడే అవకాశం తక్కువ ({tomorrow.precipitation_probability_max}%). గొడుగు అవసరం లేదు."
            elif intent == "travel_advisory":
                answer = f"{loc_name}లో రేపటి ఉష్ణోగ్రత {tomorrow.temperature_max}°C గా ఉంటుంది. వర్ష సూచన {tomorrow.precipitation_probability_max}%. ప్రయాణం చేయడానికి అనుకూలంగా ఉంటుంది."
            elif intent == "temperature":
                answer = f"{loc_name}లో ప్రస్తుత ఉష్ణోగ్రత {cur.temperature}°C (అనుభూతి {cur.apparent_temperature}°C). గరిష్ట ఉష్ణోగ్రత {tomorrow.temperature_max}°C వరకు ఉంటుంది."
            else:
                answer = f"{loc_name}లో ప్రస్తుతం వాతావరణం {cur.condition}గా ఉంది. ఉష్ణోగ్రత {cur.temperature}°C, తేమ {cur.relative_humidity}% మరియు గాలి వేగం {cur.wind_speed} కి.మీ/గం."
            
            suggested_followups = [
                "రేపు వర్షం పడుతుందా?",
                "గొడుగు అవసరమా?",
                "ఉష్ణోగ్రత ఎంత ఉంటుంది?"
            ]

        elif lang == "hi-IN":
            # Hindi Response
            if intent in ["umbrella", "precipitation"]:
                if tomorrow.precipitation_probability_max >= 50 or cur.rain_probability >= 50:
                    answer = f"हां, {loc_name} में बारिश की {tomorrow.precipitation_probability_max}% संभावना है। छाता या रेनकोट साथ रखना बेहतर रहेगा।"
                else:
                    answer = f"{loc_name} में बारिश की संभावना केवल {tomorrow.precipitation_probability_max}% है। छाते की आवश्यकता नहीं है।"
            elif intent == "travel_advisory":
                answer = f"{loc_name} में कल का तापमान {tomorrow.temperature_max}°C रहेगा। यात्रा के लिए मौसम सामान्य और अनुकूल है।"
            elif intent == "temperature":
                answer = f"{loc_name} में अभी तापमान {cur.temperature}°C (महसूस {cur.apparent_temperature}°C) है। आज अधिकतम {tomorrow.temperature_max}°C रहेगा।"
            else:
                answer = f"{loc_name} में वर्तमान में {cur.condition} मौसम है। तापमान {cur.temperature}°C, आर्द्रता {cur.relative_humidity}% और हवा {cur.wind_speed} किमी/घंटा है।"

            suggested_followups = [
                "क्या कल बारिश होगी?",
                "क्या छाता चाहिए?",
                "आज का तापमान कितना है?"
            ]

        else:
            # English Response (en-IN)
            if intent in ["umbrella", "precipitation"]:
                pop_val = max(tomorrow.precipitation_probability_max, max_pop_24h)
                precip_val = max(tomorrow.precipitation_sum, cur.precipitation)
                if pop_val >= 50:
                    answer = f"Yes, I'd recommend carrying an umbrella or raincoat in {loc_name}. There is a {pop_val}% chance of rain with around {precip_val:.1f} mm expected precipitation."
                else:
                    answer = f"No umbrella needed for {loc_name} right now. Rain probability is low at only {pop_val}% with clear to partly cloudy conditions."
            
            elif intent == "travel_advisory":
                if tomorrow.precipitation_probability_max >= 70 or tomorrow.temperature_max >= 40:
                    answer = f"Travel advice for {loc_name}: Exercise caution. High rain chance ({tomorrow.precipitation_probability_max}%) and temperature around {tomorrow.temperature_max}°C."
                else:
                    answer = f"Yes, it's generally safe to travel in {loc_name} tomorrow! Expect pleasant weather with a high of {tomorrow.temperature_max}°C and moderate wind speed of {cur.wind_speed} km/h."

            elif intent == "temperature":
                answer = f"Current temperature in {loc_name} is {cur.temperature:.1f}°C (feels like {cur.apparent_temperature:.1f}°C). Tomorrow's maximum high will reach {tomorrow.temperature_max:.1f}°C."

            elif intent == "uv_index":
                answer = f"The UV index in {loc_name} is currently {cur.uv_index:.1f} (Peak daily UV: {tomorrow.uv_index_max:.1f}). Consider sunscreen if outdoors between 11 AM and 3 PM."

            elif intent == "wind":
                answer = f"Wind speed in {loc_name} is currently {cur.wind_speed:.1f} km/h coming from {cur.wind_direction}°."

            elif intent == "comparison":
                answer = f"In {loc_name}, today's temperature is {cur.temperature:.1f}°C compared to tomorrow's expected high of {tomorrow.temperature_max:.1f}°C with a {tomorrow.precipitation_probability_max}% chance of rain."

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
