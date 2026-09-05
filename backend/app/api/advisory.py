from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import get_optional_user
from app.db.session import get_db
from app.models.entities import User
from app.schemas.api import AdvisoryRequest, CropAdvisoryRequest
from app.services.advisory_service import AdvisoryService

router = APIRouter(prefix="/advisory", tags=["advisory"])
svc = AdvisoryService()


@router.post("")
async def create_advisory(
    body: AdvisoryRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    return await svc.generate(
        db,
        body.question,
        body.advisory_type,
        body.location,
        body.language.value,
        user,
    )


@router.post("/crop")
async def get_crop_advisory(
    body: CropAdvisoryRequest,
):
    return svc.generate_crop_advisory(
        crop=body.crop,
        stage=body.stage,
        weather_data=body.weather_data,
    )

