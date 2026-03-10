import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import JobType
from app.db.session import get_db
from app.schemas.job import JobResultSummary, JobStatusResponse
from app.services.profile_service import ProfileService
from app.services.search_service import SearchService
from app.repositories.job_repository import JobRepository

router = APIRouter(prefix='/jobs', tags=['jobs'])


@router.get('/{job_id}', response_model=JobStatusResponse)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> JobStatusResponse:
    job = JobRepository(db).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')

    result_summary = None
    if job.status.value == 'succeeded':
        if job.job_type == JobType.people_search:
            search_request_id, count = SearchService(db).get_search_result_summary(job.id)
            result_summary = JobResultSummary(search_request_id=search_request_id, results_count=count)
        elif job.job_type == JobType.profile_fetch:
            profile = ProfileService(db).get_profile_by_url(job.payload.get('profile_url', ''))
            result_summary = JobResultSummary(profile_id=profile.id if profile else None)

    return JobStatusResponse(
        id=job.id,
        status=job.status.value,
        job_type=job.job_type.value,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        result=result_summary,
    )
