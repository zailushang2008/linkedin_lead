from datetime import datetime, timedelta, timezone
from jose import jwt

ALGORITHM = 'HS256'


def create_access_token(subject: str, secret_key: str, expires_minutes: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {'sub': subject, 'exp': expire}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)
