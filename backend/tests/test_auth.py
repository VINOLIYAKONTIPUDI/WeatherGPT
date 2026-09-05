from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_send_and_verify_otp():
    ident = "tester-otp@demo.weathergpt.in"
    send = client.post("/auth/send-otp", json={"identifier": ident, "name": "Tester"})
    assert send.status_code == 200
    assert send.json()["sent"] is True
    otp = get_settings().demo_otp
    verify = client.post(
        "/auth/verify-otp",
        json={
            "identifier": ident,
            "otp": otp,
            "name": "Tester",
            "role": "public",
            "preferred_language": "en",
        },
    )
    assert verify.status_code == 200
    assert "access_token" in verify.json()
    bad = client.post("/auth/verify-otp", json={"identifier": ident, "otp": "000000"})
    assert bad.status_code == 400


def test_role_based_admin_blocked_for_public():
    ident = "public-rbac@demo.weathergpt.in"
    client.post("/auth/send-otp", json={"identifier": ident})
    token = client.post(
        "/auth/verify-otp",
        json={"identifier": ident, "otp": get_settings().demo_otp, "role": "public"},
    ).json()["access_token"]
    r = client.get("/admin/system-status", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
