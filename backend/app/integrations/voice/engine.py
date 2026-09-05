from abc import ABC, abstractmethod
from typing import Any


class VoiceEngine(ABC):
    @abstractmethod
    async def speech_to_text(self, language: str, transcript_hint: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def text_to_speech(self, text: str, language: str) -> dict[str, Any]:
        raise NotImplementedError


class BrowserVoiceEngine(VoiceEngine):
    """Server-side contract. Browser uses Web Speech API; this returns a mock/pass-through."""

    async def speech_to_text(self, language: str, transcript_hint: str | None = None) -> dict[str, Any]:
        samples = {
            "en": "Will it rain tomorrow in Vijayawada?",
            "te": "రేపు విజయవాడలో వర్షం పడుతుందా?",
            "hi": "क्या कल विजयवाड़ा में बारिश होगी?",
        }
        text = transcript_hint or samples.get(language, samples["en"])
        return {
            "text": text,
            "language": language,
            "engine": "demo/browser-speech",
            "is_demo": transcript_hint is None,
            "note": "Use the browser microphone for live STT. This endpoint echoes text or a labelled demo phrase.",
        }

    async def text_to_speech(self, text: str, language: str) -> dict[str, Any]:
        return {
            "text": text,
            "language": language,
            "engine": "browser-speech-synthesis",
            "audio_url": None,
            "is_demo": False,
            "note": "Frontend should speak this text via SpeechSynthesisUtterance.",
        }
