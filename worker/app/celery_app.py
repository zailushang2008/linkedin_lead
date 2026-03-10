from celery import Celery

from app.config import settings
from app.logging_conf import configure_logging

configure_logging('INFO')

celery_app = Celery(
    'linkedin_lead_worker',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.autodiscover_tasks(['app.tasks'])
