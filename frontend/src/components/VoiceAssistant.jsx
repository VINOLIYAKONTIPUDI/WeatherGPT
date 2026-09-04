import React, { useState, useEffect } from 'react';
import { Mic, Square, Volume2, RotateCcw, Send, AlertTriangle, Sparkles } from 'lucide-react';
import { useVoiceAssistant } from '../hooks/useVoiceAssistant';
import { sendChatMessage } from '../services/api';

const QUICK_QUESTIONS = {
  'en-IN': [
    "Will it rain today?",
    "Do I need an umbrella?",
    "I'm going to college tomorrow morning. Should I carry a raincoat?",
    "How hot will it get this afternoon?",
    "Is it safe to travel tomorrow?",
  ],
  'hi-IN': [
    "क्या आज बारिश होगी?",
    "क्या मुझे छाते की जरूरत है?",
    "कल का मौसम कैसा रहेगा?",
    "आज कितनी गर्मी पड़ेगी?",
    "क्या कल यात्रा करना सुरक्षित है?"
  ],
  'te-IN': [
    "ఈరోజు వర్షం పడుతుందా?",
    "నాకు గొడుగు అవసరమా?",
    "రేపు కళాశాలకు వెళ్లేటప్పుడు వర్షం పడుతుందా?",
    "ఈ మధ్యాహ్నం ఎంత వేడిగా ఉంటుంది?",
    "రేపు ప్రయాణం సురక్షితమేనా?"
  ]
};

