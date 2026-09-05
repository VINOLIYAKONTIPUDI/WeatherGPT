import logging

import httpx

from app.config import get_settings
from app.integrations.llm.base import LLMProvider

logger = logging.getLogger("weathergpt.ai")


class OpenAICompatProvider(LLMProvider):
    name = "openai_compat"

    async def complete(self, system: str, user: str) -> str:
        settings = get_settings()
        if not settings.llm_api_key:
            raise RuntimeError("LLM_API_KEY is not configured")
        payload = {
            "model": settings.llm_model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        logger.info("llm_request provider=%s model=%s", self.name, settings.llm_model)
        async with httpx.AsyncClient(timeout=40) as client:
            resp = await client.post(
                f"{settings.llm_api_base.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
