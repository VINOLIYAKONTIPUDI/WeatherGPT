from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

INTENTS = (
    "current_weather",
    "forecast",
    "rainfall",
    "temperature",
    "wind",
    "humidity",
    "severe_weather",
    "historical_weather",
    "climate_trend",
    "agricultural_advisory",
    "travel_advisory",
    "disaster_information",
    "general_weather_question",
)

SIMPLE_INTENTS = {"current_weather", "temperature", "humidity", "wind", "rainfall"}

TELUGU_HINTS = re.compile(r"[\u0C00-\u0C7F]")
HINDI_HINTS = re.compile(r"[\u0900-\u097F]")

LOCATION_STOP = {
    "will", "it", "the", "in", "at", "for", "me", "my", "near", "today", "tomorrow",
    "weekend", "weather", "rain", "temperature", "wind", "what", "whats", "how's",
    "how", "is", "there", "any", "safe", "travel", "please", "tell",
}


@dataclass
class ParsedQuery:
    intent: str
    location_text: str | None
    date_label: str
    target_date: date | None
    language: str
    parameters: list[str] = field(default_factory=list)
    needs_llm: bool = False
    raw: str = ""
    confidence: float = 0.6


def detect_language(text: str, fallback: str = "en") -> str:
    if TELUGU_HINTS.search(text):
        return "te"
    if HINDI_HINTS.search(text):
        return "hi"
    return fallback


def _relative_date(text: str) -> tuple[str, date | None]:
    low = text.lower()
    today = date.today()
    if any(w in low for w in ["tomorrow", "రేపు", "कल"]):
        return "tomorrow", today + timedelta(days=1)
    if any(w in low for w in ["today", "ఈరోజు", "आज", "ఇప్పుడు"]):
        return "today", today
    if "weekend" in low or "వారాంతం" in low or "सप्ताहांत" in low:
        # upcoming Saturday
        days = (5 - today.weekday()) % 7
        return "weekend", today + timedelta(days=days or 6)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return d.isoformat(), d
    return "unspecified", None


def _extract_location(text: str, hint: str | None) -> str | None:
    if hint:
        return hint
    m = re.search(r"\b(?:in|at|near)\s+([A-Za-z][A-Za-z\s]{2,40})", text, re.I)
    if m:
        loc = m.group(1).strip(" ?.,!")
        parts = [p for p in loc.split() if p.lower() not in LOCATION_STOP]
        if parts:
            return " ".join(parts[:3])
    # Telugu/Hindi often include place names in Latin or native; keep hint-only fallback
    known = ["Vijayawada", "Hyderabad", "Visakhapatnam", "Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru"]
    for city in known:
        if city.lower() in text.lower() or city in text:
            return city
    if "విజయవాడ" in text:
        return "Vijayawada"
    if "हैदराबाद" in text or "హైదరాబాద్" in text:
        return "Hyderabad"
    return None


