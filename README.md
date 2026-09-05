# 🌦️ WeatherGPT — Conversational Voice-First Weather Intelligence Platform

> **Smart India Hackathon (SIH) MVP**  
> WeatherGPT is a voice-first conversational AI weather assistant that translates spoken natural-language queries into structured weather requests, grounds response generation with live **Open-Meteo NWP forecast data**, generates deterministic safety advisories, and synthesizes natural voice responses in **English (`en-IN`)**, **Hindi (`hi-IN`)**, and **Telugu (`te-IN`)**.

---

## 🌟 Key Features

- **🎙️ Voice-First Hero Experience**: Large glowing microphone button with visual audio soundwave animations, instant speech interruption, and audio replay.
- **🌐 Multilingual Indian Language Support**: Full voice & text support for **English (`en-IN`)**, **Hindi (`hi-IN`)**, and **Telugu (`te-IN`)**.
- **🎯 Grounded AI & Zero Hallucination**: AI response generation strictly grounded in actual Open-Meteo weather API data—never invents weather statistics.
- **🛡️ Deterministic Advisory Engine**: Automatic safety alerts for Extreme Heat (≥ 40°C), Heavy Rain, Thunderstorms, High UV Index (≥ 7), Strong Wind, and Travel Suitability.
- **📊 Telemetry Dashboard & Forecast Charts**: 24-hour temperature & rain probability trends powered by Recharts, plus 7-day daily forecast outlooks.
- **🗺️ Interactive Map & Location Search**: Leaflet map integration with debounced city search (Hyderabad, Vijayawada, Delhi, Mumbai, Bengaluru, Tadepalligudem, etc.) and GPS browser geolocation.
- **⚡ Fallback Demo Mode**: Resilient fallback engine ensuring 100% demo reliability even if external APIs or network connections fail during live hackathon judging.

---

## 🏗️ System Architecture

```mermaid
graph TD
    User([🎙️ User Speaks / Types]) -->|Web Speech API| STT[SpeechRecognition en-IN / hi-IN / te-IN]
    STT -->|Transcribed Text| Frontend[React + Vite Frontend]
    Frontend -->|POST /api/chat + Session Context| Backend[FastAPI Backend]
    
    Backend --> IntentParser[NLU Intent & Entity Parser]
    IntentParser -->|Location & Time| GeoService[Geocoding Service Open-Meteo / Nominatim]
    GeoService -->|Lat/Lon Coordinates| WeatherService[Open-Meteo Live Weather API]
    WeatherService -->|Live Forecast Data| WeatherData[(Weather Telemetry)]
    
    WeatherData --> AdvisoryEngine[Deterministic Advisory Engine]
    WeatherData --> ResponseGen[Multilingual Grounded Response Generator]
    AdvisoryEngine --> ResponseGen
    
    ResponseGen -->|Structured JSON + Answer| Frontend
    Frontend -->|Spoken Response| TTS[SpeechSynthesis Voice Output]
    Frontend -->|Visual UI| Dashboard[Voice Hero + Weather Cards + Recharts + Leaflet Map]
    TTS --> UserHear([🔊 User Hears Answer])
```

---

## 🚀 Voice Pipeline Flow

```text
🎙️ USER SPEAKS ("Will I need an umbrella tomorrow morning?")
      ↓
Browser SpeechRecognition (en-IN / hi-IN / te-IN)
      ↓
Transcribed Text
      ↓
FastAPI Backend NLU Intent Parser
      ↓
Structured Query: { intent: "umbrella", location: "Hyderabad", date: "tomorrow" }
      ↓
Open-Meteo Weather API (Live Metric Data)
      ↓
Deterministic Safety & Advisory Engine
      ↓
Grounded Response Generation
      ↓
🔊 Browser SpeechSynthesis Output
```

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS + Custom Glassmorphism Design System
- **Icons**: Lucide React
- **Charts**: Recharts (24h Area & Bar Charts)
- **Map**: React Leaflet + Leaflet 1.9
- **Speech**: Browser Web Speech API (`SpeechRecognition` & `SpeechSynthesis`)

### Backend
- **Framework**: Python 3.14 + FastAPI
- **HTTP Client**: `httpx` (async)
- **Validation**: Pydantic v2
- **Server**: Uvicorn

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status check |
| `GET` | `/api/weather/current` | Get current weather telemetry |
| `GET` | `/api/weather/forecast` | Get 24h hourly and 7-day daily forecast |
| `POST` | `/api/chat` | Process conversational natural language query |
| `GET` | `/api/alerts` | Get active weather safety advisories & warnings |
| `GET` | `/api/location/search` | Search city coordinates |
| `GET` | `/api/location/reverse` | Reverse geocode latitude & longitude |

---

## 💻 Quick Start & Setup Instructions

### Prerequisites
- Node.js ≥ v18
- Python ≥ 3.10

### 1. Clone & Setup Backend
```bash
# Navigate to repository root
cd WeatherGPT

# Create Python virtual environment
python3 -m venv backend/venv
source backend/venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Start FastAPI backend server (Port 8001)
PYTHONPATH=backend python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 2. Setup & Start Frontend
```bash
# In a new terminal tab
cd WeatherGPT/frontend

# Install node dependencies
npm install

# Start Vite dev server (Port 5173)
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 🎬 Hackathon Live Demo Walkthrough

1. **Demo 1 — Voice Question (English)**
   - Click the central microphone button.
   - Say: *"Will I need an umbrella tomorrow morning?"*
   - WeatherGPT speaks back: *"Yes, I'd recommend carrying an umbrella in Hyderabad. There is a 51% chance of rain..."* while displaying live telemetry chips and rain advisories.

2. **Demo 2 — Multilingual Support (Telugu & Hindi)**
   - Toggle language to **తెలుగు** or **हिंदी**.
   - Click a localized suggestion button like *"నాకు గొడుగు అవసరమా?"* or *"क्या मुझे छाते की जरूरत है?"*.
   - WeatherGPT responds in Telugu/Hindi text and voice output.

3. **Demo 3 — Weather Intelligence & Travel Advisory**
   - Ask: *"I'm going to college tomorrow morning. Should I carry a raincoat?"* or *"Is it safe to travel tomorrow?"*.
   - WeatherGPT evaluates rain probability, temperature, wind, and UV index to provide actionable advice.

4. **Demo 4 — Active Safety Advisories**
   - View active high UV radiation, extreme heat, or heavy rain warning banners with explicit safety recommendations.

---

## 📜 License
Developed for Smart India Hackathon. Open source under MIT License.
