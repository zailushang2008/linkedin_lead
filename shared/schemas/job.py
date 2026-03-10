from enum import Enum
from pydantic import BaseModel


class JobStatus(str, Enum):
    queued = 'queued'
    running = 'running'
    succeeded = 'succeeded'
    failed = 'failed'


class JobType(str, Enum):
    people_search = 'people_search'
    profile_fetch = 'profile_fetch'


class JobPayload(BaseModel):
    job_type: JobType
    payload: dict
