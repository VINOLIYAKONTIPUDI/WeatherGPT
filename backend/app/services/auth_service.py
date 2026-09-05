import logging
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import create_access_token, hash_otp, verify_otp
from app.models.entities import LanguageCode, OTPChallenge, User, UserRole

logger = logging.getLogger("weathergpt.auth")


class AuthService:
    def send_otp(self, db: Session, identifier: str) -> dict:
        settings = get_settings()
        otp = settings.demo_otp if settings.demo_mode else f"{random.randint(100000, 999999)}"
        db.query(OTPChallenge).filter(OTPChallenge.identifier == identifier, OTPChallenge.consumed.is_(False)).update(
            {"consumed": True}
        )
        challenge = OTPChallenge(
            identifier=identifier.strip().lower(),
            otp_hash=hash_otp(otp),
            expires_at=datetime.utcnow() + timedelta(minutes=settings.otp_expire_minutes),
        )
        db.add(challenge)
        db.commit()
        logger.info("otp_sent identifier_kind=%s demo=%s", "email" if "@" in identifier else "phone", settings.demo_mode)
        # Never log the OTP itself
        return {
            "sent": True,
            "demo": settings.demo_mode,
            "hint": f"Use OTP {settings.demo_otp} in demo mode" if settings.demo_mode else "OTP sent",
            "expires_minutes": settings.otp_expire_minutes,
        }

    def verify(
        self,
        db: Session,
        identifier: str,
        otp: str,
        name: str | None,
        role: UserRole,
        language: LanguageCode,
    ) -> User:
        ident = identifier.strip().lower()
        row = (
            db.query(OTPChallenge)
            .filter(OTPChallenge.identifier == ident, OTPChallenge.consumed.is_(False))
            .order_by(OTPChallenge.created_at.desc())
            .first()
        )
        if not row or row.expires_at < datetime.utcnow() or not verify_otp(otp, row.otp_hash):
            raise ValueError("Invalid or expired OTP")
        row.consumed = True
        user = db.query(User).filter((User.email == ident) | (User.phone == ident)).first()
        if not user:
            is_email = "@" in ident
            user = User(
                name=name or "WeatherGPT user",
                email=ident if is_email else None,
                phone=None if is_email else ident,
                role=role,
                preferred_language=language,
            )
            db.add(user)
        else:
            if name:
                user.name = name
            user.preferred_language = language
        db.commit()
        db.refresh(user)
        return user

    def token_for(self, user: User) -> str:
        return create_access_token(
            {"sub": str(user.id), "role": user.role.value, "lang": user.preferred_language.value}
        )
