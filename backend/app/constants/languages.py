"""
Centralized Backend Multilingual Configuration & Response Templates
"""
from typing import Dict, Any

LANGUAGES = {
    "en": {"name": "English", "code": "en-IN"},
    "hi": {"name": "Hindi", "code": "hi-IN"},
    "te": {"name": "Telugu", "code": "te-IN"},
    "ta": {"name": "Tamil", "code": "ta-IN"},
    "kn": {"name": "Kannada", "code": "kn-IN"},
    "ml": {"name": "Malayalam", "code": "ml-IN"},
    "mr": {"name": "Marathi", "code": "mr-IN"},
    "bn": {"name": "Bengali", "code": "bn-IN"},
    "or": {"name": "Odia", "code": "or-IN"},
    "pa": {"name": "Punjabi", "code": "pa-IN"},
    "gu": {"name": "Gujarati", "code": "gu-IN"},
}

LOCATION_REQUIRED_RESPONSES = {
    "en-IN": "📍 I need your location first to give you accurate weather information.\n\nPlease select 'Use My Location' or search for a city above.",
    "en": "📍 I need your location first to give you accurate weather information.\n\nPlease select 'Use My Location' or search for a city above.",
    "hi-IN": "📍 सटीक मौसम जानकारी देने के लिए मुझे आपका स्थान चाहिए।\n\nकृपया 'मेरे स्थान का उपयोग करें' चुनें या ऊपर शहर खोजें।",
    "hi": "📍 सटीक मौसम जानकारी देने के लिए मुझे आपका स्थान चाहिए।\n\nकृपया 'मेरे स्थान का उपयोग करें' चुनें या ऊपर शहर खोजें।",
    "te-IN": "📍 ఖచ్చితమైన వాతావరణ సమాచారం అందించడానికి మీ స్థానాన్ని తెలుసుకోవాలి.\n\nదయచేసి 'నా ప్రదేశాన్ని ఉపయోగించండి' ఎంచుకోండి లేదా పైన నగరాన్ని శోధించండి.",
    "te": "📍 ఖచ్చితమైన వాతావరణ సమాచారం అందించడానికి మీ స్థానాన్ని తెలుసుకోవాలి.\n\nదయచేసి 'నా ప్రదేశాన్ని ఉపయోగించండి' ఎంచుకోండి లేదా పైన నగరాన్ని శోధించండి.",
}

def get_location_required_message(lang_code: str) -> str:
    cleaned = (lang_code or "en-IN").strip()
    if cleaned in LOCATION_REQUIRED_RESPONSES:
        return LOCATION_REQUIRED_RESPONSES[cleaned]
    if cleaned.startswith("te"):
        return LOCATION_REQUIRED_RESPONSES["te-IN"]
    if cleaned.startswith("hi"):
        return LOCATION_REQUIRED_RESPONSES["hi-IN"]
    return LOCATION_REQUIRED_RESPONSES["en-IN"]
