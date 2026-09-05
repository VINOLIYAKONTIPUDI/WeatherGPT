import { useState, useEffect, useRef, useCallback } from 'react';

export function useVoiceAssistant(defaultLanguage = 'en-IN') {
  const [state, setState] = useState('idle'); // 'idle' | 'listening' | 'processing' | 'speaking' | 'error'
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [lastResponseText, setLastResponseText] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [language, setLanguage] = useState(defaultLanguage);
  const [hasSpeechSupport, setHasSpeechSupport] = useState(true);
  const [availableVoices, setAvailableVoices] = useState([]);

  const recognitionRef = useRef(null);
  const synthRef = useRef(typeof window !== 'undefined' ? window.speechSynthesis : null);

  // Load available speech synthesis voices
  useEffect(() => {
    if (!synthRef.current) return;
    
    const updateVoices = () => {
      const v = synthRef.current.getVoices();
      if (v && v.length > 0) {
        setAvailableVoices(v);
      }
    };

    updateVoices();
    if (synthRef.current.onvoiceschanged !== undefined) {
      synthRef.current.onvoiceschanged = updateVoices;
    }
  }, []);

  // Initialize SpeechRecognition instance
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setHasSpeechSupport(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = language;

      recognition.onstart = () => {
        setState('listening');
        setErrorMessage('');
        setTranscript('');
        setInterimTranscript('');
      };

      recognition.onresult = (event) => {
        let final = '';
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const trans = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            final += trans;
          } else {
            interim += trans;
          }
        }
        if (final) setTranscript(final);
        setInterimTranscript(interim);
      };

      recognition.onerror = (event) => {
        console.warn('SpeechRecognition error:', event.error);
        if (event.error !== 'no-speech') {
          let msg = `Speech issue (${event.error}). Try again or type below.`;
          if (event.error === 'not-allowed') {
            msg = 'Microphone permission denied. Please allow microphone access in browser settings.';
          } else if (event.error === 'network') {
            msg = 'Network error: Browser speech recognition service is blocked or offline. Check internet connection or Brave/Chrome settings (Enable Google Speech Services).';
          }
          setErrorMessage(msg);
          setState('error');
        } else {
          setState('idle');
        }
      };

      recognition.onend = () => {
        // Voice input ended
      };

      recognitionRef.current = recognition;
    } catch (err) {
      console.error('Failed to initialize SpeechRecognition:', err);
      setHasSpeechSupport(false);
    }
  }, [language]);

  // Start Voice Recording
  const startListening = useCallback(() => {
    if (synthRef.current && synthRef.current.speaking) {
      synthRef.current.cancel();
    }

    if (!recognitionRef.current) {
      setErrorMessage('Speech recognition is not supported in this browser mode. Please type your question.');
      setState('error');
      return;
    }

    try {
      recognitionRef.current.lang = language;
      recognitionRef.current.start();
    } catch (err) {
      console.warn('Recognition start exception, resetting:', err);
      try {
        recognitionRef.current.stop();
        setTimeout(() => recognitionRef.current && recognitionRef.current.start(), 200);
      } catch (e) {
        setState('idle');
      }
    }
  }, [language]);

  // Stop Listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // ignore
      }
    }
  }, []);

  // Text-To-Speech Output
  const speak = useCallback((text, speakLang = language) => {
    if (!synthRef.current || !text) {
      setState('idle');
      return;
    }

    setLastResponseText(text);
    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = speakLang;
    utterance.rate = 0.95; // Slightly slower for clear regional pronunciation
    utterance.pitch = 1.0;

    const voices = synthRef.current.getVoices();
    const langCode = speakLang.split('-')[0].toLowerCase();
    const fullCode = speakLang.toLowerCase().replace('_', '-');
    
    // Strict voice search for requested language
    let matchingVoice = voices.find(v => v.lang.toLowerCase().replace('_', '-') === fullCode) ||
                        voices.find(v => v.lang.toLowerCase().replace('_', '-').startsWith(langCode));

    // Secondary search by language name if BCP code tag differs
    if (!matchingVoice) {
      if (langCode === 'te') {
        matchingVoice = voices.find(v => v.name.toLowerCase().includes('telugu') || v.name.includes('తెలుగు'));
      } else if (langCode === 'hi') {
        matchingVoice = voices.find(v => v.name.toLowerCase().includes('hindi') || v.name.includes('हिन्दी'));
      } else if (langCode === 'ta') {
        matchingVoice = voices.find(v => v.name.toLowerCase().includes('tamil') || v.name.includes('தமிழ்'));
      }
    }

    // IMPORTANT: If no native voice for this language is found, DO NOT set an English voice!
    // Leaving utterance.voice unset allows Chrome / Edge to use their online/native synthesizer for utterance.lang.
    if (matchingVoice) {
      utterance.voice = matchingVoice;
      console.log(`[TTS Service] 🔊 Using matching voice '${matchingVoice.name}' (${matchingVoice.lang}) for language: ${speakLang}`);
    } else {
      console.log(`[TTS Service] 🔊 No dedicated local voice found for '${speakLang}'. Relying on browser engine with lang='${speakLang}'.`);
    }

    utterance.onstart = () => {
      console.log(`[TTS Service] ▶️ Started speaking response in ${speakLang}`);
      setState('speaking');
    };

    utterance.onend = () => {
      console.log(`[TTS Service] ⏹️ Finished speaking in ${speakLang}`);
      setState('idle');
    };

    utterance.onerror = (e) => {
      console.warn(`[TTS Service] ⚠️ SpeechSynthesis error for ${speakLang}:`, e);
      setState('idle');
    };

    synthRef.current.speak(utterance);
  }, [language]);

  // Stop Speech Output
  const stopSpeaking = useCallback(() => {
    if (synthRef.current) {
      synthRef.current.cancel();
    }
    setState('idle');
  }, []);

  // Replay Last Response
  const replaySpeech = useCallback(() => {
    if (lastResponseText) {
      speak(lastResponseText, language);
    }
  }, [lastResponseText, language, speak]);

  const clearTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
  }, []);

  return {
    state,
    setState,
    transcript,
    interimTranscript,
    lastResponseText,
    errorMessage,
    language,
    setLanguage,
    hasSpeechSupport,
    availableVoices,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    replaySpeech,
    clearTranscript,
    resetState: () => {
      setState('idle');
      setTranscript('');
      setInterimTranscript('');
      setErrorMessage('');
    }
  };
}
