import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.models.schemas import ChatRequest, ChatResponse, WeatherForecastResponse, LocationCoordinates, AdvisoryItem
from app.services.weather_service import WeatherService
from app.services.geocoding_service import GeocodingService
from app.services.advisory_service import AdvisoryService
from app.services.gemini_service import GeminiService
from app.constants.languages import get_location_required_message, normalize_language_code, get_language_name

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
    def detect_intent(text: str) -> str:
        t = text.lower()
        # umbrella / rain gear
        if any(w in t for w in [
            "umbrella", "raincoat", "rain coat", "need rain",
            "గొడుగు", "రెయిన్‌కోట్", "వర్షపు కోటు",
            "छाता", "रेनकोट"
        ]):
            return "umbrella"
        # precipitation / rain
        if any(w in t for w in [
            "rain", "raining", "rainfall", "drizzle", "shower", "precipitation",
            "వర్షం", "వర్షపాతం", "వానలు", "వర్షాలు", "వర్షపడుతుందా", "వర్షం పడుతుందా",
            "बारिश", "बरसात", "वर्षा"
        ]):
            return "precipitation"
        # comparison
        if any(w in t for w in [
            "compare", "difference", "versus", "vs",
            "పోల్చండి", "తారతమ్యం", "తేడా",
            "तुलना", "फर्क"
        ]):
            return "comparison"
        # temperature
        if any(w in t for w in [
            "hot", "cold", "temperature", "degree", "heat", "warm", "cool",
            "వేడి", "ఉష్ణోగ్రత", "చల్లగా", "డిగ్రీలు", "చలి", "వేడిగా",
            "गर्मी", "तापमान", "ठंड", "डिग्री"
        ]):
            return "temperature"
        # humidity
        if any(w in t for w in [
            "humidity", "humid", "moisture",
            "తేమ", "ఆర్ద్రత",
            "नमी", "आर्द्रता"
        ]):
            return "humidity"
        # wind
        if any(w in t for w in [
            "wind", "storm", "blow", "breeze",
            "గాలి", "హవా", "తుఫాను", "గాలివాన",
            "हवा", "आंधी", "तूफान"
        ]):
            return "wind"
        # uv index / sun
        if any(w in t for w in [
            "uv", "sun", "sunscreen", "ultraviolet",
            "ఎండ", "సన్‌స్క్రీన్", "సూర్యకాంతి",
            "धूप", "सनस्क्रीन"
        ]):
            return "uv_index"
        # thunderstorm
        if any(w in t for w in [
            "thunder", "lightning", "thunderstorm",
            "ఉరుములు", "మెరుపులు", "పిడుగు", "వర్షపు తుఫాను",
            "तूफान", "बिजली", "आंधी-तूफान"
        ]):
            return "thunderstorm"
        # travel / going out
        if any(w in t for w in [
            "college", "school", "travel", "drive", "trip", "going to", "outside", "safe to",
            "పయనం", "ప్రయాణం", "వెళ్ళవచ్చా", "వెళ్ళడం సురక్షితమా", "బయటకు వెళ్ళవచ్చా",
            "यात्रा", "सफर", "जाना"
        ]):
            return "travel_advisory"
        # outdoor activity
        if any(w in t for w in [
            "run", "jog", "walk", "outdoor", "picnic", "cricket", "match", "exercise",
            "వాకింగ్", "ఆరుబయట", "క్రికెట్", "వ్యాయామం", "పిక్నిక్",
            "सैर", "बाहर", "क्रिकेट"
        ]):
            return "outdoor_activity"
        # forecast / tomorrow
        if any(w in t for w in [
            "tomorrow", "weekend", "next week", "day after", "forecast", "week",
            "రేపు", "వచ్చే వారం", "అంచనా", "వారాంతం",
            "कल", "अगला हफ्ता", "सप्ताह"
        ]):
            return "forecast"
        return "current_weather"

    @classmethod
    async def process_chat(cls, request: ChatRequest) -> ChatResponse:
        user_msg = request.message.strip()
        norm_lang = normalize_language_code(request.language)
        lang_name = get_language_name(norm_lang)

        logger.info(f"[AIService] 🧠 Processing query: '{user_msg}' | Input Language: '{request.language}' | Normalized: '{norm_lang}' ({lang_name})")

        # 1. Check for explicit location mentioned in user message (e.g. "What's the weather in Vijayawada?")
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
                # Check if explicit city differs from active location
                active_name = (request.location.city or request.location.name) if request.location else ""
                if active_name and active_name.lower() != best.name.lower():
                    explicit_override = True
        
        if target_location is None:
            # Use active saved location from request
            if request.location and request.location.latitude != 0 and request.location.longitude != 0:
                target_location = request.location
            else:
                target_location = None

        # STRICT VALIDATION: If no location is set, return Location Required response!
        if target_location is None:
            logger.info(f"[AIService] Location is not set. Returning location required prompt in {norm_lang}.")
            return ChatResponse(
                answer=get_location_required_message(norm_lang),
                language=norm_lang,
                intent="location_required",
                location=None,
                weather=None,
                advisory=None,
                suggested_followups=[
                    "Use My Location",
                    "Search Location"
                ],
                is_fallback=False,
                is_location_required=True,
                explicit_override=False
            )

        # 2. Get Live Weather Data for target location
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

        # 5. Extract weather parameters
        cur = weather_data.current
        hourly = weather_data.hourly
        daily = weather_data.daily
        
        today = daily[0] if len(daily) > 0 else None
        tomorrow = daily[1] if len(daily) > 1 else daily[0]
        
        afternoon_temps = [h.temperature for h in hourly[12:17]] if len(hourly) >= 17 else [cur.temperature]
        afternoon_max = max(afternoon_temps, default=cur.temperature)
        
        night_thunders = any(h.weather_code in [95, 96, 99] for h in hourly[18:24]) if len(hourly) >= 24 else False
        max_pop_24h = max([h.precipitation_probability for h in hourly[:24]], default=cur.rain_probability)

        answer = ""
        suggested_followups: List[str] = []

        is_te = norm_lang.startswith("te")
        is_hi = norm_lang.startswith("hi")

        # 6. Try Gemini AI with system_instruction
        weather_context = {
            "location": loc_name,
            "current": {
                "temperature": cur.temperature,
                "apparent_temperature": cur.apparent_temperature,
                "condition": cur.condition,
                "humidity": cur.relative_humidity,
                "wind_speed": cur.wind_speed,
                "rain_probability": max_pop_24h,
                "uv_index": cur.uv_index
            },
            "tomorrow": {
                "temp_max": tomorrow.temperature_max if tomorrow else cur.temperature,
                "temp_min": tomorrow.temperature_min if tomorrow else cur.temperature,
                "rain_probability_max": tomorrow.precipitation_probability_max if tomorrow else max_pop_24h,
                "precipitation_sum": tomorrow.precipitation_sum if tomorrow else cur.precipitation,
                "condition": tomorrow.condition if tomorrow else cur.condition
            }
        }

        gemini_response = await GeminiService.generate_response(
            user_query=user_msg,
            weather_context=weather_context,
            language_code=norm_lang
        )

        if gemini_response:
            answer = gemini_response
            logger.info(f"[AIService] ✅ Using Gemini AI generated response in {lang_name} ({norm_lang})")
            if is_te:
                suggested_followups = ["రేపు వర్షం పడుతుందా?", "గొడుగు అవసరమా?", "ఉష్ణోగ్రత ఎంత ఉంటుంది?"]
            elif is_hi:
                suggested_followups = ["क्या कल बारिश होगी?", "क्या छाता चाहिए?", "आज का तापमान कितना है?"]
            else:
                suggested_followups = ["Will it rain today?", "Do I need an umbrella?", "How hot will tomorrow be?"]
        else:
            logger.info(f"[AIService] ⚡ Generating high-quality native template response for language: {norm_lang} ({lang_name})")

        if is_te:
            # Telugu Response Generation — rich, multi-sentence answers
            if intent in ["umbrella", "precipitation"]:
                pop = max(tomorrow.precipitation_probability_max, max_pop_24h)
                precip = max(tomorrow.precipitation_sum, cur.precipitation)
                if pop >= 70:
                    answer = (
                        f"{loc_name}లో వర్షం పడే అవకాశం చాలా ఎక్కువగా ఉంది — దాదాపు {pop}% వరకు! "
                        f"ఇప్పుడు ఉష్ణోగ్రత {cur.temperature}°C గా ఉండి, వాతావరణం {cur.condition} గా ఉంది. "
                        f"సుమారు {precip:.1f} మి.మీ వర్షపాతం అంచనా వేయబడింది. "
                        f"బయటకు వెళ్ళేటప్పుడు తప్పకుండా గొడుగు లేదా రెయిన్‌కోట్ తీసుకెళ్లండి."
                    )
                elif pop >= 40:
                    answer = (
                        f"{loc_name}లో వర్షం పడే అవకాశం {pop}% గా ఉంది. "
                        f"ప్రస్తుత ఉష్ణోగ్రత {cur.temperature}°C, తేమ శాతం {cur.relative_humidity}%. "
                        f"వాతావరణం అనిశ్చితంగా ఉంది, కాబట్టి జాగ్రత్తగా గొడుగు తీసుకెళ్లడం మంచిది."
                    )
                else:
                    answer = (
                        f"{loc_name}లో ఈ రోజు వర్షం పడే అవకాశం తక్కువగా ఉంది — కేవలం {pop}% మాత్రమే. "
                        f"ప్రస్తుత ఉష్ణోగ్రత {cur.temperature}°C గా ఉండి, వాతావరణం {cur.condition} గా ఉంది. "
                        f"గొడుగు అవసరం లేదు, కానీ ఆకాశం మేఘావృతంగా ఉంటే తీసుకెళ్ళవచ్చు."
                    )
            elif intent == "travel_advisory":
                if tomorrow.precipitation_probability_max >= 70 or tomorrow.temperature_max >= 40:
                    answer = (
                        f"{loc_name}కు ప్రయాణం చేసేటప్పుడు జాగ్రత్త వహించండి. "
                        f"రేపు వర్షం పడే అవకాశం {tomorrow.precipitation_probability_max}% మరియు గరిష్ట ఉష్ణోగ్రత {tomorrow.temperature_max}°C వరకు ఉంటుంది. "
                        f"ప్రస్తుతం గాలి వేగం గంటకు {cur.wind_speed} కిలోమీటర్లు ఉంది. "
                        f"వర్షాకాలపు దుస్తులు, గొడుగు తీసుకెళ్ళడం మరియు నీటి మట్టం పెరిగే ప్రాంతాలకు దూరంగా ఉండండి."
                    )
                else:
                    answer = (
                        f"{loc_name}లో రేపటి వాతావరణం ప్రయాణానికి చాలా అనుకూలంగా ఉంది. "
                        f"రేపు గరిష్ట ఉష్ణోగ్రత {tomorrow.temperature_max}°C గా ఉంటుంది, వర్షం అవకాశం {tomorrow.precipitation_probability_max}% మాత్రమే. "
                        f"ప్రస్తుతం గాలి వేగం {cur.wind_speed} కి.మీ/గం మరియు తేమ శాతం {cur.relative_humidity}%. "
                        f"సురక్షితంగా ప్రయాణించండి!"
                    )
            elif intent == "temperature":
                answer = (
                    f"{loc_name}లో ప్రస్తుత ఉష్ణోగ్రత {cur.temperature}°C గా ఉంది "
                    f"(అనుభూతి ఉష్ణోగ్రత {cur.apparent_temperature}°C). "
                    f"మధ్యాహ్నం {afternoon_max:.1f}°C వరకు పెరుగుతుంది. "
                    f"ఈ రోజు గరిష్ట ఉష్ణోగ్రత {today.temperature_max if today else afternoon_max}°C మరియు కనిష్ట ఉష్ణోగ్రత {today.temperature_min if today else cur.temperature}°C గా ఉంటుంది. "
                    f"తేమ శాతం {cur.relative_humidity}% గా ఉంది."
                )
            elif intent == "humidity":
                answer = (
                    f"{loc_name}లో ప్రస్తుత గాలి తేమ శాతం {cur.relative_humidity}% గా ఉంది. "
                    f"ఉష్ణోగ్రత {cur.temperature}°C గా ఉండటంతో, అనుభూతి ఉష్ణోగ్రత {cur.apparent_temperature}°C గా అనిపిస్తుంది. "
                    f"తేమ ఎక్కువగా ఉన్నప్పుడు మరింత వేడిగా అనిపించవచ్చు — తగినంత నీరు తాగండి మరియు చల్లని ప్రదేశంలో ఉండండి."
                )
            elif intent == "wind":
                answer = (
                    f"{loc_name}లో గాలి వేగం ప్రస్తుతం గంటకు {cur.wind_speed} కిలోమీటర్లు గా నమోదైంది. "
                    f"ఉష్ణోగ్రత {cur.temperature}°C గా ఉండి, వాతావరణం {cur.condition} గా ఉంది. "
                    f"గాలి వేగం ఎక్కువగా ఉన్నప్పుడు పైన కప్పు లేకుండా బయటకు వెళ్ళడం మానుకోండి."
                )
            elif intent == "uv_index":
                answer = (
                    f"{loc_name}లో యూవీ సూచిక (UV Index) ప్రస్తుతం {cur.uv_index} గా ఉంది. "
                    f"ఉష్ణోగ్రత {cur.temperature}°C మరియు తేమ {cur.relative_humidity}% గా ఉంది. "
                    f"మధ్యాహ్నం 11 గంటల నుండి సాయంత్రం 3 గంటల మధ్య ఎండలో బయటకు వెళ్ళేటప్పుడు సన్‌స్క్రీన్ రాసుకోండి మరియు టోపీ ధరించండి."
                )
            elif intent == "thunderstorm":
                if night_thunders or cur.weather_code in [95, 96, 99]:
                    answer = (
                        f"హెచ్చరిక! {loc_name}లో ఉరుములు-మెరుపులతో కూడిన వర్షం అవకాశం ఉంది. "
                        f"ప్రస్తుత ఉష్ణోగ్రత {cur.temperature}°C మరియు వాతావరణం {cur.condition} గా ఉంది. "
                        f"బయట ఉంటే వెంటనే సురక్షిత స్థలానికి వెళ్లండి, చెట్ల కింద నిలబడకండి మరియు ఎలక్ట్రికల్ పరికరాల వాడకం తగ్గించండి."
                    )
                else:
                    answer = (
                        f"{loc_name}లో ఇప్పుడు ఉరుముల ముప్పు తక్కువగా ఉంది. "
                        f"వాతావరణం {cur.condition} గా ఉంది, ఉష్ణోగ్రత {cur.temperature}°C. "
                        f"వర్షం అవకాశం {max_pop_24h}% గా ఉంది — ఆకాశం మేఘావృతంగా ఉన్నా పెద్ద ముప్పు లేదు."
                    )
            elif intent == "outdoor_activity":
                if cur.rain_probability > 60 or cur.temperature > 38:
                    answer = (
                        f"{loc_name}లో ఈ రోజు బహిరంగ కార్యకలాపాలకు వాతావరణం అంత అనుకూలంగా లేదు. "
                        f"వర్షం అవకాశం {cur.rain_probability}% మరియు ఉష్ణోగ్రత {cur.temperature}°C గా ఉంది. "
                        f"వీలైతే ఇంట్లోనే ఉండండి లేదా ఉదయం లేదా సాయంత్రం తక్కువ వేడిగా ఉండే సమయంలో బయటకు వెళ్ళండి."
                    )
                else:
                    answer = (
                        f"{loc_name}లో ఈ రోజు బహిరంగ కార్యకలాపాలకు వాతావరణం బాగుంది! "
                        f"ఉష్ణోగ్రత {cur.temperature}°C గా ఉండి, గాలి వేగం {cur.wind_speed} కి.మీ/గంటగా ఉంది. "
                        f"వర్షం అవకాశం కేవలం {cur.rain_probability}% మాత్రమే — నడక, వ్యాయామం లేదా క్రీడలకు అనుకూలంగా ఉంది."
                    )
            elif intent == "forecast":
                answer = (
                    f"{loc_name}లో రేపటి వాతావరణ అంచనా: గరిష్ట ఉష్ణోగ్రత {tomorrow.temperature_max}°C, "
                    f"కనిష్ట ఉష్ణోగ్రత {tomorrow.temperature_min}°C గా ఉంటుంది. "
                    f"వర్షం పడే అవకాశం {tomorrow.precipitation_probability_max}% మరియు గాలి వేగం గరిష్టంగా {tomorrow.wind_speed_max} కి.మీ/గంటగా ఉంటుంది. "
                    f"ప్రస్తుతం {cur.condition} వాతావరణం నెలకొని ఉంది."
                )
            elif intent == "comparison":
                answer = (
                    f"{loc_name}లో నేడు మరియు రేపటి వాతావరణ పోలిక: "
                    f"నేడు గరిష్ట ఉష్ణోగ్రత {today.temperature_max if today else cur.temperature}°C, రేపు {tomorrow.temperature_max}°C గా ఉంటుంది. "
                    f"నేడు వర్షం అవకాశం {today.precipitation_probability_max if today else max_pop_24h}%, రేపు {tomorrow.precipitation_probability_max}%. "
                    f"మొత్తంగా రేపటి వాతావరణం {'కొంచెం మెరుగ్గా' if tomorrow.precipitation_probability_max < (today.precipitation_probability_max if today else max_pop_24h) else 'దాదాపు ఒకేలా'} ఉంటుంది."
                )
            else:
                # current_weather — default rich response
                answer = (
                    f"{loc_name}లో ప్రస్తుత వాతావరణం: {cur.condition}. "
                    f"ఉష్ణోగ్రత {cur.temperature}°C (అనుభూతి {cur.apparent_temperature}°C), "
                    f"తేమ శాతం {cur.relative_humidity}%, గాలి వేగం {cur.wind_speed} కి.మీ/గంట. "
                    f"వర్షం పడే అవకాశం {max_pop_24h}% గా ఉంది. "
                    f"నేడు గరిష్ట ఉష్ణోగ్రత {today.temperature_max if today else cur.temperature}°C మరియు UV సూచిక {cur.uv_index} గా నమోదైంది."
                )

            suggested_followups = [
                "రేపు వర్షం పడుతుందా?",
                "గొడుగు అవసరమా?",
                "ఉష్ణోగ్రత ఎంత ఉంటుంది?",
                "బయటకు వెళ్ళవచ్చా?"
            ]

        elif is_hi:
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
            language=norm_lang,
            intent=intent,
            location=target_location,
            weather=weather_summary,
            advisory=top_advisory,
            suggested_followups=suggested_followups,
            is_fallback=weather_data.is_fallback,
            is_location_required=False,
            explicit_override=explicit_override
        )
