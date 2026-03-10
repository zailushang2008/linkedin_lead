import uuid
from sqlalchemy.orm import Session

from app.db.models import Profile


class ProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, profile_id: uuid.UUID) -> Profile | None:
        return self.db.query(Profile).filter(Profile.id == profile_id).first()

    def get_by_url(self, profile_url: str) -> Profile | None:
        return self.db.query(Profile).filter(Profile.profile_url == profile_url).first()
