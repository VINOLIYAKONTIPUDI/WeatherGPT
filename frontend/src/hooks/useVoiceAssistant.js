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
          setErrorMessage(
            event.error === 'not-allowed'
              ? 'Microphone permission denied. Please allow microphone access.'
              : `Speech issue (${event.error}). Try again or type below.`
          );
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
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    const voices = synthRef.current.getVoices();
    const langCode = speakLang.split('-')[0];
    
    // Pick matching voice for language code
    const matchingVoice = voices.find(v => v.lang.toLowerCase().replace('_', '-').startsWith(langCode)) ||
                          voices.find(v => v.lang.includes('IN')) ||
                          voices[0];
    if (matchingVoice) {
      utterance.voice = matchingVoice;
    }

    utterance.onstart = () => {
      setState('speaking');
    };

    utterance.onend = () => {
      setState('idle');
    };

    utterance.onerror = (e) => {
      console.warn('SpeechSynthesis error:', e);
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
