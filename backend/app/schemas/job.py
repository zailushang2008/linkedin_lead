from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobCreateResponse(BaseModel):
    job_id: UUID
    status: str
    job_type: str


class JobResultSummary(BaseModel):
    search_request_id: UUID | None = None
    results_count: int | None = None
    profile_id: UUID | None = None


class JobStatusResponse(BaseModel):
    id: UUID
    status: str
    job_type: str
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: JobResultSummary | None = None
