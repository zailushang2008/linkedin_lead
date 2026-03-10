import uuid
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail='Invalid credentials')

    # Skeleton behavior: replace with real user/password verification.
    demo_user_id = str(uuid.uuid4())
    token = create_access_token(demo_user_id, settings.secret_key, settings.access_token_expire_minutes)
    return LoginResponse(access_token=token)
