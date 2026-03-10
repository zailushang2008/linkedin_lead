import logging
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.celery_client import celery_client
from app.db.session import get_db
from app.schemas.job import JobCreateResponse
from app.schemas.profile import ProfileFetchCachedResponse, ProfileResponse
from app.schemas.search import PeopleSearchRequest, ProfileFetchRequest
from app.services.job_service import JobService
from app.services.profile_service import ProfileService

logger = logging.getLogger(__name__)
router = APIRouter(prefix='', tags=['search'])

DEMO_USER_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')


@router.post('/search/people', response_model=JobCreateResponse)
def create_people_search(payload: PeopleSearchRequest, db: Session = Depends(get_db)) -> JobCreateResponse:
    service = JobService(db)
    job = service.create_people_search_job(user_id=DEMO_USER_ID, keywords=payload.keywords, page=payload.page)
    celery_client.send_task('tasks.people_search.run', args=[str(job.id)])
    logger.info('queued people search job_id=%s keywords=%s page=%s', job.id, payload.keywords, payload.page)
    return JobCreateResponse(job_id=job.id, status=job.status.value, job_type=job.job_type.value)


@router.post('/profiles/fetch', response_model=ProfileFetchCachedResponse)
def fetch_profile(payload: ProfileFetchRequest, db: Session = Depends(get_db)) -> ProfileFetchCachedResponse:
    profile_service = ProfileService(db)
    existing = profile_service.get_profile_by_url(str(payload.profile_url))
    if existing:
        logger.info('profile cache hit profile_id=%s url=%s', existing.id, existing.profile_url)
        return ProfileFetchCachedResponse(
            cached=True,
            profile=ProfileResponse(
                id=existing.id,
                profile_url=existing.profile_url,
                full_name=existing.full_name,
                headline=existing.headline,
                location=existing.location,
                about=existing.about,
                experiences=existing.experiences,
                education=existing.education,
            ),
        )

    job = JobService(db).create_profile_fetch_job(user_id=DEMO_USER_ID, profile_url=str(payload.profile_url))
    celery_client.send_task('tasks.profile_fetch.run', args=[str(job.id)])
    logger.info('queued profile fetch job_id=%s url=%s', job.id, payload.profile_url)
    return ProfileFetchCachedResponse(cached=False, job_id=job.id, status=job.status.value)
