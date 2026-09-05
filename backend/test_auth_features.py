import asyncio
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.routes.auth import signup, verify_otp, login, resend_otp, get_me
from app.models.schemas import (
    UserSignupRequest, UserVerifyOTPRequest, UserResendOTPRequest, UserLoginRequest
)
from app.db.mongodb import db_instance

async def test_auth_pipeline():
    print("=== TEST 1: Signup Flow ===")
    signup_req = UserSignupRequest(
        name="Test User",
        email="testuser@example.com",
        password="Password123",
        confirm_password="Password123"
    )
    signup_res = await signup(signup_req)
    assert "successful" in signup_res["message"].lower()
    print(f"  [OK] Signup Response: {signup_res['message']}")

    # Fetch stored user to extract generated OTP for verification test
    stored_user = db_instance.in_memory_users.get("testuser@example.com")
    otp_code = stored_user["otp"]
    print(f"  [OK] Generated OTP: {otp_code}")

    print("\n=== TEST 2: OTP Verification Flow ===")
    verify_req = UserVerifyOTPRequest(email="testuser@example.com", otp=otp_code)
    auth_res = await verify_otp(verify_req)
    assert auth_res.access_token is not None
    assert auth_res.user.is_verified is True
    print(f"  [OK] OTP Verified. Access Token Generated! User='{auth_res.user.name}'")

    print("\n=== TEST 3: Login Flow ===")
    login_req = UserLoginRequest(email="testuser@example.com", password="Password123")
    login_res = await login(login_req)
    assert login_res.access_token is not None
    print(f"  [OK] Login Successful! Token='{login_res.access_token[:25]}...'")

    print("\n=== TEST 4: Get Current User (/me) Flow ===")
    me_res = await get_me(authorization=f"Bearer {login_res.access_token}")
    assert me_res.email == "testuser@example.com"
    print(f"  [OK] Get Me Success! ID={me_res.id} Name={me_res.name} Email={me_res.email}")

    print("\n[PASSED] ALL AUTHENTICATION TEST SUITES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_auth_pipeline())
