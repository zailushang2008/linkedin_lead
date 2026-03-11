from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl


class PeopleSearchRequest(BaseModel):
    keywords: str = Field(min_length=1, max_length=255)
    page: int = Field(default=1, ge=1)
    cookies_json: str | None = None
    storage_state_path: str | None = None


class SearchResultItemResponse(BaseModel):
    id: UUID
    profile_url: str
    full_name: str | None = None
    headline: str | None = None
    location: str | None = None
    current_company: str | None = None
    profile_urn: str | None = None
    public_identifier: str | None = None


class ProfileFetchRequest(BaseModel):
    profile_url: HttpUrl
    cookies_json: str | None = None
    storage_state_path: str | None = None
