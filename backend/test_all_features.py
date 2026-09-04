import asyncio
import logging
from app.services.weather_service import WeatherService
from app.services.geocoding_service import GeocodingService
from app.services.advisory_service import AdvisoryService
from app.services.ai_service import AIService
from app.models.schemas import ChatRequest, LocationCoordinates

logging.basicConfig(level=logging.INFO)

async def test_suite():
    print("=== TEST 1: Location Required State (No Location Provided) ===")
    req_no_loc = ChatRequest(message="What's the weather today?", location=None, language="en-IN")
    res_no_loc = await AIService.process_chat(req_no_loc)
    assert res_no_loc.is_location_required is True
    assert "location" in res_no_loc.answer.lower()
    print(f"✓ Location Required OK: Answer='{res_no_loc.answer[:60]}...'")

    print("\n=== TEST 2: Active Saved Location (Tadepalligudem) ===")
    tade_loc = LocationCoordinates(latitude=16.8123, longitude=81.5284, city="Tadepalligudem", name="Tadepalligudem", country="India", admin1="Andhra Pradesh")
    forecast = await WeatherService.get_forecast(tade_loc.latitude, tade_loc.longitude, tade_loc.city)
    assert forecast.current.temperature is not None
    print(f"✓ Forecast OK: {forecast.location.name} Temp={forecast.current.temperature}°C Condition={forecast.current.condition}")

    print("\n=== TEST 3: Conversational Queries for Active Location (Tadepalligudem) ===")
    queries = [
        "Will it rain tomorrow?",
        "What about tomorrow evening?",
        "How hot will it be?"
    ]
    for q in queries:
        req = ChatRequest(message=q, location=tade_loc, language="en-IN")
        res = await AIService.process_chat(req)
        assert res.is_location_required is False
        assert "Tadepalligudem" in res.answer
        print(f"  Q: '{q}' -> Location: {res.location.name} | Answer: '{res.answer}'")

    print("\n=== TEST 4: Explicit Location Override (Vijayawada active, query for Hyderabad) ===")
    vija_loc = LocationCoordinates(latitude=16.5062, longitude=80.6480, city="Vijayawada", name="Vijayawada", country="India", admin1="Andhra Pradesh")
    req_override = ChatRequest(message="What is the weather in Hyderabad?", location=vija_loc, language="en-IN")
    res_override = await AIService.process_chat(req_override)
    assert res_override.explicit_override is True
    assert res_override.location.name == "Hyderabad"
    print(f"✓ Override OK: Answered for {res_override.location.name} | explicit_override={res_override.explicit_override}")

    print("\n=== TEST 5: Multilingual Location Required & Weather Queries ===")
    req_te_noloc = ChatRequest(message="ఈరోజు వాతావరణం ఎలా ఉంది?", location=None, language="te-IN")
    res_te_noloc = await AIService.process_chat(req_te_noloc)
    assert res_te_noloc.is_location_required is True
    print(f"  TE No-Loc: '{res_te_noloc.answer[:60]}...'")

    req_te = ChatRequest(message="రేపు వర్షం పడుతుందా?", location=vija_loc, language="te-IN")
    res_te = await AIService.process_chat(req_te)
    assert "Vijayawada" in res_te.answer or "విజయవాడ" in res_te.answer
    print(f"  TE With Loc: '{res_te.answer}'")

    req_hi = ChatRequest(message="क्या कल बारिश होगी?", location=vija_loc, language="hi-IN")
    res_hi = await AIService.process_chat(req_hi)
    assert "Vijayawada" in res_hi.answer
    print(f"  HI With Loc: '{res_hi.answer}'")

    print("\n✅ ALL ACCEPTANCE TEST SUITES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_suite())
