// Centralized Multilingual Configuration & UI Strings for WeatherGPT

export const LANGUAGES = {
  'en-IN': { code: 'en-IN', shortCode: 'en', name: 'English', nativeName: 'English', speechLang: 'en-IN' },
  'hi-IN': { code: 'hi-IN', shortCode: 'hi', name: 'Hindi', nativeName: 'हिन्दी', speechLang: 'hi-IN' },
  'te-IN': { code: 'te-IN', shortCode: 'te', name: 'Telugu', nativeName: 'తెలుగు', speechLang: 'te-IN' },
  'ta-IN': { code: 'ta-IN', shortCode: 'ta', name: 'Tamil', nativeName: 'தமிழ்', speechLang: 'ta-IN' },
  'kn-IN': { code: 'kn-IN', shortCode: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', speechLang: 'kn-IN' },
  'ml-IN': { code: 'ml-IN', shortCode: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', speechLang: 'ml-IN' },
  'mr-IN': { code: 'mr-IN', shortCode: 'mr', name: 'Marathi', nativeName: 'मराठी', speechLang: 'mr-IN' },
  'bn-IN': { code: 'bn-IN', shortCode: 'bn', name: 'Bengali', nativeName: 'বাংলা', speechLang: 'bn-IN' },
  'or-IN': { code: 'or-IN', shortCode: 'or', name: 'Odia', nativeName: 'ଓଡ଼ିଆ', speechLang: 'or-IN' },
  'pa-IN': { code: 'pa-IN', shortCode: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', speechLang: 'pa-IN' },
  'gu-IN': { code: 'gu-IN', shortCode: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', speechLang: 'gu-IN' },
};

export const PRIMARY_LANGUAGES = ['en-IN', 'hi-IN', 'te-IN'];

export const UI_TRANSLATIONS = {
  'en-IN': {
    locationRequiredTitle: "📍 Location Required",
    locationRequiredMessage: "I need your location first to give you accurate weather information.",
    useMyLocation: "📍 Use My Location",
    searchLocation: "🔎 Search Location",
    searchPlaceholder: "Search city, town, village, or area (e.g. Vijayawada, Tadepalligudem)...",
    locationNotSet: "📍 Location not set",
    setLocation: "Set Location",
    changeLocation: "Change Location",
    tapToSpeak: "TAP TO SPEAK",
    askAnything: "Ask me anything about weather",
    listening: "🎙️ Listening...",
    checkingWeather: "Checking latest weather...",
    typePlaceholder: "Or type your weather question here...",
    demoWarning: "⚠️ Live weather temporarily unavailable. Showing demo forecast.",
    quickQuestions: [
      "Will it rain today?",
      "Do I need an umbrella?",
      "I'm going to college tomorrow morning. Should I carry a raincoat?",
      "How hot will it get this afternoon?",
      "Is it safe to travel tomorrow?"
    ]
  },
  'hi-IN': {
    locationRequiredTitle: "📍 स्थान आवश्यक है",
    locationRequiredMessage: "सटीक मौसम जानकारी देने के लिए मुझे आपका स्थान चाहिए।",
    useMyLocation: "📍 मेरे स्थान का उपयोग करें",
    searchLocation: "🔎 स्थान खोजें",
    searchPlaceholder: "शहर, गांव या क्षेत्र खोजें (जैसे विजयवाड़ा, ताडेपल्लीगुडेम)...",
    locationNotSet: "📍 स्थान सेट नहीं है",
    setLocation: "स्थान सेट करें",
    changeLocation: "स्थान बदलें",
    tapToSpeak: "बोलने के लिए टैप करें",
    askAnything: "मौसम के बारे में कुछ भी पूछें",
    listening: "🎙️ सुन रहा हूँ...",
    checkingWeather: "मौसम की जानकारी प्राप्त की जा रही है...",
    typePlaceholder: "मौसम के बारे में अपना प्रश्न यहाँ टाइप करें...",
    demoWarning: "⚠️ लाइव मौसम अस्थायी रूप से अनुपलब्ध है। डेमो पूर्वानुमान दिखाया जा रहा है।",
    quickQuestions: [
      "क्या आज बारिश होगी?",
      "क्या मुझे छाते की जरूरत है?",
      "कल का मौसम कैसा रहेगा?",
      "आज कितनी गर्मी पड़ेगी?",
      "क्या कल यात्रा करना सुरक्षित है?"
    ]
  },
  'te-IN': {
    locationRequiredTitle: "📍 స్థానం వివరాలు అవసరం",
    locationRequiredMessage: "ఖచ్చితమైన వాతావరణ సమాచారం అందించడానికి మీ స్థానాన్ని తెలుసుకోవాలి.",
    useMyLocation: "📍 నా ప్రదేశాన్ని ఉపయోగించండి",
    searchLocation: "🔎 స్థానాన్ని శోధించండి",
    searchPlaceholder: "నగరం, గ్రామం లేదా ప్రాంతాన్ని శోధించండి (ఉదా. విజయవాడ, తాడేపల్లిగూడెం)...",
    locationNotSet: "📍 స్థానం అమర్చబడలేదు",
    setLocation: "స్థానాన్ని అమర్చండి",
    changeLocation: "స్థానాన్ని మార్చండి",
    tapToSpeak: "మాట్లాడటానికి నొక్కండి",
    askAnything: "వాతావరణం గురించి ఏదైనా అడగండి",
    listening: "🎙️ వింటున్నాను...",
    checkingWeather: "వాతావరణ సమాచారాన్ని పొందుపరుస్తున్నాము...",
    typePlaceholder: "వాతావరణం గురించి మీ ప్రశ్నను ఇక్కడ టైప్ చేయండి...",
    demoWarning: "⚠️ ప్రత్యక్ష వాతావరణ సమాచారం తాత్కాలికంగా అందుబాటులో లేదు. డెమో అంచనా చూపిస్తున్నాము.",
    quickQuestions: [
      "ఈరోజు వర్షం పడుతుందా?",
      "నాకు గొడుగు అవసరమా?",
      "రేపు కళాశాలకు వెళ్లేటప్పుడు వర్షం పడుతుందా?",
      "ఈ మధ్యాహ్నం ఎంత వేడిగా ఉంటుంది?",
      "రేపు ప్రయాణం సురక్షితమేనా?"
    ]
  },
  'ta-IN': {
    locationRequiredTitle: "📍 இருப்பிடம் தேவை",
    locationRequiredMessage: "துல்லியமான வானிலை தகவலை வழங்க உங்கள் இருப்பிடம் தேவை.",
    useMyLocation: "📍 என் இருப்பிடத்தைப் பயன்படுத்து",
    searchLocation: "🔎 இருப்பிடத்தைத் தேடு",
    searchPlaceholder: "நகரம் அல்லது பகுதியைத் தேடவும்...",
    locationNotSet: "📍 இருப்பிடம் அமைக்கப்படவில்லை",
    setLocation: "இருப்பிடத்தை அமை",
    changeLocation: "இருப்பிடத்தை மாற்று",
    tapToSpeak: "பேச தட்டவும்",
    askAnything: "வானிலை பற்றி எதுவும் கேளுங்கள்",
    listening: "🎙️ கேட்கிறது...",
    checkingWeather: "வானிலை தகவலைப் பெறுகிறது...",
    typePlaceholder: "உங்கள் கேள்வியை தட்டச்சு செய்க...",
    quickQuestions: ["இன்று மழை பெய்யுமா?", "எனக்கு குடை தேவையா?", "நாளை வானிலை எப்படி இருக்கும்?"]
  },
  'kn-IN': {
    locationRequiredTitle: "📍 ಸ್ಥಳದ ವಿವರ ಅಗತ್ಯವಿದೆ",
    locationRequiredMessage: "ನಿಖರವಾದ ಹವಾಮಾನ ಮಾಹಿತಿಯನ್ನು ನೀಡಲು ನಿಮ್ಮ ಸ್ಥಳದ ವಿವರಗಳು ಬೇಕು.",
    useMyLocation: "📍 ನನ್ನ ಸ್ಥಳ ಬಳಸಿ",
    searchLocation: "🔎 ಸ್ಥಳ ಹುಡುಕಿ",
    searchPlaceholder: "ನಗರ ಅಥವಾ ಪ್ರದೇಶ ಹುಡುಕಿ...",
    locationNotSet: "📍 ಸ್ಥಳ ಹೊಂದಿಸಿಲ್ಲ",
    setLocation: "ಸ್ಥಳ ಹೊಂದಿಸಿ",
    changeLocation: "ಸ್ಥಳ ಬದಲಾಯಿಸಿ",
    tapToSpeak: "ಮಾತನಾಡಲು ಸ್ಪರ್ಶಿಸಿ",
    askAnything: "ಹವಾಮಾನದ ಬಗ್ಗೆ ಕೇಳಿ",
    listening: "🎙️ ಆಲಿಸಲಾಗುತ್ತಿದೆ...",
    checkingWeather: "ಹವಾಮಾನ ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...",
    typePlaceholder: "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ...",
    quickQuestions: ["ಇಂದು ಮಳೆ ಬರುತ್ತದೆಯೇ?", "ನನಗೆ ಛತ್ರಿ ಬೇಕೇ?", "ನಾಳೆ ವಾತಾವರಣ ಹೇಗಿರುತ್ತದೆ?"]
  }
};

export function getTranslation(langCode, key) {
  const langKey = LANGUAGES[langCode] ? langCode : (langCode?.startsWith('te') ? 'te-IN' : (langCode?.startsWith('hi') ? 'hi-IN' : 'en-IN'));
  return UI_TRANSLATIONS[langKey]?.[key] || UI_TRANSLATIONS['en-IN']?.[key] || '';
}
