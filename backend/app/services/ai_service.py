import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.models.schemas import ChatRequest, ChatResponse, WeatherForecastResponse, LocationCoordinates, AdvisoryItem
from app.services.weather_service import WeatherService
from app.services.geocoding_service import GeocodingService
from app.services.advisory_service import AdvisoryService
from app.constants.languages import get_location_required_message

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def extract_location_from_text(text: str) -> Optional[str]:
        text_lower = text.lower()
        
        # Check standard Indian city names directly in text
        cities = [
            "Hyderabad", "Vijayawada", "Delhi", "Mumbai", "Bengaluru", "Bangalore",
            "Tadepalligudem", "Chennai", "Kolkata", "Visakhapatnam", "Vizag", "Pune",
            "Jaipur", "Ahmedabad", "Lucknow", "Bhimavaram", "Guntur", "Tirupati",
            "Kakinada", "Rajahmundry", "Nellore", "Anantapur", "Warangal", "Surat", "Patna"
        ]
        for c in cities:
            if c.lower() in text_lower:
                return "Bengaluru" if c.lower() == "bangalore" else ("Visakhapatnam" if c.lower() == "vizag" else c)
        
        # Pattern match "in <City>", "at <City>", "for <City>"
        in_match = re.search(r'\b(?:in|at|for|near|of|around)\s+([a-zA-Z\s]+?)(?:\s+today|\s+tomorrow|\s+this|\s+now|\?|\.|$|,)', text, re.IGNORECASE)
        if in_match:
            candidate = in_match.group(1).strip()
            ignored = ["the", "my area", "here", "college", "work", "office", "home", "india", "my location", "location", "area"]
            if candidate and candidate.lower() not in ignored and len(candidate) > 2:
                return candidate.title()
                
        return None

    @staticmethod
    def detect_language(text: str, default_lang: str = "en-IN") -> str:
        if re.search(r"[\u0C00-\u0C7F]", text):
            return "te-IN"
        if re.search(r"[\u0900-\u097F]", text):
            return "hi-IN"
        return default_lang

    @staticmethod
    def detect_intent(text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["umbrella", "raincoat", "rain coat", "need rain", "గొడుగు", "రెయిన్‌కోట్", "छाता"]):
            return "umbrella"
        if any(w in t for w in ["cold", "colder", "coldest", "cool", "ठंड", "ठंडी", "सर्दी", "చల్లగా", "చలి"]):
            return "cold_check"
        if any(w in t for w in ["hot", "hotter", "heat", "warm", "warmer", "गर्म", "गर्मी", "धूप", "వేడిగా", "వేడి", "ఎండ"]):
            return "heat_check"
        if any(w in t for w in ["rain", "raining", "rainfall", "drizzle", "shower", "వర్షం", "వర్షపాతం", "बारिश", "बरसात"]):
            return "precipitation"
        if any(w in t for w in ["compare", "difference", "versus", "vs", "పోల్చండి", "తారతమ్యం", "तुलना"]):
            return "comparison"
        if any(w in t for w in ["temperature", "degree", "temp", "ఉష్ణోగ్రత", "तापमान"]):
            return "temperature"
        if any(w in t for w in ["humidity", "humid", "moisture", "తేమ", "नमी"]):
            return "humidity"
        if any(w in t for w in ["wind", "storm", "blow", "breeze", "గాలి", "హవా", "हवा", "आंधी"]):
            return "wind"
        if any(w in t for w in ["uv", "sun", "sunscreen", "ultraviolet", "ఎండ", "धूप"]):
            return "uv_index"
        if any(w in t for w in ["thunder", "lightning", "storm", "ఉరుములు", "మెరుపులు", "तूफान", "बिजली"]):
            return "thunderstorm"
        if any(w in t for w in ["college", "school", "travel", "drive", "trip", "going to", "outside", "safe to", "పయనం", "ప్రయాణం", "यात्रा", "घूमने"]):
            return "travel_advisory"
        if any(w in t for w in ["run", "jog", "walk", "outdoor", "picnic", "cricket", "match", "వాకింగ్", "ఆరుబయట", "सैर", "घूमना"]):
            return "outdoor_activity"
        if any(w in t for w in ["tomorrow", "weekend", "next week", "day after", "రేపు", "कल"]):
            return "forecast"
        return "current_weather"

    @classmethod
    async def process_chat(cls, request: ChatRequest) -> ChatResponse:
        user_msg = request.message.strip()
        
        # 0. Script-based Auto Language Override (Te/Hi/En)
        lang = cls.detect_language(user_msg, request.language or "en-IN")

        # 1. Check for explicit location mentioned in user message
        extracted_city = cls.extract_location_from_text(user_msg)
        
        target_location: Optional[LocationCoordinates] = None
        explicit_override = False

        if extracted_city:
            search_results = await GeocodingService.search_location(extracted_city)
            if search_results:
                best = search_results[0]
                target_location = LocationCoordinates(
                    latitude=best.latitude,
                    longitude=best.longitude,
                    name=best.name,
                    city=best.name,
                    country=best.country or "India",
                    admin1=best.admin1 or "",
                    state=best.admin1 or "",
                    displayName=best.display_name,
                    source="search"
                )
                active_name = (request.location.city or request.location.name) if request.location else ""
                if active_name and active_name.lower() != best.name.lower():
                    explicit_override = True
        
        if target_location is None:
            if request.location and request.location.latitude != 0 and request.location.longitude != 0:
                target_location = request.location
            else:
                target_location = None

        if target_location is None:
            return ChatResponse(
                answer=get_location_required_message(lang),
                language=lang,
                intent="location_required",
                location=None,
                weather=None,
                advisory=None,
                suggested_followups=["Use My Location", "Search Location"],
                is_fallback=False,
                is_location_required=True,
                explicit_override=False
            )

        # 2. Fetch Weather Data
        loc_name = target_location.city or target_location.name or "Selected Location"
        weather_data = await WeatherService.get_forecast(
            latitude=target_location.latitude,
            longitude=target_location.longitude,
            location_name=loc_name
        )

        # 3. Advisories
        advisories = AdvisoryService.generate_advisories(weather_data)
        top_advisory = advisories[0] if advisories else None

        # 4. Intent detection
        intent = cls.detect_intent(user_msg)

        # 5. Weather Parameters
        cur = weather_data.current
        hourly = weather_data.hourly
        daily = weather_data.daily
        
        today = daily[0] if len(daily) > 0 else None
        tomorrow = daily[1] if len(daily) > 1 else (daily[0] if daily else None)

        msg_low = user_msg.lower()

        # Timeframe resolution: tomorrow vs today vs weekend
        is_tomorrow = any(w in msg_low for w in ["tomorrow", "రేపు", "कल"])
        is_weekend = any(w in msg_low for w in ["weekend", "వారాంతం", "वीकेंड"])

        target_day = tomorrow if (is_tomorrow and tomorrow) else today
        
        # Telemetry metrics
        t_max = target_day.temperature_max if target_day else cur.temperature
        t_min = target_day.temperature_min if target_day else cur.temperature
        pop_max = target_day.precipitation_probability_max if target_day else cur.rain_probability
        precip_sum = target_day.precipitation_sum if target_day else cur.precipitation

        answer = ""
        suggested_followups: List[str] = []

        is_te = lang.startswith("te")
        is_hi = lang.startswith("hi")

        if is_te:
            # --- TELUGU CONVERSATIONAL REASONING ---
            if intent == "cold_check":
                if t_max < 20.0:
                    answer = f"అవును, {loc_name}లో చల్లగా ఉంటుంది. ఉష్ణోగ్రత కనిష్టం {t_min:.0f}°C మరియు గరిష్టం {t_max:.0f}°C వరకు ఉండవచ్చు."
                else:
                    answer = f"లేదు, {loc_name}లో {'రేపు ' if is_tomorrow else ''}చల్లగా ఉండే అవకాశం లేదు. ఉష్ణోగ్రత సుమారు {t_max:.0f}°C ఉంటుంది, కాబట్టి వాతావరణం వెచ్చగా అనిపించవచ్చు."
            
            elif intent == "heat_check":
                if t_max >= 35.0:
                    answer = f"అవును, {loc_name}లో {'రేపు ' if is_tomorrow else ''}చాలా వేడిగా ఉంటుంది. గరిష్ట ఉష్ణోగ్రత {t_max:.0f}°C కు చేరుకోవచ్చు. ఎండ దెబ్బ తగలకుండా జాగ్రత్త పడండి."
                else:
                    answer = f"లేదండీ, {loc_name}లో తీవ్రమైన వేడి లేదు. ఉష్ణోగ్రత సుమారు {t_max:.0f}°C గా ఉంటుంది."

            elif intent in ["umbrella", "precipitation"]:
                if pop_max >= 45 or precip_sum >= 1.5:
                    answer = f"అవును, {loc_name}లో {'రేపు ' if is_tomorrow else ''}గొడుగు లేదా రెయిన్‌కోట్ తీసుకెళ్లడం మంచిది. {pop_max:.0f}% వర్షం పడే అవకాశం ఉంది."
                else:
                    answer = f"లేదు, {loc_name}లో {'రేపు ' if is_tomorrow else ''}గొడుగు అవసరం లేదు. వర్షం పడే అవకాశం కేవలం {pop_max:.0f}% మాత్రమే ఉంది."

            elif intent == "travel_advisory":
                if pop_max >= 65 or t_max >= 39 or cur.wind_speed >= 30:
                    answer = f"{loc_name}కు ప్రయాణం చేసేటప్పుడు జాగ్రత్త వహించండి. వర్ష సూచన {pop_max:.0f}% మరియు ఉష్ణోగ్రత {t_max:.0f}°C వరకు ఉంటుంది."
                else:
                    answer = f"అవును, {loc_name}లో {'రేపు ' if is_tomorrow else ''}ప్రయాణం చేయడానికి వాతావరణం చాలా అనుకూలంగా ఉంది! ఉష్ణోగ్రత సుమారు {t_max:.0f}°C ఉంటుంది."

            elif intent == "outdoor_activity":
                if pop_max >= 50 or t_max >= 36:
                    answer = f"{loc_name}లో ఆరుబయట తిరగడం లేదా ఆటలకు వర్షం ({pop_max:.0f}%) లేదా వేడి ({t_max:.0f}°C) వల్ల కొద్దిగా అంతరాయం కలగవచ్చు."
                else:
                    answer = f"{loc_name}లో వాతావరణం చాలా ప్రశాంతంగా ఉంది! వాకింగ్ లేదా బయటకు వెళ్లడానికి ఇది సరైన సమయం. ఉష్ణోగ్రత {t_max:.0f}°C."

            elif intent == "comparison":
                t0 = today.temperature_max if today else cur.temperature
                t1 = tomorrow.temperature_max if tomorrow else cur.temperature
                if t1 > t0 + 1:
                    answer = f"ఈరోజు కంటే రేపు {loc_name}లో కొద్దిగా వేడిగా ఉంటుంది. ఈరోజు గరిష్ట ఉష్ణోగ్రత {t0:.0f}°C కాగా, రేపు {t1:.0f}°C నమోదు కావచ్చు."
                elif t0 > t1 + 1:
                    answer = f"ఈరోజు కంటే రేపు {loc_name}లో వాతావరణం చల్లగా ఉంటుంది. ఈరోజు ఉష్ణోగ్రత {t0:.0f}°C కాగా, రేపు {t1:.0f}°C కు పడిపోవచ్చు."
                else:
                    answer = f"ఈరోజు మరియు రేపు {loc_name}లో ఉష్ణోగ్రతలు సమానంగా ఉంటాయి (సుమారు {t0:.0f}°C)."

            elif intent == "humidity":
                answer = f"{loc_name}లో ప్రస్తుత గాలి తేమ శాతం {cur.relative_humidity}%."

            elif intent == "wind":
                answer = f"{loc_name}లో గాలి వేగం ప్రస్తుతం గంటకు {cur.wind_speed} కిలోమీటర్లు."

            elif intent == "uv_index":
                answer = f"{loc_name}లో యూవీ ఇండెక్స్ {cur.uv_index}. మధ్యాహ్నం 11 నుండి 3 గంటల మధ్య ఎండలో జాగ్రత్తగా ఉండండి."

            elif intent == "temperature":
                answer = f"{loc_name}లో ఉష్ణోగ్రత ప్రస్తుతానికి {cur.temperature:.1f}°C (అనుభూతి {cur.apparent_temperature:.1f}°C). {'రేపటి ' if is_tomorrow else 'నేటి '}గరిష్ట ఉష్ణోగ్రత {t_max:.0f}°C వరకు ఉంటుంది."

            else:
                answer = f"{loc_name}లో ప్రస్తుతం వాతావరణం {cur.condition}గా ఉంది. ఉష్ణోగ్రత {cur.temperature:.1f}°C, తేమ {cur.relative_humidity}% మరియు గాలి వేగం {cur.wind_speed} కి.మీ/గం."

            suggested_followups = ["రేపు వర్షం పడుతుందా?", "గొడుగు అవసరమా?", "ఉష్ణోగ్రత ఎంత ఉంటుంది?"]

        elif is_hi:
            # --- HINDI CONVERSATIONAL REASONING ---
            if intent == "cold_check":
                if t_max < 20.0:
                    answer = f"हां, {loc_name} में मौसम ठंडा रहेगा। न्यूनतम तापमान {t_min:.0f}°C और अधिकतम {t_max:.0f}°C रहने की संभावना है।"
                else:
                    answer = f"नहीं, {loc_name} में {'कल ' if is_tomorrow else ''}ठंड होने की संभावना नहीं है। तापमान लगभग {t_max:.0f}°C रहेगा, इसलिए मौसम गर्म महसूस हो सकता है।"

            elif intent == "heat_check":
                if t_max >= 35.0:
                    answer = f"हां, {loc_name} में {'कल ' if is_tomorrow else ''}काफी गर्मी रहेगी। अधिकतम तापमान {t_max:.0f}°C तक पहुंच सकता है। धूप से बचाव रखें।"
                else:
                    answer = f"नहीं, {loc_name} में अत्यधिक गर्मी नहीं है। तापमान लगभग {t_max:.0f}°C रहने का अनुमान है।"

            elif intent in ["umbrella", "precipitation"]:
                if pop_max >= 45 or precip_sum >= 1.5:
                    answer = f"हां, कल {loc_name} में छाता या रेनकोट साथ रखना बेहतर रहेगा। बारिश की {pop_max:.0f}% संभावना है।"
                else:
                    answer = f"नहीं, कल {loc_name} में छाते की आवश्यकता नहीं है। बारिश की संभावना केवल {pop_max:.0f}% है।"

            elif intent == "travel_advisory":
                if pop_max >= 65 or t_max >= 39 or cur.wind_speed >= 30:
                    answer = f"{loc_name} की यात्रा में सावधानी बरतें। बारिश की संभावना ({pop_max:.0f}%) और तापमान {t_max:.0f}°C रहेगा।"
                else:
                    answer = f"हां, कल {loc_name} में यात्रा करना बिल्कुल ठीक रहेगा! मौसम सुहावना रहेगा और तापमान लगभग {t_max:.0f}°C रहेगा।"

            elif intent == "outdoor_activity":
                if pop_max >= 50 or t_max >= 36:
                    answer = f"{loc_name} में बाहर घूमने या खेलकूद में बारिश ({pop_max:.0f}%) या गर्मी ({t_max:.0f}°C) के कारण रुकावट आ सकती है।"
                else:
                    answer = f"{loc_name} में मौसम बहुत अच्छा है! टहलने या बाहर जाने के लिए यह सही समय है। तापमान {t_max:.0f}°C है।"

            elif intent == "comparison":
                t0 = today.temperature_max if today else cur.temperature
                t1 = tomorrow.temperature_max if tomorrow else cur.temperature
                if t1 > t0 + 1:
                    answer = f"कल {loc_name} में आज की तुलना में थोड़ी अधिक गर्मी रहेगी। आज का अधिकतम तापमान {t0:.0f}°C है, जबकि कल {t1:.0f}°C तक पहुंचेगा।"
                elif t0 > t1 + 1:
                    answer = f"आज की तुलना में कल {loc_name} में मौसम ठंडा रहेगा। आज का तापमान {t0:.0f}°C है, जबकि कल {t1:.0f}°C रहने का अनुमान है।"
                else:
                    answer = f"आज और कल {loc_name} में तापमान लगभग समान रहेगा (लगभग {t0:.0f}°C)।"

            elif intent == "humidity":
                answer = f"{loc_name} में वर्तमान नमी (Humidity) {cur.relative_humidity}% है।"

            elif intent == "wind":
                answer = f"{loc_name} में हवा की गति {cur.wind_speed} किमी/घंटा है।"

            elif intent == "uv_index":
                answer = f"{loc_name} में यूवी इंडेक्स {cur.uv_index} है। दोपहर में धूप से बचाव रखें।"

            elif intent == "temperature":
                answer = f"{loc_name} में अभी तापमान {cur.temperature:.1f}°C (महसूस {cur.apparent_temperature:.1f}°C) है। {'कल का ' if is_tomorrow else 'आज का '}अधिकतम तापमान {t_max:.0f}°C रहेगा।"

            else:
                answer = f"{loc_name} में वर्तमान में {cur.condition} मौसम है। तापमान {cur.temperature:.1f}°C, आर्द्रता {cur.relative_humidity}% और हवा {cur.wind_speed} किमी/घंटा है।"

            suggested_followups = ["क्या कल बारिश होगी?", "क्या छाता चाहिए?", "आज का तापमान कितना है?"]

        else:
            # --- ENGLISH CONVERSATIONAL REASONING ---
            if intent == "cold_check":
                if t_max < 20.0:
                    answer = f"Yes, it will be cold in {loc_name}{' tomorrow' if is_tomorrow else ''}. Low temperature will drop to {t_min:.0f}°C with a high of {t_max:.0f}°C."
                else:
                    answer = f"No, {'tomorrow is' if is_tomorrow else 'it is'} not expected to be cold in {loc_name}. The temperature will be around {t_max:.0f}°C, so it will feel warm."

            elif intent == "heat_check":
                if t_max >= 35.0:
                    answer = f"Yes, it will be hot in {loc_name}{' tomorrow' if is_tomorrow else ''}. Expect temperatures peaking around {t_max:.0f}°C. Take precautions against sun exposure."
                else:
                    answer = f"No, severe heat is not expected in {loc_name}. The high temperature will reach a comfortable {t_max:.0f}°C."

            elif intent in ["umbrella", "precipitation"]:
                if pop_max >= 45 or precip_sum >= 1.5:
                    answer = f"Yes, I recommend carrying an umbrella or raincoat in {loc_name}{' tomorrow' if is_tomorrow else ''}. There is a {pop_max:.0f}% chance of rain with expected precipitation."
                else:
                    answer = f"No umbrella needed in {loc_name}{' tomorrow' if is_tomorrow else ''}. Rain probability is low at only {pop_max:.0f}% with {cur.condition.lower()} conditions."

            elif intent == "travel_advisory":
                if pop_max >= 65 or t_max >= 39 or cur.wind_speed >= 30:
                    answer = f"Travel caution advised for {loc_name}: Rain probability is {pop_max:.0f}% with temperatures peaking at {t_max:.0f}°C."
                else:
                    answer = f"Yes, {'tomorrow' if is_tomorrow else 'it'} is great for travelling in {loc_name}! Expect pleasant weather with a high of {t_max:.0f}°C."

            elif intent == "outdoor_activity":
                if pop_max >= 50 or t_max >= 36:
                    answer = f"Outdoor activities in {loc_name} may be affected by rain risk ({pop_max:.0f}%) or warm temperatures ({t_max:.0f}°C)."
                else:
                    answer = f"Conditions in {loc_name} are great for outdoor activities, runs, or walks! Temperature is {cur.temperature:.1f}°C with light breeze."

            elif intent == "comparison":
                t0 = today.temperature_max if today else cur.temperature
                t1 = tomorrow.temperature_max if tomorrow else cur.temperature
                if t1 > t0 + 1:
                    answer = f"Tomorrow will be slightly warmer than today in {loc_name}. Today's high is {t0:.0f}°C, while tomorrow will reach {t1:.0f}°C."
                elif t0 > t1 + 1:
                    answer = f"Tomorrow will be cooler than today in {loc_name}. Today's high reaches {t0:.0f}°C compared to tomorrow's expected {t1:.0f}°C."
                else:
                    answer = f"Temperatures in {loc_name} today and tomorrow will be similar around {t0:.0f}°C."

            elif intent == "humidity":
                answer = f"Relative humidity in {loc_name} is currently {cur.relative_humidity}%."

            elif intent == "wind":
                answer = f"Wind speed in {loc_name} is currently {cur.wind_speed:.1f} km/h."

            elif intent == "uv_index":
                answer = f"The UV index in {loc_name} is currently {cur.uv_index:.1f}. Sunscreen is recommended between 11 AM and 3 PM."

            elif intent == "temperature":
                answer = f"In {loc_name}, current temperature is {cur.temperature:.1f}°C (feels like {cur.apparent_temperature:.1f}°C). {'Tomorrow' if is_tomorrow else 'Today'}'s maximum high will reach {t_max:.0f}°C."

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
            "rain_probability": pop_max,
            "uv_index": cur.uv_index
        }

        return ChatResponse(
            answer=answer,
            language=lang,
            intent=intent,
            location=target_location,
            weather=weather_summary,
            advisory=top_advisory,
            suggested_followups=suggested_followups,
            is_fallback=weather_data.is_fallback,
            is_location_required=False,
            explicit_override=explicit_override
        )

