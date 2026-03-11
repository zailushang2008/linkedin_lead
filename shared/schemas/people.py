from pydantic import BaseModel


class PeopleSearchItem(BaseModel):
    profile_url: str
    full_name: str | None = None
    headline: str | None = None
    location: str | None = None
    current_company: str | None = None
    profile_urn: str | None = None
    public_identifier: str | None = None
