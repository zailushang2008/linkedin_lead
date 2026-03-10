import logging
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, search, jobs, profiles, api_keys, usage, search_results
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.models import User
from app.db.session import SessionLocal, engine

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title='LinkedIn Lead MVP API', version='0.2.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

DEMO_USER_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')


def seed_demo_user() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.id == DEMO_USER_ID).first()
        if existing:
            return

        db.add(
            User(
                id=DEMO_USER_ID,
                email='demo@linkedin-lead.local',
                password_hash='demo_password_not_used_in_mvp',
                role='user',
                is_active=True,
            )
        )
        db.commit()
        logger.info('seeded demo user id=%s', DEMO_USER_ID)
    finally:
        db.close()


@app.on_event('startup')
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_demo_user()


app.include_router(auth.router, prefix='/api')
app.include_router(search.router, prefix='/api')
app.include_router(search_results.router, prefix='/api')
app.include_router(jobs.router, prefix='/api')
app.include_router(profiles.router, prefix='/api')
app.include_router(api_keys.router, prefix='/api')
app.include_router(usage.router, prefix='/api')


@app.get('/healthz')
def healthz() -> dict:
    return {'status': 'ok'}
