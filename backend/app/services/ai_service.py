import re
import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.config import settings
from app.models.schemas import ChatRequest, ChatResponse, LocationCoordinates
from app.services.weather_service import WeatherService
from app.services.geocoding_service import GeocodingService
from app.services.advisory_service import AdvisoryService
from app.services.query_resolver import QueryResolver, WeatherQueryObject
from app.constants.languages import get_location_required_message

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def extract_location_from_text(text: str) -> Optional[str]:
        text_lower = text.lower()
        
        cities = [
            "Hyderabad", "Vijayawada", "Delhi", "Mumbai", "Bengaluru", "Bangalore",
            "Tadepalligudem", "Chennai", "Kolkata", "Visakhapatnam", "Vizag", "Pune",
            "Jaipur", "Ahmedabad", "Lucknow", "Bhimavaram", "Guntur", "Tirupati",
            "Kakinada", "Rajahmundry", "Nellore", "Anantapur", "Warangal", "Surat", "Patna",
            "Chinamiram", "Pedda Amiram"
        ]
        for c in cities:
            if c.lower() in text_lower:
                if c.lower() == "bangalore": return "Bengaluru"
                if c.lower() == "vizag": return "Visakhapatnam"
                return c
        
        in_match = re.search(r'\b(?:in|at|for|near|of|around)\s+([a-zA-Z\s]+?)(?:\s+today|\s+tomorrow|\s+yesterday|\s+this|\s+now|\?|\.|$|,)', text, re.IGNORECASE)
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

    @classmethod
    async def process_chat(cls, request: ChatRequest) -> ChatResponse:
        user_msg = request.message.strip()
        lang = cls.detect_language(user_msg, request.language or "en-IN")

        # 1. Resolve Location
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

        loc_name = target_location.city or target_location.name or "Selected Location"

        # 2. Resolve Query Object (Date, Time, Metric, Comparison)
        query_obj: WeatherQueryObject = QueryResolver.resolve_query(user_msg)
        
        # 3. Retrieve Open-Meteo Weather Data for exact requested date(s)
        weather_payload: Dict[str, Any] = {}
        comparison_payload: Dict[str, Any] = {}
        
        if query_obj.is_comparison and query_obj.comparison_date1 and query_obj.comparison_date2:
            data1 = await WeatherService.get_weather_for_date_range(
                latitude=target_location.latitude,
                longitude=target_location.longitude,
                start_date=query_obj.comparison_date1,
                end_date=query_obj.comparison_date1,
                location_name=loc_name
            )
            data2 = await WeatherService.get_weather_for_date_range(
                latitude=target_location.latitude,
                longitude=target_location.longitude,
                start_date=query_obj.comparison_date2,
                end_date=query_obj.comparison_date2,
                location_name=loc_name
            )
            weather_payload = data1
            comparison_payload = data2
        else:
            weather_payload = await WeatherService.get_weather_for_date_range(
                latitude=target_location.latitude,
                longitude=target_location.longitude,
                start_date=query_obj.target_date,
                end_date=query_obj.end_date or query_obj.target_date,
                location_name=loc_name
            )

        # 4. Strict Validation of returned weather data
        if not weather_payload.get("is_available", False):
            unavailable_msg = {
                "te-IN": f"క్షమించండి, {loc_name} కోసం {query_obj.resolved_date_label} వాతావరణ సమాచారం అందుబాటులో లేదు.",
                "hi-IN": f"क्षमा करें, {loc_name} के लिए {query_obj.resolved_date_label} का मौसम डेटा उपलब्ध नहीं है।",
                "en-IN": f"Sorry, weather data for {query_obj.resolved_date_label} in {loc_name} is currently unavailable."
            }
            return ChatResponse(
                answer=unavailable_msg.get(lang, unavailable_msg["en-IN"]),
                language=lang,
                intent=query_obj.intent,
                location=target_location,
                weather=None,
                advisory=None,
                suggested_followups=["Today's Weather", "Tomorrow's Forecast"],
                is_fallback=True,
                is_location_required=False,
                explicit_override=explicit_override
            )

        # 5. Generate Response via Google Gemini API (or Fallback Engine)
        answer = await cls._generate_answer(
            user_msg=user_msg,
            lang=lang,
            loc_name=loc_name,
            query_obj=query_obj,
            data1=weather_payload,
            data2=comparison_payload if query_obj.is_comparison else None
        )

        # Fetch standard forecast object for UI widgets & advisory generator
        standard_forecast = await WeatherService.get_forecast(
            latitude=target_location.latitude,
            longitude=target_location.longitude,
            location_name=loc_name
        )
        advisories = AdvisoryService.generate_advisories(standard_forecast)
        top_advisory = advisories[0] if advisories else None

        # Build weather summary dictionary for response metadata
        daily_first = weather_payload.get("daily", [{}])[0] if weather_payload.get("daily") else {}
        hourly_first = weather_payload.get("hourly", [{}])[0] if weather_payload.get("hourly") else {}

        weather_summary = {
            "temperature": daily_first.get("temperature_max", standard_forecast.current.temperature),
            "apparent_temperature": hourly_first.get("apparent_temperature", standard_forecast.current.apparent_temperature),
            "condition": daily_first.get("condition", standard_forecast.current.condition),
            "humidity": hourly_first.get("humidity", standard_forecast.current.relative_humidity),
            "wind_speed": daily_first.get("wind_speed_max", standard_forecast.current.wind_speed),
            "rain_probability": daily_first.get("precipitation_probability_max", 0),
            "uv_index": daily_first.get("uv_index_max", 5.0),
            "requested_date": query_obj.target_date,
            "resolved_label": query_obj.resolved_date_label
        }

        # Suggested followups based on language
        followups_map = {
            "te-IN": ["రేపు వర్షం పడుతుందా?", "నిన్న ఎంత ఉష్ణోగ్రత ఉండింది?", "ఈరోజు వాతావరణం ఎలా ఉంది?"],
            "hi-IN": ["क्या कल बारिश होगी?", "कल का तापमान कितना था?", "आज का मौसम कैसा है?"],
            "en-IN": ["Will it rain tomorrow?", "What was yesterday's temperature?", "Was yesterday hotter than today?"]
        }

        return ChatResponse(
            answer=answer,
            language=lang,
            intent=query_obj.intent,
            location=target_location,
            weather=weather_summary,
            advisory=top_advisory,
            suggested_followups=followups_map.get(lang, followups_map["en-IN"]),
            is_fallback=False,
            is_location_required=False,
            explicit_override=explicit_override
        )

    @classmethod
    async def _generate_answer(
        cls,
        user_msg: str,
        lang: str,
        loc_name: str,
        query_obj: WeatherQueryObject,
        data1: Dict[str, Any],
        data2: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Attempts to call Google Gemini API to synthesize natural conversational answer.
        Falls back to exact Python template synthesis if Gemini key is not provided or API fails.
        """
        # If Gemini API Key is configured, attempt LLM call
        if settings.GEMINI_API_KEY:
            try:
                llm_response = await cls._call_gemini_llm(user_msg, lang, loc_name, query_obj, data1, data2)
                if llm_response:
                    return llm_response
            except Exception as e:
                logger.warning(f"Gemini API call failed ({e}). Using fallback template engine.")

        # Deterministic Fallback Synthesis
        return cls._synthesize_fallback_answer(lang, loc_name, query_obj, data1, data2)

    @classmethod
    async def _call_gemini_llm(
        cls,
        user_msg: str,
        lang: str,
        loc_name: str,
        query_obj: WeatherQueryObject,
        data1: Dict[str, Any],
        data2: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        lang_names = {"te-IN": "Telugu", "hi-IN": "Hindi", "en-IN": "English"}
        target_lang = lang_names.get(lang, "English")

        prompt = f"""
You are WeatherGPT, a voice-first conversational weather assistant.
Answer the user's question using ONLY the provided Open-Meteo weather data below.

CRITICAL INSTRUCTIONS:
1. You MUST use ONLY the exact numbers in the Open-Meteo data below. Never invent or estimate weather values.
2. The user's question is for: {loc_name} ({query_obj.resolved_date_label}, Date: {query_obj.target_date}).
3. Answer the user's specific question directly in 1-2 clear, conversational sentences.
4. Respond completely in {target_lang}.

USER QUESTION: "{user_msg}"
TARGET METRIC: {query_obj.metric}
TIME SLOT / HOUR: {query_obj.target_time_slot or 'All Day'}

OPEN-METEO WEATHER DATA 1 ({query_obj.resolved_date_label} - {query_obj.target_date}):
{data1}
"""
        if data2 and query_obj.is_comparison:
            prompt += f"""
OPEN-METEO WEATHER DATA 2 ({query_obj.comparison_label2} - {query_obj.comparison_date2}):
{data2}
"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.post(url, json=payload)
            if res.status_code == 200:
                body = res.json()
                candidates = body.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        return None

    @classmethod
    def _synthesize_fallback_answer(
        cls,
        lang: str,
        loc_name: str,
        query_obj: WeatherQueryObject,
        data1: Dict[str, Any],
        data2: Optional[Dict[str, Any]] = None
    ) -> str:
        daily1 = data1.get("daily", [{}])[0] if data1.get("daily") else {}
        hourly1 = data1.get("hourly", [])
        
        t_max1 = daily1.get("temperature_max", 30.0)
        t_min1 = daily1.get("temperature_min", 22.0)
        precip1 = daily1.get("precipitation_sum", 0.0)
        pop1 = daily1.get("precipitation_probability_max", 0)
        cond1 = daily1.get("condition", "Partly Cloudy")
        wind1 = daily1.get("wind_speed_max", 10.0)

        # Filter hourly if specific time slot or hour requested
        specific_hourly = None
        if query_obj.target_hour is not None and hourly1:
            for h in hourly1:
                if h.get("hour") == query_obj.target_hour:
                    specific_hourly = h
                    break
        elif query_obj.target_time_slot and hourly1:
            # Pick representative hour for time slot
            slot_hours = {"morning": 9, "afternoon": 14, "evening": 18, "night": 22}
            target_h = slot_hours.get(query_obj.target_time_slot, 12)
            for h in hourly1:
                if h.get("hour") == target_h:
                    specific_hourly = h
                    break

        label = query_obj.resolved_date_label
        date_str = query_obj.target_date

        is_te = lang.startswith("te")
        is_hi = lang.startswith("hi")

        # --- COMPARISON SYNTHESIS ---
        if query_obj.is_comparison and data2:
            daily2 = data2.get("daily", [{}])[0] if data2.get("daily") else {}
            t_max2 = daily2.get("temperature_max", 30.0)
            lbl1 = query_obj.comparison_label1 or "Date 1"
            lbl2 = query_obj.comparison_label2 or "Date 2"

            if is_te:
                if t_max1 > t_max2 + 1:
                    return f"{lbl2} తో పోలిస్తే {lbl1}న {loc_name} లో వాతావరణం వేడిగా ఉంది. {lbl1}న గరిష్ట ఉష్ణోగ్రత {t_max1:.0f}°C కాగా, {lbl2}న {t_max2:.0f}°C."
                elif t_max2 > t_max1 + 1:
                    return f"{lbl2} తో పోలిస్తే {lbl1}న {loc_name} లో వాతావరణం చల్లగా ఉంది. {lbl1}న ఉష్ణోగ్రత {t_max1:.0f}°C కాగా, {lbl2}న {t_max2:.0f}°C."
                else:
                    return f"{lbl1} మరియు {lbl2}న {loc_name} లో ఉష్ణోగ్రతలు సమానంగా ఉంటాయి (సుమారు {t_max1:.0f}°C)."
            elif is_hi:
                if t_max1 > t_max2 + 1:
                    return f"{lbl2} की तुलना में {lbl1} को {loc_name} में अधिक गर्मी थी। {lbl1} का अधिकतम तापमान {t_max1:.0f}°C था जबकि {lbl2} को {t_max2:.0f}°C।"
                elif t_max2 > t_max1 + 1:
                    return f"{lbl2} की तुलना में {lbl1} को {loc_name} में मौसम ठंडा था। {lbl1} को तापमान {t_max1:.0f}°C था जबकि {lbl2} को {t_max2:.0f}°C।"
                else:
                    return f"{lbl1} और {lbl2} को {loc_name} में तापमान समान था (लगभग {t_max1:.0f}°C)।"
            else:
                if t_max1 > t_max2 + 1:
                    return f"{lbl1} was warmer than {lbl2} in {loc_name}. High temperature on {lbl1} was {t_max1:.0f}°C compared to {t_max2:.0f}°C on {lbl2}."
                elif t_max2 > t_max1 + 1:
                    return f"{lbl1} was cooler than {lbl2} in {loc_name}. High temperature on {lbl1} was {t_max1:.0f}°C compared to {t_max2:.0f}°C on {lbl2}."
                else:
                    return f"Temperatures on {lbl1} and {lbl2} in {loc_name} were similar around {t_max1:.0f}°C."

        # --- SPECIFIC HOUR / TIME SLOT SYNTHESIS ---
        if specific_hourly:
            h_temp = specific_hourly.get("temperature", t_max1)
            h_pop = specific_hourly.get("precipitation_probability", pop1)
            h_cond = specific_hourly.get("condition", cond1)
            h_time = specific_hourly.get("time", "12:00")

            if is_te:
                return f"{loc_name} లో {label} ({date_str}) సమయం {h_time} కి ఉష్ణోగ్రత {h_temp:.1f}°C మరియు వాతావరణం {h_cond} గా ఉంది (వర్ష సూచన {h_pop}%)."
            elif is_hi:
                return f"{loc_name} में {label} ({date_str}) को समय {h_time} बजे तापमान {h_temp:.1f}°C और मौसम {h_cond} रहने का अनुमान है (बारिश {h_pop}%)।"
            else:
                return f"In {loc_name} on {label} ({date_str}) at {h_time}, temperature is {h_temp:.1f}°C with {h_cond.lower()} conditions (rain chance {h_pop}%)."

        # --- METRIC SPECIFIC SYNTHESIS ---
        m = query_obj.metric

        if m in ["umbrella", "precipitation"]:
            if pop1 >= 40 or precip1 >= 1.0:
                if is_te:
                    return f"అవును, {loc_name} లో {label} ({date_str}) న వర్షం పడే అవకాశం {pop1}% ఉంది. వర్షపాతం సుమారు {precip1:.1f} mm నమోదు కావచ్చు."
                elif is_hi:
                    return f"हां, {loc_name} में {label} ({date_str}) को बारिश होने की {pop1}% संभावना है (वर्षा {precip1:.1f} mm)।"
                else:
                    return f"Yes, rain is expected in {loc_name} on {label} ({date_str}) with a {pop1}% chance and {precip1:.1f} mm precipitation."
            else:
                if is_te:
                    return f"లేదు, {loc_name} లో {label} ({date_str}) న వర్షం పడే అవకాశం తక్కువ (కేవలం {pop1}%, వర్షపాతం {precip1:.1f} mm)."
                elif is_hi:
                    return f"नहीं, {loc_name} में {label} ({date_str}) को बारिश की संभावना केवल {pop1}% है।"
                else:
                    return f"No rain is expected in {loc_name} on {label} ({date_str}). Rain chance is only {pop1}% with {cond1.lower()} weather."

        elif m == "temperature":
            if is_te:
                return f"{loc_name} లో {label} ({date_str}) న కనిష్ట ఉష్ణోగ్రత {t_min1:.0f}°C మరియు గరిష్ట ఉష్ణోగ్రత {t_max1:.0f}°C గా నమోదైంది."
            elif is_hi:
                return f"{loc_name} में {label} ({date_str}) को न्यूनतम तापमान {t_min1:.0f}°C और अधिकतम {t_max1:.0f}°C दर्ज किया गया था।"
            else:
                return f"In {loc_name} on {label} ({date_str}), temperatures range from a low of {t_min1:.0f}°C to a high of {t_max1:.0f}°C."

        elif m == "humidity":
            h_val = hourly1[0].get("humidity", 65) if hourly1 else 65
            if is_te:
                return f"{loc_name} లో {label} ({date_str}) న సగటు గాలి తేమ శాతం {h_val}%."
            elif is_hi:
                return f"{loc_name} में {label} ({date_str}) को औसत नमी {h_val}% दर्ज की गई थी।"
            else:
                return f"Relative humidity in {loc_name} on {label} ({date_str}) averaged around {h_val}%."

        elif m == "wind":
            if is_te:
                return f"{loc_name} లో {label} ({date_str}) న గరిష్ట గాలి వేగం గంటకు {wind1:.1f} కిలోమీటర్లు."
            elif is_hi:
                return f"{loc_name} में {label} ({date_str}) को अधिकतम हवा की गति {wind1:.1f} किमी/घंटा थी।"
            else:
                return f"Maximum wind speed in {loc_name} on {label} ({date_str}) reached {wind1:.1f} km/h."

        # Default Summary
        if is_te:
            return f"{loc_name} లో {label} ({date_str}) న వాతావరణం {cond1} గా ఉంది. ఉష్ణోగ్రతలు {t_min1:.0f}°C నుండి {t_max1:.0f}°C వరకు ఉంటాయి (వర్షపాతం {precip1:.1f} mm)."
        elif is_hi:
            return f"{loc_name} में {label} ({date_str}) को मौसम {cond1} रहा। तापमान {t_min1:.0f}°C से {t_max1:.0f}°C तक (वर्षा {precip1:.1f} mm)।"
        else:
            return f"Weather in {loc_name} on {label} ({date_str}) features {cond1.lower()} conditions with temperatures between {t_min1:.0f}°C and {t_max1:.0f}°C (precipitation {precip1:.1f} mm)."
