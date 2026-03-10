from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, search, jobs, profiles, api_keys, usage, search_results
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine

configure_logging(settings.log_level)

app = FastAPI(title='LinkedIn Lead MVP API', version='0.2.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


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
