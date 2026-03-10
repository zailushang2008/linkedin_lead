from celery import Celery

from app.core.config import settings

celery_client = Celery(
    'linkedin_lead_backend',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
