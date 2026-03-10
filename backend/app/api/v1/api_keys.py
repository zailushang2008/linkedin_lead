from fastapi import APIRouter

router = APIRouter(prefix='/api-keys', tags=['api-keys'])


@router.post('')
def create_api_key():
    return {'message': 'API key endpoint skeleton'}
