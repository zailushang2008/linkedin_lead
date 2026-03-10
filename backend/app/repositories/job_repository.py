import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import Job, JobStatus, JobType


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: uuid.UUID, job_type: JobType, payload: dict) -> Job:
        job = Job(user_id=user_id, job_type=job_type, status=JobStatus.queued, payload=payload)
        self.db.add(job)
        self.db.flush()
        return job

    def get(self, job_id: uuid.UUID) -> Job | None:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def update_status(self, job: Job, status: JobStatus, error_message: str | None = None) -> Job:
        job.status = status
        if status == JobStatus.running:
            job.started_at = datetime.utcnow()
        if status in (JobStatus.succeeded, JobStatus.failed):
            job.finished_at = datetime.utcnow()
        job.error_message = error_message
        self.db.add(job)
        self.db.flush()
        return job