def parse_weather_query(text: str, language: str | None = None, location_hint: str | None = None) -> ParsedQuery:
    lang = detect_language(text, language or "en")
    low = text.lower()
    date_label, target = _relative_date(text)
    location = _extract_location(text, location_hint)

    intent = "general_weather_question"
    params = ["temperature", "condition"]
    needs_llm = True

    spray = any(w in low for w in ["spray", "pesticide", "పురుగుమందు", "कीटनाशक", "sow", "irrigation"])
    travel = any(w in low for w in ["travel", "safe to travel", "ప్రయాణం", "यात्रा"])
    severe = any(
        w in low
        for w in ["cyclone", "flood", "warning", "alert", "severe", "thunder", "lightning", "heatwave", "హెచ్చరిక", "चेतावनी"]
    )
    climate = any(w in low for w in ["climate", "trend", "decade", "historical average"])
    historical = any(w in low for w in ["last year", "historical", "in 20", "past decade"])

    if spray:
        intent = "agricultural_advisory"
        params = ["rain_probability", "wind_speed", "humidity", "temperature"]
    elif travel:
        intent = "travel_advisory"
        params = ["rain_probability", "wind_speed", "alerts", "condition"]
    elif severe:
        intent = "severe_weather" if "cyclone" not in low and "flood" not in low else "disaster_information"
        params = ["alerts", "wind_speed", "rainfall"]
    elif climate:
        intent = "climate_trend"
        params = ["rainfall", "temperature"]
    elif historical:
        intent = "historical_weather"
        params = ["temperature", "rainfall"]
    elif any(w in low for w in ["rain", "rainfall", "వర్షం", "बारिश", "precip"]):
        intent = "rainfall" if date_label in ("today", "unspecified") and "tomorrow" not in low else "forecast"
        if date_label == "tomorrow" or "forecast" in low:
            intent = "forecast"
        params = ["rain_probability", "rainfall", "temperature"]
        needs_llm = date_label not in ("today",) or "will" in low or "పడుతుందా" in text or "होगी" in text
    elif any(w in low for w in ["humidity", "తేమ", "नमी"]):
        intent = "humidity"
        params = ["humidity"]
        needs_llm = False
    elif any(w in low for w in ["wind", "గాలి", "हवा"]):
        intent = "wind"
        params = ["wind_speed", "wind_direction"]
        needs_llm = False
    elif any(w in low for w in ["temperature", "temp", "hot", "cold", "ఉష్ణోగ్రత", "तापमान"]):
        intent = "temperature"
        params = ["temperature"]
        needs_llm = date_label not in ("today", "unspecified") or "weekend" in low
    elif any(w in low for w in ["current", "now", "right now", "what's the weather", "weather today", "వాతావరణం"]):
        intent = "current_weather"
        params = ["temperature", "condition", "humidity", "wind_speed"]
        needs_llm = lang != "en"
    elif any(w in low for w in ["forecast", "7 day", "week"]):
        intent = "forecast"
        params = ["temperature", "rain_probability", "condition"]

    # Cost rule: simple factual current queries skip LLM when English
    if intent in SIMPLE_INTENTS and date_label in ("today", "unspecified") and lang == "en" and not spray and not travel:
        if not any(w in low for w in ["explain", "should i", "advise", "safe"]):
            needs_llm = False

    if lang != "en" and intent not in SIMPLE_INTENTS:
        needs_llm = True
    if lang != "en" and ("?" in text or "పడుతుందా" in text or "क्या" in text):
        needs_llm = True

    return ParsedQuery(
        intent=intent,
        location_text=location,
        date_label=date_label,
        target_date=target,
        language=lang,
        parameters=params,
        needs_llm=needs_llm,
        raw=text,
        confidence=0.75,
    )


