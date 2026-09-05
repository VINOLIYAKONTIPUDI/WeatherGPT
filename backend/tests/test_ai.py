from datetime import date

from app.ai.grounding import SYSTEM_PROMPT, build_grounded_user_prompt
from app.ai.parser import parse_weather_query
from app.integrations.llm.demo import DemoLLMProvider
from app.services.historical_weather_service import HistoricalWeatherService


def test_parser_telugu_rain():
    p = parse_weather_query("రేపు విజయవాడలో వర్షం పడుతుందా?")
    assert p.language == "te"
    assert p.location_text == "Vijayawada"
    assert p.date_label == "tomorrow"


def test_parser_simple_temp_skips_llm():
    p = parse_weather_query("What is the current temperature?")
    assert p.intent == "temperature"
    assert p.needs_llm is False


def test_grounded_prompt_contains_retrieved_only():
    parsed = parse_weather_query("Will it rain tomorrow?")
    retrieved = {
        "location_name": "Vijayawada",
        "temperature": 29,
        "rain_probability": 80,
        "rainfall": 18,
        "wind_speed": 15,
        "is_demo": False,
        "source": "open-meteo",
    }
    prompt = build_grounded_user_prompt("Will it rain tomorrow?", parsed.__dict__, retrieved)
    assert "80" in prompt
    assert "29" in prompt
    assert "Never invent" in SYSTEM_PROMPT or "only using" in SYSTEM_PROMPT.lower() or "ONLY" in SYSTEM_PROMPT


async def _demo_complete():
    llm = DemoLLMProvider()
    retrieved = {
        "location_name": "Vijayawada",
        "intent": "rainfall",
        "language": "en",
        "facts": {"rain_probability": 80, "temperature": 29, "rainfall": 18, "wind_speed": 15},
        "temperature": 29,
        "rain_probability": 80,
        "rainfall": 18,
        "wind_speed": 15,
        "is_demo": True,
    }
    parsed = {"intent": "rainfall", "language": "en", "date_label": "tomorrow"}
    user = build_grounded_user_prompt("Will it rain tomorrow?", parsed, retrieved)
    text = await llm.complete(SYSTEM_PROMPT, user)
    assert "80" in text
    assert "29" in text
    # Must not invent a cyclone category or extra rainfall number like 250mm
    assert "250" not in text
    assert "category 5" not in text.lower()


def test_demo_llm_does_not_invent_values():
    import asyncio

    asyncio.get_event_loop().run_until_complete(_demo_complete())


def test_historical_stats_are_calculated_not_llm():
    rows = [
        {"date": "2000-01-01", "rainfall": 10, "is_demo": True},
        {"date": "2012-01-01", "rainfall": 20, "is_demo": True},
    ]
    stats = HistoricalWeatherService().statistics(rows, "rainfall")
    assert stats["mean"] == 15
    assert stats["change_pct"] == 100.0
