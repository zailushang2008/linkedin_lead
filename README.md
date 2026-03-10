# LinkedIn Lead MVP (Runnable with Mock Scraper)

## Stack
- Frontend: Next.js
- Backend: FastAPI
- Worker: Celery
- Queue/Cache: Redis
- DB: PostgreSQL

## Local start
```bash
cp .env.example .env
docker compose up --build
```

## MVP flow to verify
1. Open frontend: `http://localhost:13000/login` and submit form.
2. Go to `http://localhost:13000/search`.
3. Input keywords and click **Run Search**.
4. Frontend calls `POST /api/search/people`, polls `GET /api/jobs/{job_id}`, then loads `GET /api/search/results/{search_request_id}`.
5. Click one result item; frontend calls `POST /api/profiles/fetch` and polls job.
6. Frontend jumps to `/profiles/{id}` and loads `GET /api/profiles/{id}`.

## Notes
- Scrapers are mock implementations in this phase.
- Job lifecycle (`queued/running/succeeded/failed`) and DB persistence are real.