export default function VoiceAssistant({ currentLocation, onWeatherUpdate }) {
  const {
    state,
    setState,
    transcript,
    interimTranscript,
    errorMessage,
    language,
    setLanguage,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    replaySpeech,
    clearTranscript,
    resetState
  } = useVoiceAssistant('en-IN');

  const [textInput, setTextInput] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [activeResponse, setActiveResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  // Handle voice transcript when user finishes speaking
  useEffect(() => {
    if (transcript && transcript.trim().length > 0) {
      const q = transcript;
      clearTranscript();
      handleQuerySubmit(q);
    }
  }, [transcript]);

  const handleQuerySubmit = async (queryText) => {
    if (!queryText || !queryText.trim()) return;

    setState('processing');
    setLoading(true);

    try {
      const response = await sendChatMessage(
        queryText,
        currentLocation,
        language,
        chatHistory.slice(-4)
      );

      setActiveResponse(response);
      setChatHistory(prev => [
        ...prev,
        { role: 'user', content: queryText },
        { role: 'assistant', content: response.answer }
      ]);

      if (response.location && onWeatherUpdate) {
        onWeatherUpdate(response.location);
      }

      speak(response.answer, language);
    } catch (err) {
      console.error('Failed to get answer:', err);
      setState('error');
    } finally {
      setLoading(false);
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (textInput.trim()) {
      const q = textInput.trim();
      setTextInput('');
      handleQuerySubmit(q);
    }
  };

  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    resetState();
    if (activeResponse) {
      // Re-trigger query in new language if available
      const lastUserMsg = chatHistory.length > 0 ? chatHistory[chatHistory.length - 2]?.content : null;
      if (lastUserMsg) {
        handleQuerySubmit(lastUserMsg);
      }
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto mb-10">
      {/* Main Hero Card */}
      <div className="glass-card rounded-3xl p-6 sm:p-10 shadow-2xl relative overflow-hidden border border-cyan-500/20">
        {/* Ambient glow */}
        <div className="absolute -top-24 -left-24 w-72 h-72 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-72 h-72 bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" />

        {/* Header & Language Switcher */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-8 relative z-10">
          <div className="text-center sm:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              Voice Intelligence
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-heading">
              Ask WeatherGPT
            </h2>
          </div>

          {/* Multilingual Toggle */}
          <div className="flex items-center bg-dark-900/80 p-1.5 rounded-full border border-slate-700/60 shadow-inner">
            <button
              onClick={() => handleLanguageChange('en-IN')}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                language === 'en-IN'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              English
            </button>
            <button
              onClick={() => handleLanguageChange('hi-IN')}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                language === 'hi-IN'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              हिंदी
            </button>
            <button
              onClick={() => handleLanguageChange('te-IN')}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                language === 'te-IN'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              తెలుగు
            </button>
          </div>
        </div>

        {/* Central Microphone Visual & Controls */}
        <div className="flex flex-col items-center justify-center my-6 relative z-10">
          <div className="relative flex items-center justify-center">
            {state === 'listening' && (
              <>
                <span className="absolute w-36 h-36 rounded-full bg-cyan-500/25 animate-ping pointer-events-none" />
                <span className="absolute w-44 h-44 rounded-full bg-indigo-500/20 animate-pulse pointer-events-none" />
              </>
            )}

            {state === 'speaking' && (
              <span className="absolute w-40 h-40 rounded-full bg-gradient-to-r from-cyan-500/40 to-indigo-500/40 animate-pulse-glow pointer-events-none" />
            )}

            {/* Main Microphone Button */}
            <button
              onClick={state === 'listening' ? stopListening : startListening}
              disabled={state === 'processing'}
              className={`relative w-28 h-28 sm:w-32 sm:h-32 rounded-full flex items-center justify-center transition-all duration-300 transform active:scale-95 shadow-2xl ${
                state === 'listening'
                  ? 'bg-gradient-to-tr from-rose-500 to-red-600 shadow-red-500/50 scale-105'
                  : state === 'speaking'
                  ? 'bg-gradient-to-tr from-indigo-500 to-cyan-500 shadow-cyan-500/50'
                  : state === 'processing'
                  ? 'bg-slate-700 opacity-80 cursor-wait'
                  : 'bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 hover:scale-105 shadow-cyan-500/40'
              }`}
              aria-label="Start voice conversation"
              id="voice-mic-button"
            >
              {state === 'listening' ? (
                <Mic className="w-12 h-12 text-white animate-bounce" />
              ) : state === 'speaking' ? (
                <Volume2 className="w-12 h-12 text-white animate-pulse" />
              ) : state === 'processing' ? (
                <div className="w-10 h-10 border-4 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Mic className="w-12 h-12 text-white" />
              )}
            </button>
          </div>

          {/* Status Indicator */}
          <div className="mt-6 text-center">
            {state === 'idle' && (
              <div>
                <p className="text-lg font-bold text-white tracking-wide">TAP TO SPEAK</p>
                <p className="text-slate-400 text-xs mt-1">Ask me anything about weather</p>
              </div>
            )}

            {state === 'listening' && (
              <div>
                <p className="text-lg font-bold text-cyan-400 tracking-wide animate-pulse">🎙️ Listening...</p>
                <p className="text-slate-300 text-sm mt-1 italic min-h-[24px]">
                  {interimTranscript || transcript || 'Speak your question now...'}
                </p>
              </div>
            )}

            {state === 'processing' && (
              <div>
                <p className="text-lg font-bold text-indigo-400 tracking-wide animate-pulse">Checking latest weather...</p>
                <p className="text-slate-400 text-xs mt-1">Grounding response with Open-Meteo live data</p>
              </div>
            )}

            {state === 'speaking' && (
              <div className="flex flex-col items-center gap-2">
                <p className="text-lg font-bold text-cyan-300 tracking-wide flex items-center gap-2">
                  <Volume2 className="w-5 h-5 animate-pulse" /> WeatherGPT is speaking...
                </p>
                <button
                  onClick={stopSpeaking}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500/20 hover:bg-red-500/30 text-red-300 text-xs border border-red-500/40 transition-all mt-1"
                >
                  <Square className="w-3.5 h-3.5 fill-current" /> Stop Speech
                </button>
              </div>
            )}

            {state === 'error' && (
              <div className="flex flex-col items-center gap-2">
                <p className="text-red-400 text-sm font-semibold flex items-center gap-1">
                  <AlertTriangle className="w-4 h-4" /> {errorMessage || "I couldn't hear that. Try again."}
                </p>
                <button
                  onClick={startListening}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs border border-cyan-500/30 transition-all"
                >
                  <RotateCcw className="w-3.5 h-3.5" /> Retry Voice
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Display Active Response Card */}
        {activeResponse && (
          <div className="mt-6 p-5 rounded-2xl bg-dark-900/90 border border-cyan-500/30 shadow-lg relative z-10 animate-fade-in">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
                <Sparkles className="w-4 h-4" />
                WeatherGPT Answer ({activeResponse.location?.name || 'Selected Area'})
              </div>
              <button
                onClick={replaySpeech}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-cyan-400 text-xs border border-slate-700 flex items-center gap-1 transition-all"
                title="Replay Voice Response"
              >
                <Volume2 className="w-3.5 h-3.5" /> Replay
              </button>
            </div>

            <p className="text-base text-slate-100 font-medium leading-relaxed mb-3">
              "{activeResponse.answer}"
            </p>

            {/* Weather Telemetry Chips */}
            {activeResponse.weather && (
              <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800 text-xs text-slate-300">
                <span className="px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60">
                  🌡️ {activeResponse.weather.temperature}°C (Feels {activeResponse.weather.apparent_temperature}°C)
                </span>
                <span className="px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60">
                  🌧️ Rain Chance: {activeResponse.weather.rain_probability}%
                </span>
                <span className="px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60">
                  💨 Wind: {activeResponse.weather.wind_speed} km/h
                </span>
                <span className="px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60">
                  ☀️ UV Index: {activeResponse.weather.uv_index}
                </span>
              </div>
            )}

            {/* Active Advisory Alert Banner */}
            {activeResponse.advisory && activeResponse.advisory.severity !== 'safe' && (
              <div className="mt-3 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-200 flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-amber-300">{activeResponse.advisory.title}: </span>
                  {activeResponse.advisory.recommendation}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Quick Suggestion Pills */}
        <div className="mt-8 pt-6 border-t border-slate-800/80 relative z-10">
          <p className="text-xs text-slate-400 font-medium mb-3 text-center sm:text-left">
            Suggested Questions:
          </p>
          <div className="flex flex-wrap gap-2 justify-center sm:justify-start">
            {(QUICK_QUESTIONS[language] || QUICK_QUESTIONS['en-IN']).map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleQuerySubmit(q)}
                className="px-3.5 py-2 rounded-xl bg-slate-800/60 hover:bg-cyan-500/15 hover:border-cyan-500/40 border border-slate-700/50 text-slate-300 hover:text-cyan-300 text-xs transition-all text-left"
              >
                "{q}"
              </button>
            ))}
          </div>
        </div>

        {/* Fallback Text Input Bar */}
        <form onSubmit={handleTextSubmit} className="mt-6 flex items-center gap-2 relative z-10">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder={
              language === 'te-IN'
                ? "వాతావరణం గురించి ఇక్కడ టైప్ చేయండి..."
                : language === 'hi-IN'
                ? "मौसम के बारे में प्रश्न टाइप करें..."
                : "Or type your weather question here..."
            }
            className="flex-1 px-4 py-3 rounded-2xl glass-input text-white text-sm focus:outline-none placeholder-slate-500"
          />
          <button
            type="submit"
            disabled={!textInput.trim() || loading}
            className="p-3 rounded-2xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-black font-bold transition-all shadow-md flex items-center justify-center shrink-0"
            aria-label="Send Query"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
