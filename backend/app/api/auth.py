from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.rbac import get_current_user
from app.db.session import get_db
from app.models.entities import Location, User, UserLocation
from app.schemas.api import OTPSendRequest, OTPVerifyRequest, ProfileUpdate, TokenResponse
from app.services.auth_service import AuthService
from app.services.location_service import LocationService

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()
locations = LocationService()


@router.post("/send-otp")
def send_otp(body: OTPSendRequest, db: Session = Depends(get_db)):
    return auth_service.send_otp(db, body.identifier)


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(body: OTPVerifyRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.verify(
            db, body.identifier, body.otp, body.name, body.role, body.preferred_language
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TokenResponse(
        access_token=auth_service.token_for(user),
        user=_user_dict(user),
        demo=True,
    )


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _user_dict(user, db)


@router.patch("/profile")
def update_profile(
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.name:
        user.name = body.name
    if body.preferred_language:
        user.preferred_language = body.preferred_language
    if body.location_id:
        loc = db.get(Location, body.location_id)
        if not loc:
            raise HTTPException(404, "Location not found")
        db.query(UserLocation).filter(UserLocation.user_id == user.id).delete()
        db.add(UserLocation(user_id=user.id, location_id=loc.id, is_primary=True))
    elif body.location_name:
        loc = locations.search_db(db, body.location_name)
        if loc:
            db.query(UserLocation).filter(UserLocation.user_id == user.id).delete()
            db.add(UserLocation(user_id=user.id, location_id=loc[0].id, is_primary=True))
    db.commit()
    db.refresh(user)
    return _user_dict(user, db)


def _user_dict(user: User, db: Session | None = None) -> dict:
    loc = None
    if user.locations:
        l = user.locations[0].location
        loc = {
            "id": l.id,
            "name": l.name,
            "district": l.district,
            "state": l.state,
            "latitude": l.latitude,
            "longitude": l.longitude,
        }
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.phone,
        "email": user.email,
        "role": user.role.value,
        "preferred_language": user.preferred_language.value,
        "location": loc,
    }
