import { useState, useEffect, useRef, useCallback } from 'react';

export function useVoiceAssistant(defaultLanguage = 'en-IN') {
  const [state, setState] = useState('idle'); // 'idle' | 'listening' | 'processing' | 'speaking' | 'error'
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [lastResponseText, setLastResponseText] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [language, setLanguage] = useState(defaultLanguage);
  const [hasSpeechSupport, setHasSpeechSupport] = useState(true);

  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis || null);

  // Initialize SpeechRecognition
  useEffect(() => {
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
              : `Speech recognition issue (${event.error}). Try again or type below.`
          );
          setState('error');
        } else {
          setState('idle');
        }
      };

      recognition.onend = () => {
        // Will transition to 'processing' externally if transcript exists
      };

      recognitionRef.current = recognition;
    } catch (err) {
      console.error('Failed to initialize SpeechRecognition:', err);
      setHasSpeechSupport(false);
    }
  }, [language]);

  // Start Voice Recording
  const startListening = useCallback(() => {
    // Stop any ongoing speech output first
    if (synthRef.current && synthRef.current.speaking) {
      synthRef.current.cancel();
    }

    if (!recognitionRef.current) {
      setErrorMessage('Speech recognition is not supported in this browser. Please use Chrome/Edge or type your question.');
      setState('error');
      return;
    }

    try {
      recognitionRef.current.lang = language;
      recognitionRef.current.start();
    } catch (err) {
      console.warn('Recognition start exception, retrying:', err);
      try {
        recognitionRef.current.stop();
        setTimeout(() => recognitionRef.current.start(), 200);
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

  // Text-To-Speech (Speech Synthesis)
  const speak = useCallback((text, speakLang = language) => {
    if (!synthRef.current || !text) {
      setState('idle');
      return;
    }

    setLastResponseText(text);
    synthRef.current.cancel(); // Stop any active speech

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = speakLang;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    // Pick best matching voice if available
    const voices = synthRef.current.getVoices();
    const matchingVoice = voices.find(v => v.lang.startsWith(speakLang.slice(0, 2))) ||
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
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    replaySpeech,
    resetState: () => {
      setState('idle');
      setTranscript('');
      setInterimTranscript('');
      setErrorMessage('');
    }
  };
}
