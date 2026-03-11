# LinkedIn Lead MVP

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

## LinkedIn session best practice
- Prefer `LINKEDIN_STORAGE_STATE_PATH` and point it to a local file outside the repo, for example `/root/.secrets/linkedin/storage_state.json`.
- Use `LINKEDIN_COOKIES_JSON` only as a temporary override when you already have a clean cookie export.
- Do not commit cookies or `storage_state.json` into this repository.
- When both are present, the worker loads `storage_state_path` first and then overlays `cookies_json`.

## People search output
`POST /api/search/people` is intended to return a lead list close to Harvest `lead-search / LeadShort` for the fields below:

- `full_name`
- `headline`
- `location`
- `current_company`
- `profile_url`
- `profile_urn`
- `public_identifier`

The worker now combines two sources:

- LinkedIn people search page DOM
- LinkedIn internal Voyager/GraphQL search responses captured during page load

This is necessary because LinkedIn's current search page often renders subtitle data in nested `aria-hidden` spans or in internal JSON payloads instead of the old `.entity-result__*` text nodes alone.

## Why headline/location were null before
- The old scraper relied on legacy DOM selectors such as `.entity-result__primary-subtitle` and `.entity-result__secondary-subtitle`.
- LinkedIn's current people search UI frequently serves those values through SDUI/Voyager payloads and `aria-hidden` text runs, so those selectors miss the real content.
- `current_company`, `profile_urn`, and `public_identifier` were never exposed through the backend response schema or persisted columns, so even when partially discovered they were dropped.

## Pagination
- The API accepts `page >= 1`.
- The worker navigates to `https://www.linkedin.com/search/results/people/?keywords=...&page=N` and stores results for that specific page.

## DB migration for dedupe
Apply [`docker/postgres/migrations/20260311_search_results_leadshort.sql`](docker/postgres/migrations/20260311_search_results_leadshort.sql) before running the updated worker on an existing database.

The migration:
- adds `current_company`, `profile_urn`, `public_identifier`
- removes existing duplicate rows for the same `(search_request_id, profile_url)`
- adds a unique constraint on `(search_request_id, profile_url)`

The worker uses PostgreSQL `ON CONFLICT ... DO UPDATE`, so reruns enrich the same result row instead of inserting duplicates.

## MVP flow to verify
1. Open frontend: `http://localhost:13000/login` and submit form.
2. Go to `http://localhost:13000/search`.
3. Input keywords and click **Run Search**.
4. Frontend calls `POST /api/search/people`, polls `GET /api/jobs/{job_id}`, then loads `GET /api/search/results/{search_request_id}`.
5. Click one result item; frontend calls `POST /api/profiles/fetch` and polls job.
6. Frontend jumps to `/profiles/{id}` and loads `GET /api/profiles/{id}`.

## Minimal API verification
1. Trigger a search:
```bash
curl -sS -X POST http://localhost:18000/api/search/people \
  -H 'Content-Type: application/json' \
  -d '{"keywords":"software engineer","page":1}'
```
2. Poll the returned job id:
```bash
curl -sS http://localhost:18000/api/jobs/<job_id>
```
3. Read the stored page results:
```bash
curl -sS http://localhost:18000/api/search/results/<search_request_id>
```
4. Inspect Postgres:
```sql
SELECT
  search_request_id,
  profile_url,
  full_name,
  headline,
  location,
  current_company,
  profile_urn,
  public_identifier
FROM search_results
WHERE search_request_id = '<search_request_id>'
ORDER BY created_at ASC;
```
