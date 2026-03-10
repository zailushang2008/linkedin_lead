import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.profile import ProfileResponse
from app.services.profile_service import ProfileService

router = APIRouter(prefix='/profiles', tags=['profiles'])


@router.get('/{profile_id}', response_model=ProfileResponse)
def get_profile(profile_id: uuid.UUID, db: Session = Depends(get_db)) -> ProfileResponse:
    profile = ProfileService(db).get_profile_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail='Profile not found')

    return ProfileResponse(
        id=profile.id,
        profile_url=profile.profile_url,
        full_name=profile.full_name,
        headline=profile.headline,
        location=profile.location,
        about=profile.about,
        experiences=profile.experiences,
        education=profile.education,
    )
