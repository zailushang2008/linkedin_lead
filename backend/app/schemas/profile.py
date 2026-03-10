from uuid import UUID
from pydantic import BaseModel


class ProfileResponse(BaseModel):
    id: UUID
    profile_url: str
    full_name: str | None = None
    headline: str | None = None
    location: str | None = None
    about: str | None = None
    experiences: list[dict] = []
    education: list[dict] = []


class ProfileFetchCachedResponse(BaseModel):
    cached: bool
    profile: ProfileResponse | None = None
    job_id: UUID | None = None
    status: str | None = None
