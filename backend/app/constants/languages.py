"""
Centralized Multilingual Configuration & Language Code Mapping
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Standard Indian Language TTS Codes
TTS_LANGUAGE_CODES: Dict[str, str] = {
    "te": "te-IN",
    "te-in": "te-IN",
    "telugu": "te-IN",
    "hi": "hi-IN",
    "hi-in": "hi-IN",
    "hindi": "hi-IN",
    "ta": "ta-IN",
    "ta-in": "ta-IN",
    "tamil": "ta-IN",
    "mr": "mr-IN",
    "mr-in": "mr-IN",
    "marathi": "mr-IN",
    "bn": "bn-IN",
    "bn-in": "bn-IN",
    "bengali": "bn-IN",
    "kn": "kn-IN",
    "kn-in": "kn-IN",
    "kannada": "kn-IN",
    "ml": "ml-IN",
    "ml-in": "ml-IN",
    "malayalam": "ml-IN",
    "gu": "gu-IN",
    "gu-in": "gu-IN",
    "gujarati": "gu-IN",
    "pa": "pa-IN",
    "pa-in": "pa-IN",
    "punjabi": "pa-IN",
    "or": "or-IN",
    "or-in": "or-IN",
    "odia": "or-IN",
    "en": "en-IN",
    "en-in": "en-IN",
    "en-us": "en-US",
    "english": "en-IN",
}

LANGUAGE_NAMES: Dict[str, str] = {
    "te-IN": "Telugu",
    "te": "Telugu",
    "hi-IN": "Hindi",
    "hi": "Hindi",
    "ta-IN": "Tamil",
    "ta": "Tamil",
    "mr-IN": "Marathi",
    "mr": "Marathi",
    "bn-IN": "Bengali",
    "bn": "Bengali",
    "kn-IN": "Kannada",
    "kn": "Kannada",
    "ml-IN": "Malayalam",
    "ml": "Malayalam",
    "gu-IN": "Gujarati",
    "gu": "Gujarati",
    "pa-IN": "Punjabi",
    "pa": "Punjabi",
    "or-IN": "Odia",
    "or": "Odia",
    "en-IN": "English",
    "en": "English",
}

def normalize_language_code(lang_input: Optional[str]) -> str:
    """
    Normalizes any language string (e.g. 'Telugu', 'te', 'te-IN', 'TE') to standard TTS code (e.g. 'te-IN').
    Never silently defaults to English if a valid non-English code is provided.
    """
    if not lang_input:
        return "en-IN"
    
    cleaned = lang_input.strip().lower()
    
    # Direct match in lookup table
    if cleaned in TTS_LANGUAGE_CODES:
        return TTS_LANGUAGE_CODES[cleaned]
    
    # Prefix matches
    if cleaned.startswith("te"):
        return "te-IN"
    if cleaned.startswith("hi"):
        return "hi-IN"
    if cleaned.startswith("ta"):
        return "ta-IN"
    if cleaned.startswith("mr"):
        return "mr-IN"
    if cleaned.startswith("bn"):
        return "bn-IN"
    if cleaned.startswith("kn"):
        return "kn-IN"
    if cleaned.startswith("ml"):
        return "ml-IN"
    if cleaned.startswith("gu"):
        return "gu-IN"
    if cleaned.startswith("pa"):
        return "pa-IN"
    if cleaned.startswith("or"):
        return "or-IN"
    if cleaned.startswith("en"):
        return "en-IN"
        
    return lang_input

def get_language_name(lang_input: Optional[str]) -> str:
    """
    Returns the human-readable language name for prompt/system instructions (e.g. 'Telugu').
    """
    code = normalize_language_code(lang_input)
    return LANGUAGE_NAMES.get(code, LANGUAGE_NAMES.get(code.split("-")[0], "English"))

LOCATION_REQUIRED_RESPONSES = {
    "en-IN": "📍 I need your location first to give you accurate weather information.\n\nPlease select 'Use My Location' or search for a city above.",
    "hi-IN": "📍 सटीक मौसम जानकारी देने के लिए मुझे आपका स्थान चाहिए।\n\nकृपया 'मेरे स्थान का उपयोग करें' चुनें या ऊपर शहर खोजें।",
    "te-IN": "📍 ఖచ్చితమైన వాతావరణ సమాచారం అందించడానికి మీ స్థానాన్ని తెలుసుకోవాలి.\n\nదయచేసి 'నా ప్రదేశాన్ని ఉపయోగించండి' ఎంచుకోండి లేదా పైన నగరాన్ని శోధించండి.",
    "ta-IN": "📍 துல்லியமான வானிலை தகவலை வழங்க உங்கள் இருப்பிடம் தேவை.\n\nதயவுசெய்து மேலே உள்ள 'என் இருப்பிடத்தைப் பயன்படுத்து' என்பதைத் தேர்ந்தெடுக்கவும்.",
    "mr-IN": "📍 अचूक हवामानाची माहिती देण्यासाठी मला तुमच्या स्थानाची माहिती हवी आहे.\n\nकृपया 'माझे स्थान वापरा' निवडा.",
    "bn-IN": "📍 সঠিক আবহাওয়ার তথ্যের জন্য আপনার অবস্থান প্রয়োজন।\n\nঅনুগ্রহ করে 'আমার অবস্থান ব্যবহার করুন' নির্বাচন করুন।",
}

def get_location_required_message(lang_code: str) -> str:
    normalized = normalize_language_code(lang_code)
    if normalized in LOCATION_REQUIRED_RESPONSES:
        return LOCATION_REQUIRED_RESPONSES[normalized]
    if normalized.startswith("te"):
        return LOCATION_REQUIRED_RESPONSES["te-IN"]
    if normalized.startswith("hi"):
        return LOCATION_REQUIRED_RESPONSES["hi-IN"]
    return LOCATION_REQUIRED_RESPONSES["en-IN"]
