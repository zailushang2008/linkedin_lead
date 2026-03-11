ALTER TABLE search_results
    ADD COLUMN IF NOT EXISTS current_company VARCHAR(255),
    ADD COLUMN IF NOT EXISTS profile_urn VARCHAR(255),
    ADD COLUMN IF NOT EXISTS public_identifier VARCHAR(255);

DELETE FROM search_results a
USING search_results b
WHERE a.ctid < b.ctid
  AND a.search_request_id = b.search_request_id
  AND a.profile_url = b.profile_url;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_search_results_request_profile_url'
    ) THEN
        ALTER TABLE search_results
            ADD CONSTRAINT uq_search_results_request_profile_url
            UNIQUE (search_request_id, profile_url);
    END IF;
END $$;
