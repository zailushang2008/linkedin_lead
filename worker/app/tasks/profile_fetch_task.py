import asyncio
import logging
from datetime import datetime

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import Job, JobStatus, Profile
from app.scraper.profile_scraper import scrape_profile

logger = logging.getLogger(__name__)


@celery_app.task(name='tasks.profile_fetch.run')
def run_profile_fetch(job_id: str) -> dict:
    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error('profile_fetch job missing job_id=%s', job_id)
            return {'error': 'job_not_found'}

        logger.info('profile_fetch started job_id=%s', job_id)
        job.status = JobStatus.running
        job.started_at = datetime.utcnow()
        db.commit()

        profile_url = job.payload.get('profile_url')
        if not profile_url:
            raise ValueError('missing profile_url in job payload')

        profile_data = asyncio.run(
            scrape_profile(
                profile_url=profile_url,
                cookies_json=job.payload.get('cookies_json'),
                storage_state_path=job.payload.get('storage_state_path'),
            )
        )

        profile = db.query(Profile).filter(Profile.profile_url == profile_url).first()
        if not profile:
            profile = Profile(profile_url=profile_url)
            db.add(profile)

        profile.full_name = profile_data.get('full_name')
        profile.headline = profile_data.get('headline')
        profile.location = profile_data.get('location')
        profile.about = profile_data.get('about')
        profile.experiences = profile_data.get('experiences', [])
        profile.education = profile_data.get('education', [])
        profile.raw_json = profile_data
        profile.updated_at = datetime.utcnow()

        job.status = JobStatus.succeeded
        job.finished_at = datetime.utcnow()
        db.commit()
        logger.info('profile_fetch succeeded job_id=%s profile_url=%s', job_id, profile_url)
        return {'job_id': job_id, 'status': 'succeeded', 'profile_url': profile_url}
    except Exception as exc:
        logger.exception('profile_fetch failed job_id=%s error=%s', job_id, exc)
        db.rollback()
        if not job:
            job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.failed
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            db.commit()
        return {'job_id': job_id, 'status': 'failed', 'error': str(exc)}
    finally:
        db.close()
