import asyncio
import logging
from app.models.schemas import ChatRequest, LocationCoordinates
from app.services.ai_service import AIService

logging.basicConfig(level=logging.INFO)

TEST_LOCATION = LocationCoordinates(
    latitude=16.54,
    longitude=81.52,
    name="Chinamiram",
    city="Chinamiram",
    country="India"
)

TEST_QUESTIONS = [
    # CURRENT
    ("What is the weather now?", "en-IN"),
    ("Is it raining now?", "en-IN"),

    # YESTERDAY
    ("What was the weather yesterday?", "en-IN"),
    ("What was yesterday's temperature?", "en-IN"),
    ("Did it rain yesterday?", "en-IN"),
    ("How humid was yesterday?", "en-IN"),
    ("How windy was yesterday?", "en-IN"),

    # DAY BEFORE YESTERDAY
    ("How was the weather day before yesterday?", "en-IN"),
    ("Did it rain the day before yesterday?", "en-IN"),

    # SPECIFIC TIME
    ("What was the temperature yesterday morning?", "en-IN"),
    ("What was the temperature yesterday at 6 PM?", "en-IN"),

    # TOMORROW
    ("What will the weather be tomorrow?", "en-IN"),
    ("Will it rain tomorrow?", "en-IN"),

    # DAY AFTER TOMORROW
    ("What will the weather be the day after tomorrow?", "en-IN"),

    # NEXT WEEK / NEXT DAYS
    ("What will the weather be next week?", "en-IN"),
    ("What will the weather be next Sunday?", "en-IN"),
    ("What will the weather be next Monday?", "en-IN"),

    # COMPARISONS
    ("Was yesterday hotter than today?", "en-IN"),
    ("Will tomorrow be hotter than today?", "en-IN"),

    # MULTILINGUAL
    ("निन्न वातावरणम एला उंदि?", "te-IN"),
    ("निन्न वर्षम पडिंदा?", "te-IN"),
    ("कल मौसम कैसा था?", "hi-IN"),
]

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='replace').decode('ascii'))

async def run_tests():
    safe_print("\n" + "="*80)
    safe_print("  RUNNING WEATHER QUERY INTELLIGENCE VERIFICATION TESTS")
    safe_print("="*80 + "\n")
    
    passed = 0
    failed = 0

    for idx, (q, lang) in enumerate(TEST_QUESTIONS, 1):
        req = ChatRequest(
            message=q,
            language=lang,
            location=TEST_LOCATION
        )
        try:
            res = await AIService.process_chat(req)
            safe_print(f"[{idx:02d}] Q: '{q}' ({lang})")
            safe_print(f"     Intent: {res.intent} | Resolved Date: {res.weather.get('resolved_label')} ({res.weather.get('requested_date')})")
            safe_print(f"     A: '{res.answer}'\n")
            passed += 1
        except Exception as e:
            safe_print(f"[{idx:02d}] FAILED: '{q}' -> Error: {e}\n")
            failed += 1

    safe_print("="*80)
    safe_print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED OUT OF {len(TEST_QUESTIONS)} TESTS.")
    safe_print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
