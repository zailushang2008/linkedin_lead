import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import SearchResultItemResponse
from app.services.search_service import SearchService

router = APIRouter(prefix='/search/results', tags=['search-results'])


@router.get('/{search_request_id}', response_model=list[SearchResultItemResponse])
def get_search_results(search_request_id: uuid.UUID, db: Session = Depends(get_db)) -> list[SearchResultItemResponse]:
    results = SearchService(db).get_results(search_request_id)
    if results is None:
        raise HTTPException(status_code=404, detail='search request not found')

    return [
        SearchResultItemResponse(
            id=item.id,
            profile_url=item.profile_url,
            full_name=item.full_name,
            headline=item.headline,
            location=item.location,
            current_company=item.current_company,
            profile_urn=item.profile_urn,
            public_identifier=item.public_identifier,
        )
        for item in results
    ]
