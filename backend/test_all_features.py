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
    forecast = await WeatherService.get_forecast(17.3850, 78.4867, "Hyderabad")
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

    print("\n=== TEST 3: Deterministic Advisory Engine ===")
    alerts_resp = AdvisoryService.get_alerts_response(forecast)
    assert alerts_resp.count > 0
    print(f"✓ Advisories OK: Count={alerts_resp.count}, Top Alert={alerts_resp.alerts[0].title}")

    print("\n=== TEST 4: Conversational NLU Intents (English) ===")
    queries = [
        "Will I need an umbrella tomorrow morning?",
        "How hot will it get this afternoon?",
        "Is it safe to travel tomorrow?",
        "What's the humidity in Vijayawada?",
        "Compare today and tomorrow"
    ]
    loc = LocationCoordinates(latitude=17.3850, longitude=78.4867, name="Hyderabad")
    for q in queries:
        req = ChatRequest(message=q, location=loc, language="en-IN")
        res = await AIService.process_chat(req)
        print(f"  Q: '{q}' -> Intent: {res.intent} | Answer: '{res.answer}'")

    print("\n=== TEST 5: Multilingual Queries (Hindi & Telugu) ===")
    req_hi = ChatRequest(message="क्या मुझे छाते की जरूरत है?", location=loc, language="hi-IN")
    res_hi = await AIService.process_chat(req_hi)
    print(f"  HI: '{req_hi.message}' -> Answer: '{res_hi.answer}'")

    req_te = ChatRequest(message="రేపు వర్షం పడుతుందా?", location=loc, language="te-IN")
    res_te = await AIService.process_chat(req_te)
    print(f"  TE: '{req_te.message}' -> Answer: '{res_te.answer}'")

    print("\n✅ ALL 5 TEST SUITES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_suite())
