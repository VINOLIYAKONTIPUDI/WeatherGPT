import asyncio
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.services.sms_service import SMSService

async def test_sms_broadcast():
    print("=== TEST 1: Emergency SMS Broadcast (Thunderstorm & Flash Flood Hazard) ===")
    test_phones = ["+917993678737", "+919959051684"]
    res = await SMSService.dispatch_emergency_broadcast(
        phone_numbers=test_phones,
        alert_type="Severe Thunderstorm & Lightning Warning",
        location_name="Vijayawada, Andhra Pradesh",
        recommendation="Seek immediate indoor shelter. Avoid open fields, metal structures, and tall trees.",
        severity="DANGER"
    )
    assert res["success"] is True
    assert res["recipient_count"] == 2
    assert "THUNDERSTORM" in res["message_preview"]
    print(f"  [OK] SMS Broadcast Dispatched: Count={res['recipient_count']} Mode={res['broadcast_mode']}")
    print(f"  [OK] Preview: {res['message_preview'][:80]}...")

    print("\n=== TEST 2: Emergency SMS Broadcast (Default Emergency Group) ===")
    res_def = await SMSService.dispatch_emergency_broadcast(
        phone_numbers=None,
        alert_type="Extreme Heat Wave & Sunstroke Advisory",
        location_name="Hyderabad, Telangana",
        recommendation="Stay indoors during peak afternoon hours (12 PM - 4 PM), drink plenty of water.",
        severity="DANGER"
    )
    assert res_def["success"] is True
    assert res_def["recipient_count"] >= 1
    print(f"  [OK] Default Group SMS Dispatched: Count={res_def['recipient_count']}")

    print("\n[PASSED] EMERGENCY SMS BROADCAST TEST SUITE PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_sms_broadcast())
