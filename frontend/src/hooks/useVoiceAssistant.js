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
  const [hasNativeVoice, setHasNativeVoice] = useState(true);

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

  // Check if native voice is available for active language (e.g. te-IN, hi-IN, en-IN)
  useEffect(() => {
    if (!synthRef.current) return;
    const voices = availableVoices.length > 0 ? availableVoices : synthRef.current.getVoices();
    if (!voices || voices.length === 0) return;

    const langPrefix = language.split('-')[0].toLowerCase();
    const found = voices.some(v => 
      v.lang.toLowerCase().replace('_', '-').startsWith(language.toLowerCase()) ||
      v.lang.toLowerCase().replace('_', '-').startsWith(langPrefix) ||
      v.name.toLowerCase().includes(langPrefix === 'te' ? 'telugu' : (langPrefix === 'hi' ? 'hindi' : 'english'))
    );
    setHasNativeVoice(found);
  }, [language, availableVoices]);

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

  const chunksRef = useRef([]);
  const chunkIndexRef = useRef(0);
  const isCancelledRef = useRef(false);

  // Helper to split text into natural speech chunks
  const splitTextIntoChunks = (text) => {
    if (!text) return [];
    const cleaned = text.replace(/\*\*/g, '').trim();
    if (!cleaned) return [];

    const sentences = cleaned.split(/(?<=[.!?|।\n])\s+/);
    const chunks = [];

    for (const s of sentences) {
      const trimmed = s.trim();
      if (!trimmed) continue;

      if (trimmed.length > 120) {
        const parts = trimmed.split(/(?<=[,;])\s+/);
        for (const p of parts) {
          if (p.trim()) chunks.push(p.trim());
        }
      } else {
        chunks.push(trimmed);
      }
    }

    return chunks.length > 0 ? chunks : [cleaned];
  };

  // Stop Speech Output & Clear Queue
  const stopSpeaking = useCallback(() => {
    isCancelledRef.current = true;
    if (synthRef.current) {
      synthRef.current.cancel();
    }
    chunksRef.current = [];
    chunkIndexRef.current = 0;
    setState('idle');
  }, []);

  // Text-To-Speech Output (Sequential Chunks)
  const speak = useCallback((text, speakLang = language) => {
    if (!synthRef.current || !text) {
      setState('idle');
      return;
    }

    setLastResponseText(text);
    
    // Stop ongoing speech & reset flags
    stopSpeaking();
    isCancelledRef.current = false;

    const chunks = splitTextIntoChunks(text);
    if (chunks.length === 0) {
      setState('idle');
      return;
    }

    chunksRef.current = chunks;
    chunkIndexRef.current = 0;

    const voices = synthRef.current.getVoices();
    const langPrefix = speakLang.split('-')[0].toLowerCase();
    
    // Pick matching voice for language code (Telugu, Hindi, English)
    const matchingVoice = voices.find(v => v.lang.toLowerCase().replace('_', '-').startsWith(speakLang.toLowerCase())) ||
                          voices.find(v => v.lang.toLowerCase().replace('_', '-').startsWith(langPrefix)) ||
                          voices.find(v => v.name.toLowerCase().includes(langPrefix === 'te' ? 'telugu' : (langPrefix === 'hi' ? 'hindi' : 'english'))) ||
                          voices.find(v => v.lang.includes('IN')) ||
                          voices[0];

    const speakNextChunk = () => {
      if (isCancelledRef.current) return;

      if (chunkIndexRef.current >= chunksRef.current.length) {
        setState('idle');
        return;
      }

      const chunkText = chunksRef.current[chunkIndexRef.current];
      chunkIndexRef.current += 1;

      const utterance = new SpeechSynthesisUtterance(chunkText);
      utterance.lang = speakLang;
      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      if (matchingVoice) {
        utterance.voice = matchingVoice;
      }

      utterance.onstart = () => {
        if (!isCancelledRef.current) {
          setState('speaking');
        }
      };

      utterance.onend = () => {
        if (!isCancelledRef.current) {
          speakNextChunk();
        }
      };

      utterance.onerror = (e) => {
        console.warn('SpeechSynthesis chunk error:', e);
        if (!isCancelledRef.current) {
          speakNextChunk();
        }
      };

      synthRef.current.speak(utterance);
    };

    speakNextChunk();
  }, [language, stopSpeaking]);

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
    hasNativeVoice,
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
