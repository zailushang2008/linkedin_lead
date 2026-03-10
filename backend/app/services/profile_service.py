import uuid
from sqlalchemy.orm import Session

from app.repositories.profile_repository import ProfileRepository


class ProfileService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProfileRepository(db)

    def get_profile_by_id(self, profile_id: uuid.UUID):
        return self.repo.get_by_id(profile_id)

    def get_profile_by_url(self, profile_url: str):
        return self.repo.get_by_url(profile_url)
