import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, Header, status
from typing import Optional
from app.models.schemas import (
    UserSignupRequest, UserVerifyOTPRequest, UserResendOTPRequest,
    UserLoginRequest, UserResponse, AuthTokenResponse
)
from app.core import security
from app.db.mongodb import db_instance
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication & Verification"])

def get_user_collection():
    if db_instance.db is not None:
        return db_instance.db["users"]
    return None

async def find_user_by_email(email: str):
    email_clean = email.strip().lower()
    collection = get_user_collection()
    if collection is not None:
        user = await collection.find_one({"email": email_clean})
        return user
    return db_instance.in_memory_users.get(email_clean)

async def save_user(user_doc: dict):
    email_clean = user_doc["email"].strip().lower()
    collection = get_user_collection()
    if collection is not None:
        await collection.update_one({"email": email_clean}, {"$set": user_doc}, upsert=True)
    else:
        db_instance.in_memory_users[email_clean] = user_doc

@router.post("/signup")
async def signup(request: UserSignupRequest):
    email_clean = request.email.strip().lower()
    
    if not request.name or not request.name.strip():
        raise HTTPException(status_code=400, detail="Name is required.")
    if not email_clean or "@" not in email_clean:
        raise HTTPException(status_code=400, detail="Valid email address is required.")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Password and Confirm Password do not match.")

    existing = await find_user_by_email(email_clean)
    if existing and existing.get("is_verified", False):
        raise HTTPException(status_code=400, detail="An account with this email already exists. Please log in.")

    # Generate Hash & 5-minute OTP
    password_hash = security.hash_password(request.password)
    otp = security.generate_otp(6)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    user_id = existing.get("id") if existing else f"usr_{int(datetime.now().timestamp() * 1000)}"

    user_doc = {
        "id": user_id,
        "name": request.name.strip(),
        "email": email_clean,
        "password_hash": password_hash,
        "is_verified": False,
        "otp": otp,
        "otp_expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await save_user(user_doc)

    # Dispatch OTP Email asynchronously
    await EmailService.send_otp_email(email_clean, otp, request.name.strip())

    return {
        "message": "Signup successful! A 6-digit OTP code has been sent to your email.",
        "email": email_clean,
        "otp_expires_in_seconds": 300
    }

@router.post("/verify-otp", response_model=AuthTokenResponse)
async def verify_otp(request: UserVerifyOTPRequest):
    email_clean = request.email.strip().lower()
    otp_input = request.otp.strip()

    user = await find_user_by_email(email_clean)
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    if user.get("is_verified", False):
        # User already verified, issue access token directly
        token = security.create_access_token({"sub": user["id"], "email": email_clean})
        return AuthTokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                id=user["id"],
                name=user["name"],
                email=user["email"],
                is_verified=True
            )
        )

    saved_otp = user.get("otp")
    expires_str = user.get("otp_expires_at")

    if not saved_otp or saved_otp != otp_input:
        raise HTTPException(status_code=400, detail="Invalid OTP code. Please check your email and try again.")

    if expires_str:
        try:
            expires_at = datetime.fromisoformat(expires_str)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                raise HTTPException(
                    status_code=400,
                    detail="OTP code has expired (valid for 5 minutes). Please click 'Resend OTP' to get a new code."
                )
        except HTTPException:
            raise
        except Exception:
            pass

    # Mark user verified
    user["is_verified"] = True
    user["otp"] = None
    user["otp_expires_at"] = None
    await save_user(user)

    # Issue JWT Token
    token = security.create_access_token({"sub": user["id"], "email": email_clean})

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            is_verified=True
        )
    )

@router.post("/resend-otp")
async def resend_otp(request: UserResendOTPRequest):
    email_clean = request.email.strip().lower()

    user = await find_user_by_email(email_clean)
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email.")

    if user.get("is_verified", False):
        raise HTTPException(status_code=400, detail="Your account is already verified. You can log in directly.")

    # Generate fresh OTP valid for 5 minutes
    otp = security.generate_otp(6)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    user["otp"] = otp
    user["otp_expires_at"] = expires_at.isoformat()
    await save_user(user)

    await EmailService.send_otp_email(email_clean, otp, user.get("name", "User"))

    return {
        "message": "A new 6-digit OTP code has been sent to your email.",
        "email": email_clean,
        "otp_expires_in_seconds": 300
    }

@router.post("/login", response_model=AuthTokenResponse)
async def login(request: UserLoginRequest):
    email_clean = request.email.strip().lower()
    
    user = await find_user_by_email(email_clean)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not security.verify_password(request.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.get("is_verified", False):
        # Auto resend fresh OTP for convenience
        otp = security.generate_otp(6)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        user["otp"] = otp
        user["otp_expires_at"] = expires_at.isoformat()
        await save_user(user)
        await EmailService.send_otp_email(email_clean, otp, user.get("name", "User"))

        raise HTTPException(
            status_code=403,
            detail="Your email is not verified yet. We have sent a new OTP code to your email."
        )

    # Issue JWT Token
    token = security.create_access_token({"sub": user["id"], "email": email_clean})

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            is_verified=True
        )
    )

@router.get("/me", response_model=UserResponse)
async def get_me(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authentication token.")

    token = authorization.split(" ")[1]
    payload = security.decode_access_token(token)
    if not payload or "email" not in payload:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")

    user = await find_user_by_email(payload["email"])
    if not user or not user.get("is_verified", False):
        raise HTTPException(status_code=401, detail="User account inactive or not found.")

    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        is_verified=user.get("is_verified", True)
    )

@router.post("/demo-login", response_model=AuthTokenResponse)
async def demo_login():
    """Provides instant 1-click login for hackathon judges & evaluators."""
    demo_email = "demo@weathergpt.com"
    user = await find_user_by_email(demo_email)
    if not user:
        user = {
            "id": "usr_demo_judge_2026",
            "name": "Hackathon Judge",
            "email": demo_email,
            "password_hash": security.hash_password("DemoJudge2026!"),
            "is_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await save_user(user)

    token = security.create_access_token({"sub": user["id"], "email": demo_email})
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            is_verified=True
        )
    )
