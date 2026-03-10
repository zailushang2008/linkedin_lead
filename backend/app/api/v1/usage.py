from fastapi import APIRouter

router = APIRouter(prefix='/usage', tags=['usage'])


@router.get('')
def usage_overview():
    return {'message': 'Usage endpoint skeleton'}
