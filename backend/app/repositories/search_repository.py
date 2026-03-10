import uuid
from sqlalchemy.orm import Session

from app.db.models import SearchRequest, SearchResult


class SearchRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_request(self, job_id: uuid.UUID, user_id: uuid.UUID, keywords: str, page: int) -> SearchRequest:
        request = SearchRequest(job_id=job_id, user_id=user_id, keyword=keywords, page=page)
        self.db.add(request)
        self.db.flush()
        return request

    def get_request_by_job(self, job_id: uuid.UUID) -> SearchRequest | None:
        return self.db.query(SearchRequest).filter(SearchRequest.job_id == job_id).first()

    def get_request(self, request_id: uuid.UUID) -> SearchRequest | None:
        return self.db.query(SearchRequest).filter(SearchRequest.id == request_id).first()

    def list_results(self, search_request_id: uuid.UUID) -> list[SearchResult]:
        return (
            self.db.query(SearchResult)
            .filter(SearchResult.search_request_id == search_request_id)
            .order_by(SearchResult.created_at.asc())
            .all()
        )
