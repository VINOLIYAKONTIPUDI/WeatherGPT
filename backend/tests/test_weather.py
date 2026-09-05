import pytest

from app.ai.parser import parse_weather_query
from app.integrations.weather.demo import DemoWeatherProvider
from app.services.forecast_service import ForecastService
from app.services.weather_service import WeatherService


@pytest.mark.asyncio
async def test_demo_current_weather_labelled():
    w = WeatherService(DemoWeatherProvider())
    data = await w.current(16.5, 80.6)
    assert data["is_demo"] is True
    assert data["temperature"] == 29.0
    assert "DEMO" in data["source"]


@pytest.mark.asyncio
async def test_forecast_tomorrow_rain():
    f = ForecastService(WeatherService(DemoWeatherProvider()))
    from datetime import date, timedelta

    row = await f.for_date(16.5, 80.6, date.today() + timedelta(days=1))
    assert row is not None
    assert row["rain_probability"] == 80
    assert row["rainfall"] == 18.0


def test_location_parse_vijayawada():
    p = parse_weather_query("Will it rain tomorrow in Vijayawada?")
    assert p.location_text == "Vijayawada"
    assert p.date_label == "tomorrow"
    assert p.intent in ("forecast", "rainfall")
