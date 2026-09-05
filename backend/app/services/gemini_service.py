"""
WeatherGPT — Python Gemini Service
Direct integration with Google Generative AI (Gemini 2.5 / 1.5 Flash)
Enforces strict model-level system_instruction for Telugu and Indian languages.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
from dotenv import load_dotenv
from app.constants.languages import normalize_language_code, get_language_name

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_ID = "gemini-2.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent"

class GeminiService:
    @staticmethod
    def build_system_instruction(language_name: str) -> str:
        """
        Builds the model-level system instruction enforcing strict native language output.
        """
        return (
            f"You are WeatherGPT, a multilingual voice-first weather assistant.\n\n"
            f"ABSOLUTE STRICT CONSTRAINT — NEVER VIOLATE THIS RULE:\n"
            f"• Respond entirely in {language_name}, using native {language_name} script only, no English mixed in.\n"
            f"• Every single word, sentence, number, unit, and alert MUST be written in {language_name}.\n"
            f"• If language is Telugu, write ONLY in Telugu script (తెలుగు) — NEVER use transliteration or Latin characters.\n"
            f"• If language is Hindi, write ONLY in Devanagari script (हिंदी).\n"
            f"• If language is Tamil, write ONLY in Tamil script (தமிழ்).\n"
            f"• If language is Marathi, write ONLY in Marathi script (मराठी).\n"
            f"• If language is Bengali, write ONLY in Bengali script (বাংলা).\n"
            f"• Do NOT include English translations, English subtitles, or parenthetical English words.\n"
            f"• Deliver a warm, helpful, natural 3 to 4 sentence conversational response.\n"
            f"• Rely solely on the provided weather forecast context."
        )

    @classmethod
    async def generate_response(
        cls,
        user_query: str,
        weather_context: Dict[str, Any],
        language_code: str
    ) -> Optional[str]:
        """
        Calls the Gemini REST endpoint with system_instruction and returns the generated text.
        """
        normalized_code = normalize_language_code(language_code)
        language_name = get_language_name(normalized_code)

        logger.info(f"[GeminiService] 🤖 Invoking Gemini API for language: '{language_code}' -> Normalized: '{normalized_code}' ({language_name})")

        api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
        if not api_key or api_key.strip() == "" or api_key.strip() == "your_gemini_api_key_here":
            logger.warning(f"[GeminiService] ⚠️ GEMINI_API_KEY is not set or placeholder. Falling back to local native {language_name} generator.")
            return None

        system_instruction_text = cls.build_system_instruction(language_name)
        logger.info(f"[GeminiService] 📜 System Instruction applied for {language_name}:\n{system_instruction_text}")

        prompt = (
            f"WEATHER DATA CONTEXT:\n{json.dumps(weather_context, indent=2)}\n\n"
            f"USER QUERY: {user_query}\n\n"
            f"Please respond to the user in {language_name} using native {language_name} script only."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [
                    {"text": system_instruction_text}
                ]
            },
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 600
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{API_URL}?key={api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        if parts:
                            ans = parts[0].get("text", "").strip()
                            logger.info(f"[GeminiService] ✅ Received Gemini response in {language_name}: {ans[:100]}...")
                            return ans
                else:
                    logger.error(f"[GeminiService] ❌ Gemini API returned error {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"[GeminiService] ❌ Exception during Gemini call: {e}")

        return None