def format_simple_answer(parsed: ParsedQuery, facts: dict[str, Any], location_name: str) -> str:
    demo = "[DEMO DATA] " if facts.get("is_demo") else ""
    current = facts.get("current") or facts
    tomorrow = facts.get("tomorrow") or {}

    src = tomorrow if parsed.date_label == "tomorrow" and tomorrow else current
    t_val = src.get("temperature") or src.get("temp_max") or current.get("temperature", 28)
    t_min = src.get("temp_min") or current.get("temperature", 20)
    pop_val = src.get("rain_probability") or current.get("rain_probability", 20)
    precip_val = src.get("rainfall") or current.get("precipitation", 0.0)
    wind_val = src.get("wind_speed") or current.get("wind_speed", 10)
    humidity_val = src.get("humidity") or current.get("humidity", 60)
    is_tom = parsed.date_label == "tomorrow"
    raw_low = parsed.raw.lower()

    is_cold_q = any(w in raw_low for w in ["cold", "cool", "ठंड", "ठंडी", "సర్దీ", "చల్లగా", "చలి"])
    is_umbrella_q = any(w in raw_low for w in ["umbrella", "raincoat", "छाता", "గొడుగు"])
    is_travel_q = any(w in raw_low for w in ["travel", "trip", "यात्रा", "ప్రయాణం"])

    lang = parsed.language

    if lang == "te":
        if is_cold_q:
            if float(t_val) < 20:
                return f"{demo}అవును, {location_name}లో చల్లగా ఉంటుంది. ఉష్ణోగ్రత సుమారు {t_val}°C గా ఉంటుంది."
            return f"{demo}లేదు, {location_name}లో {'రేపు ' if is_tom else ''}చల్లగా ఉండే అవకాశం లేదు. ఉష్ణోగ్రత సుమారు {t_val}°C ఉంటుంది, కాబట్టి వాతావరణం వెచ్చగా అనిపించవచ్చు."
        if is_umbrella_q:
            if float(pop_max_val := pop_val or 0) >= 45:
                return f"{demo}అవును, {location_name}లో {'రేపు ' if is_tom else ''}గొడుగు లేదా రెయిన్‌కోట్ తీసుకెళ్లడం మంచిది. {pop_max_val}% వర్షం పడే అవకాశం ఉంది."
            return f"{demo}లేదు, {location_name}లో {'రేపు ' if is_tom else ''}గొడుగు అవసరం లేదు. వర్షం పడే అవకాశం కేవలం {pop_val}% మాత్రమే ఉంది."
        if is_travel_q:
            if float(pop_val or 0) >= 65 or float(t_val) >= 39:
                return f"{demo}{location_name}కు ప్రయాణం చేసేటప్పుడు జాగ్రత్త వహించండి. వర్ష సూచన {pop_val}% మరియు ఉష్ణోగ్రత {t_val}°C."
            return f"{demo}అవును, {location_name}లో {'రేపు ' if is_tom else ''}ప్రయాణం చేయడానికి వాతావరణం చాలా అనుకూలంగా ఉంది! ఉష్ణోగ్రత సుమారు {t_val}°C ఉంటుంది."
        return f"{demo}{location_name}లో ప్రస్తుతం ఉష్ణోగ్రత {current.get('temperature', 28)}°C, గాలి తేమ {humidity_val}%, మరియు వర్ష సూచన {pop_val}%."

    elif lang == "hi":
        if is_cold_q:
            if float(t_val) < 20:
                return f"{demo}हां, {location_name} में मौसम ठंडा रहेगा। तापमान लगभग {t_val}°C रहने की संभावना है।"
            return f"{demo}नहीं, {location_name} में {'कल ' if is_tom else ''}ठंड होने की संभावना नहीं है। तापमान लगभग {t_val}°C रहेगा, इसलिए मौसम गर्म महसूस हो सकता है।"
        if is_umbrella_q:
            if float(pop_val or 0) >= 45:
                return f"{demo}हां, कल {location_name} में छाता या रेनकोट साथ रखना बेहतर रहेगा। बारिश की {pop_val}% संभावना है।"
            return f"{demo}नहीं, कल {location_name} में छाते की आवश्यकता नहीं है। बारिश की संभावना केवल {pop_val}% है।"
        if is_travel_q:
            if float(pop_val or 0) >= 65 or float(t_val) >= 39:
                return f"{demo}{location_name} की यात्रा में सावधानी बरतें। बारिश की संभावना ({pop_val}%) और तापमान {t_val}°C रहेगा।"
            return f"{demo}हां, कल {location_name} में यात्रा करना बिल्कुल ठीक रहेगा! मौसम सुहावना रहेगा और तापमान लगभग {t_val}°C रहेगा।"
        return f"{demo}{location_name} में वर्तमान तापमान {current.get('temperature', 28)}°C, नमी {humidity_val}% और बारिश की संभावना {pop_val}% है।"

    else:
        if is_cold_q:
            if float(t_val) < 20:
                return f"{demo}Yes, it will be cold in {location_name}{' tomorrow' if is_tom else ''}. Temperatures will be around {t_val}°C."
            return f"{demo}No, {'tomorrow is' if is_tom else 'it is'} not expected to be cold in {location_name}. The temperature will be around {t_val}°C, so it will feel warm."
        if is_umbrella_q:
            if float(pop_val or 0) >= 45:
                return f"{demo}Yes, I recommend carrying an umbrella in {location_name}{' tomorrow' if is_tom else ''}. There is a {pop_val}% chance of rain."
            return f"{demo}No umbrella needed in {location_name}{' tomorrow' if is_tom else ''}. Rain probability is low at only {pop_val}%."
        if is_travel_q:
            if float(pop_val or 0) >= 65 or float(t_val) >= 39:
                return f"{demo}Travel caution advised for {location_name}: High rain probability ({pop_val}%) and temperatures around {t_val}°C."
            return f"{demo}Yes, {'tomorrow' if is_tom else 'it'} is great for travelling in {location_name}! Expect pleasant weather with a high of {t_val}°C."
        return f"{demo}Current weather in {location_name}: {current.get('temperature', 28)}°C, humidity {humidity_val}%, wind {wind_val} km/h."

