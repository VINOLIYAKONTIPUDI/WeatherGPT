import asyncio
import logging
from app.models.schemas import ChatRequest, LocationCoordinates
from app.services.ai_service import AIService

logging.basicConfig(level=logging.INFO)

ACTIVE_LOCATION = LocationCoordinates(
    latitude=16.54,
    longitude=81.52,
    name="Chinamiram",
    city="Chinamiram",
    country="India"
)

TEST_FLOW = [
    ("What is the weather?", "en-IN", "Chinamiram"),
    ("What will it be tomorrow?", "en-IN", "Chinamiram"),
    ("What was the weather yesterday?", "en-IN", "Chinamiram"),
    ("What was yesterday's temperature?", "en-IN", "Chinamiram"),
    ("Did it rain yesterday?", "en-IN", "Chinamiram"),
    ("How humid was yesterday?", "en-IN", "Chinamiram"),
    ("What was the weather day before yesterday?", "en-IN", "Chinamiram"),
    ("What will it be next Sunday?", "en-IN", "Chinamiram"),
    ("What will it be next Monday?", "en-IN", "Chinamiram"),
    ("How was last week?", "en-IN", "Chinamiram"),
    ("What will next week be like?", "en-IN", "Chinamiram"),
    ("Was yesterday hotter than today?", "en-IN", "Chinamiram"),
    ("What was yesterday morning's temperature?", "en-IN", "Chinamiram"),
    ("What is the weather in Hyderabad?", "en-IN", "Hyderabad"), # Explicit override
    ("What about tomorrow?", "en-IN", "Chinamiram"), # Reverts to active location
]

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='replace').decode('ascii'))

async def run_tests():
    safe_print("\n" + "="*80)
    safe_print("  WEATHER INTELLIGENCE & ACTIVE LOCATION VERIFICATION SUITE")
    safe_print("="*80 + "\n")
    
    passed = 0
    failed = 0

    for idx, (q, lang, expected_city) in enumerate(TEST_FLOW, 1):
        req = ChatRequest(
            message=q,
            language=lang,
            location=ACTIVE_LOCATION
        )
        try:
            res = await AIService.process_chat(req)
            actual_loc = res.location.city or res.location.name if res.location else "None"
            date_label = res.weather.get('resolved_label', 'N/A') if res.weather else 'N/A'
            req_date = res.weather.get('requested_date', 'N/A') if res.weather else 'N/A'
            
            loc_match = expected_city.lower() in actual_loc.lower() or actual_loc.lower() in expected_city.lower()
            status = "PASSED" if loc_match else "FAILED (LOCATION MISMATCH)"

            if loc_match:
                passed += 1
            else:
                failed += 1

            safe_print(f"[{idx:02d}] Q: '{q}'")
            safe_print(f"     Expected Loc: {expected_city} | Actual Loc: {actual_loc} [{status}]")
            safe_print(f"     Resolved Date: {date_label} ({req_date})")
            safe_print(f"     A: '{res.answer}'\n")

        except Exception as e:
            safe_print(f"[{idx:02d}] FAILED: '{q}' -> Error: {e}\n")
            failed += 1

    safe_print("="*80)
    safe_print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED OUT OF {len(TEST_FLOW)} TESTS.")
    safe_print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
