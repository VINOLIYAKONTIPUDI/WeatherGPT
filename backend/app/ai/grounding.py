import json
from typing import Any

SYSTEM_PROMPT = (
    "You are WeatherGPT, a meteorological decision-support assistant for India. "
    "Answer ONLY using the provided retrieved weather data JSON. "
    "Never invent temperature, rainfall, forecast, cyclone information, warning severity, "
    "wind speed, or historical statistics. "
    "If a required value is null or missing, say that the data is unavailable. "
    "Clearly separate retrieved facts from advice. Advice must not introduce new numeric weather values. "
    "Respond in the language specified by `language` (en, te, or hi). "
    "If is_demo is true, start the answer with [DEMO DATA]. "
    "Keep answers concise (2–5 sentences)."
)

ADVISORY_DISCLAIMER = (
    "This AI advisory does not replace official agricultural or disaster-management guidance."
)


def build_grounded_user_prompt(
    question: str,
    parsed: dict[str, Any],
    retrieved: dict[str, Any],
) -> str:
    payload = {
        "intent": parsed.get("intent"),
        "language": parsed.get("language"),
        "location_name": retrieved.get("location_name"),
        "date_label": parsed.get("date_label"),
        "is_demo": retrieved.get("is_demo", False),
        "facts": retrieved,
        "advisory_disclaimer": ADVISORY_DISCLAIMER
        if parsed.get("intent") in ("agricultural_advisory", "travel_advisory")
        else None,
    }
    return (
        f"DATA_JSON:\n{json.dumps(payload, default=str)}\n\n"
        f"USER_QUESTION:\n{question}\n"
        "Reply using only facts inside DATA_JSON."
    )


def extract_numeric_facts(retrieved: dict[str, Any]) -> list[str]:
    """Flatten numeric values so tests can assert the LLM cannot invent extras."""
    found: list[str] = []

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            found.append(str(int(obj)) if float(obj).is_integer() else str(obj))

    walk(retrieved)
    return found
