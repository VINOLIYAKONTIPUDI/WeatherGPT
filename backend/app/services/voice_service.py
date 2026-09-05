from app.integrations.voice.engine import BrowserVoiceEngine


class VoiceService:
    def __init__(self) -> None:
        self.engine = BrowserVoiceEngine()

    async def transcribe(self, language: str, hint: str | None) -> dict:
        return await self.engine.speech_to_text(language, hint)

    async def speak(self, text: str, language: str) -> dict:
        return await self.engine.text_to_speech(text, language)
