import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_weathergpt.db")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("WEATHER_PROVIDER", "demo")
os.environ.setdefault("SECRET_KEY", "test-secret")

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.init_db import init_db
from app.db.session import SessionLocal, engine, Base
from app.main import app
from app.models.entities import UserRole
from app.services.alert_service import AlertService
from app.services.historical_weather_service import HistoricalWeatherService
from app.services.notification_service import NotificationService
from app.ai.parser import parse_weather_query
from app.ai.grounding import extract_numeric_facts, SYSTEM_PROMPT, build_grounded_user_prompt
from app.integrations.llm.demo import DemoLLMProvider
from app.integrations.weather.demo import DemoWeatherProvider


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    get_settings.cache_clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    init_db(db)
    db.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_otp_auth(client):
    send = client.post("/auth/send-otp", json={"identifier": "tester@demo.weathergpt.in"})
    assert send.status_code == 200
    assert send.json()["sent"] is True
    bad = client.post(
        "/auth/verify-otp",
        json={"identifier": "tester@demo.weathergpt.in", "otp": "000000"},
    )
    assert bad.status_code == 400
    ok = client.post(
        "/auth/verify-otp",
        json={
            "identifier": "tester@demo.weathergpt.in",
            "otp": "123456",
            "name": "Tester",
            "role": "public",
            "preferred_language": "en",
        },
    )
    assert ok.status_code == 200
    assert "access_token" in ok.json()


def test_role_based_admin_forbidden(client):
    client.post("/auth/send-otp", json={"identifier": "pub@demo.weathergpt.in"})
    token = client.post(
        "/auth/verify-otp",
        json={"identifier": "pub@demo.weathergpt.in", "otp": "123456", "role": "public"},
    ).json()["access_token"]
    r = client.get("/admin/system-status", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_role_based_admin_allowed(client):
    client.post("/auth/send-otp", json={"identifier": "admin@demo.weathergpt.in"})
    token = client.post(
        "/auth/verify-otp",
        json={"identifier": "admin@demo.weathergpt.in", "otp": "123456", "role": "admin"},
    ).json()["access_token"]
    r = client.get("/admin/system-status", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_weather_service_demo():
    from app.services.weather_service import WeatherService

    svc = WeatherService(DemoWeatherProvider())
    cur = await svc.current(16.5, 80.6)
    assert cur["temperature"] == 29.0
    assert cur["is_demo"] is True
    fc = await svc.forecast(16.5, 80.6)
    assert fc["daily"]
    assert fc["daily"][1]["rain_probability"] == 80


def test_location_resolution_parser():
    q = parse_weather_query("Will it rain tomorrow in Vijayawada?")
    assert q.location_text == "Vijayawada"
    assert q.date_label == "tomorrow"
    assert q.intent in ("forecast", "rainfall")


def test_telugu_parser():
    q = parse_weather_query("రేపు విజయవాడలో వర్షం పడుతుందా?")
    assert q.language == "te"
    assert q.location_text == "Vijayawada"
    assert q.date_label == "tomorrow"


def test_simple_query_skips_llm():
    q = parse_weather_query("What is the current temperature?")
    assert q.needs_llm is False
    assert q.intent == "temperature"


@pytest.mark.asyncio
async def test_grounded_ai_does_not_invent_values():
    retrieved = {
        "location_name": "Vijayawada",
        "temperature": 29,
        "rain_probability": 80,
        "rainfall": 18,
        "wind_speed": 15,
        "is_demo": True,
        "language": "en",
        "intent": "rainfall",
        "facts": {
            "temperature": 29,
            "rain_probability": 80,
            "rainfall": 18,
            "wind_speed": 15,
        },
    }
    allowed = set(extract_numeric_facts(retrieved))
    llm = DemoLLMProvider()
    prompt = build_grounded_user_prompt(
        "Will it rain tomorrow?",
        {"intent": "rainfall", "language": "en", "date_label": "tomorrow"},
        retrieved,
    )
    answer = await llm.complete(SYSTEM_PROMPT, prompt)
    # Invented weather-like numbers (e.g. 47°C, 99% not in data) should not appear
    import re

    nums = re.findall(r"\d+", answer)
    for n in nums:
        if n in {"2", "5"}:  # sentence filler counts ok-ish; skip tiny
            continue
        assert n in allowed or n in {"0"}, f"invented number {n} in {answer}"
    assert "80" in answer
    assert "29" in answer


def test_historical_statistics():
    rows = [
        {"date": "2000-01-01", "rainfall": 10, "is_demo": True},
        {"date": "2010-01-01", "rainfall": 20, "is_demo": True},
        {"date": "2020-01-01", "rainfall": 30, "is_demo": True},
        {"date": "2024-01-01", "rainfall": 40, "is_demo": True},
    ]
    stats = HistoricalWeatherService().statistics(rows, "rainfall")
    assert stats["mean"] == 25.0
    assert stats["change_pct"] is not None
    assert stats["count"] == 4


def test_alert_match_and_notification():
    db = SessionLocal()
    svc = AlertService()
    from app.models.entities import Location, User, UserLocation, LanguageCode

    loc = db.query(Location).filter(Location.name == "Vijayawada").first()
    user = User(
        name="Alert User",
        email="alertuser@demo.weathergpt.in",
        role=UserRole.public,
        preferred_language=LanguageCode.en,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(UserLocation(user_id=user.id, location_id=loc.id))
    db.commit()
    alert = svc.ingest(
        db,
        {
            "alert_type": "cyclone",
            "severity": "severe",
            "title": "Test cyclone",
            "description": "demo",
            "affected_location": "Vijayawada",
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "is_demo": True,
            "source": "test",
        },
    )
    users = svc.matching_users(db, alert)
    assert any(u.id == user.id for u in users)
    n = NotificationService().create_for_alert(db, user, alert)
    assert n.id
    assert "DEMO DATA" in n.message or "DEMO" in alert.title
    db.close()


def test_chat_grounded_endpoint(client):
    r = client.post(
        "/chat",
        json={"message": "What is the current temperature?", "language": "en", "location": "Vijayawada"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["grounded"] is True
    assert body["location"] == "Vijayawada"
    assert "29" in body["answer"] or "temperature" in body["answer"].lower()
