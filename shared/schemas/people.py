from pydantic import BaseModel


class PeopleSearchItem(BaseModel):
    profile_url: str
    full_name: str | None = None
    headline: str | None = None
    location: str | None = None
