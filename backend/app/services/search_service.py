import uuid
from sqlalchemy.orm import Session

from app.repositories.search_repository import SearchRepository


class SearchService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SearchRepository(db)

    def get_search_result_summary(self, job_id: uuid.UUID) -> tuple[uuid.UUID | None, int | None]:
        request = self.repo.get_request_by_job(job_id)
        if not request:
            return None, None
        results = self.repo.list_results(request.id)
        return request.id, len(results)

    def get_results(self, search_request_id: uuid.UUID):
        request = self.repo.get_request(search_request_id)
        if not request:
            return None
        return self.repo.list_results(search_request_id)
