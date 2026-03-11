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

    def create_people_search_job(
        self,
        user_id: uuid.UUID,
        keywords: str,
        page: int,
        cookies_json: str | None = None,
        storage_state_path: str | None = None,
    ):
        payload = {'keywords': keywords, 'page': page}
        if cookies_json:
            payload['cookies_json'] = cookies_json
        if storage_state_path:
            payload['storage_state_path'] = storage_state_path
        job = self.jobs.create(user_id=user_id, job_type=JobType.people_search, payload=payload)
        self.search.create_request(job_id=job.id, user_id=user_id, keywords=keywords, page=page)
        self.db.commit()
        self.db.refresh(job)
        return job

    def create_profile_fetch_job(
        self,
        user_id: uuid.UUID,
        profile_url: str,
        cookies_json: str | None = None,
        storage_state_path: str | None = None,
    ):
        payload = {'profile_url': profile_url}
        if cookies_json:
            payload['cookies_json'] = cookies_json
        if storage_state_path:
            payload['storage_state_path'] = storage_state_path
        job = self.jobs.create(user_id=user_id, job_type=JobType.profile_fetch, payload=payload)
        self.db.commit()
        self.db.refresh(job)
        return job
