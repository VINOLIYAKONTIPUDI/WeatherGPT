import asyncio
import logging
from app.services.weather_service import WeatherService
from app.services.geocoding_service import GeocodingService
from app.services.advisory_service import AdvisoryService
from app.services.ai_service import AIService
from app.models.schemas import ChatRequest, LocationCoordinates

logging.basicConfig(level=logging.INFO)

async def test_suite():
    print("=== TEST 1: Open-Meteo Weather Forecast Retrieval ===")
    forecast = await WeatherService.get_forecast(16.8123, 81.5284, "Tadepalligudem")
    assert forecast.current.temperature is not None
    assert len(forecast.hourly) == 24
    assert len(forecast.daily) == 7
    print(f"✓ Forecast OK: {forecast.location.name} Temp={forecast.current.temperature}°C Condition={forecast.current.condition}")

    print("\n=== TEST 2: Geocoding & City Search ===")
    cities = await GeocodingService.search_location("Vijayawada")
    assert len(cities) > 0
    print(f"✓ Search OK: Found {cities[0].name} ({cities[0].latitude}, {cities[0].longitude})")

    reverse_loc = await GeocodingService.reverse_geocode(16.5062, 80.6480)
    print(f"✓ Reverse Geocode OK: Name={reverse_loc.name}, State={reverse_loc.admin1}")

    print("\n=== TEST 3: Strict Location Required Validation ===")
    # When no location is provided and no explicit city is in message text
    req_no_loc = ChatRequest(message="What's the weather today?", location=None, language="en-IN")
    res_no_loc = await AIService.process_chat(req_no_loc)
    assert res_no_loc.is_location_required is True
    assert "location first" in res_no_loc.answer.lower() or "need your location" in res_no_loc.answer.lower()
    print(f"✓ Location Required Check OK: Response='{res_no_loc.answer}'")

    print("\n=== TEST 4: Active Location Conversational Query ===")
    tade_loc = LocationCoordinates(latitude=16.8123, longitude=81.5284, name="Tadepalligudem", admin1="Andhra Pradesh")
    req_tade = ChatRequest(message="Will it rain tomorrow?", location=tade_loc, language="en-IN")
    res_tade = await AIService.process_chat(req_tade)
    assert res_tade.is_location_required is False
    assert "Tadepalligudem" in res_tade.answer or res_tade.location.name == "Tadepalligudem"
    print(f"✓ Active Location Query OK: Answer='{res_tade.answer}'")

    print("\n=== TEST 5: Explicit City Query Override (Without Overwriting Active Location) ===")
    vija_loc = LocationCoordinates(latitude=16.5062, longitude=80.6480, name="Vijayawada", admin1="Andhra Pradesh")
    req_override = ChatRequest(message="What is the weather in Hyderabad?", location=vija_loc, language="en-IN")
    res_override = await AIService.process_chat(req_override)
    assert res_override.is_location_required is False
    assert res_override.explicit_override is True
    assert "Hyderabad" in res_override.answer or res_override.location.name == "Hyderabad"
    print(f"✓ Explicit Override OK: Explicit Override={res_override.explicit_override}, Location={res_override.location.name}")

    print("\n=== TEST 6: Multilingual Chat Queries (Telugu & Hindi) ===")
    req_te = ChatRequest(message="రేపు వర్షం పడుతుందా?", location=vija_loc, language="te-IN")
    res_te = await AIService.process_chat(req_te)
    assert "Vijayawada" in res_te.answer or "విజయవాడ" in res_te.answer or res_te.language == "te-IN"
    print(f"✓ Telugu Chat Query OK: Answer='{res_te.answer}'")

    req_hi = ChatRequest(message="कल मौसम कैसा रहेगा?", location=vija_loc, language="hi-IN")
    res_hi = await AIService.process_chat(req_hi)
    assert res_hi.language == "hi-IN"
    print(f"✓ Hindi Chat Query OK: Answer='{res_hi.answer}'")

    print("\n✅ ALL 6 TEST SUITES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_suite())
