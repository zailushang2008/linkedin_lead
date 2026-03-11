import asyncio
import logging
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import Job, JobStatus, SearchRequest, SearchResult
from app.scraper.people_search_scraper import scrape_people_search

logger = logging.getLogger(__name__)


@celery_app.task(name='tasks.people_search.run')
def run_people_search(job_id: str) -> dict:
    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error('people_search job missing job_id=%s', job_id)
            return {'error': 'job_not_found'}

        logger.info('people_search started job_id=%s', job_id)
        job.status = JobStatus.running
        job.started_at = datetime.utcnow()
        db.commit()

        keywords = job.payload.get('keywords', '')
        page = int(job.payload.get('page', 1))
        scraped = asyncio.run(
            scrape_people_search(
                keywords=keywords,
                page=page,
                cookies_json=job.payload.get('cookies_json'),
                storage_state_path=job.payload.get('storage_state_path'),
            )
        )

        request = db.query(SearchRequest).filter(SearchRequest.job_id == job.id).first()
        if not request:
            raise ValueError(f'search_request not found for job_id={job_id}')

        rows = [
            {
                'search_request_id': request.id,
                'profile_url': item['profile_url'],
                'full_name': item.get('full_name'),
                'headline': item.get('headline'),
                'location': item.get('location'),
                'current_company': item.get('current_company'),
                'profile_urn': item.get('profile_urn'),
                'public_identifier': item.get('public_identifier'),
                'raw_json': item,
            }
            for item in scraped
            if item.get('profile_url')
        ]

        if rows:
            insert_stmt = pg_insert(SearchResult.__table__).values(rows)
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['search_request_id', 'profile_url'],
                set_={
                    'full_name': insert_stmt.excluded.full_name,
                    'headline': insert_stmt.excluded.headline,
                    'location': insert_stmt.excluded.location,
                    'current_company': insert_stmt.excluded.current_company,
                    'profile_urn': insert_stmt.excluded.profile_urn,
                    'public_identifier': insert_stmt.excluded.public_identifier,
                    'raw_json': insert_stmt.excluded.raw_json,
                },
            )
            db.execute(upsert_stmt)

        job.status = JobStatus.succeeded
        job.finished_at = datetime.utcnow()
        db.commit()
        logger.info('people_search succeeded job_id=%s results=%s', job_id, len(rows))
        return {'job_id': job_id, 'status': 'succeeded', 'results_count': len(rows)}
    except Exception as exc:
        logger.exception('people_search failed job_id=%s error=%s', job_id, exc)
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
