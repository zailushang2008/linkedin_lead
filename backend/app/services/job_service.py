import uuid
from sqlalchemy.orm import Session

from app.db.models import JobType
from app.repositories.job_repository import JobRepository
from app.repositories.search_repository import SearchRepository


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.jobs = JobRepository(db)
        self.search = SearchRepository(db)

    def create_people_search_job(self, user_id: uuid.UUID, keywords: str, page: int):
        job = self.jobs.create(user_id=user_id, job_type=JobType.people_search, payload={'keywords': keywords, 'page': page})
        self.search.create_request(job_id=job.id, user_id=user_id, keywords=keywords, page=page)
        self.db.commit()
        self.db.refresh(job)
        return job

    def create_profile_fetch_job(self, user_id: uuid.UUID, profile_url: str):
        job = self.jobs.create(user_id=user_id, job_type=JobType.profile_fetch, payload={'profile_url': profile_url})
        self.db.commit()
        self.db.refresh(job)
        return job
