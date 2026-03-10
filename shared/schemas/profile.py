from pydantic import BaseModel


class ProfileSchema(BaseModel):
    profile_url: str
    full_name: str | None = None
    headline: str | None = None
    location: str | None = None
    about: str | None = None
    experiences: list = []
    education: list = []
