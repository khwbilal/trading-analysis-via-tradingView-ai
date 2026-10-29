-- 009: job run detail (WL-052). Times in UTC, how the run started, how long it took,
-- and the AI usage of jobs that call a model. AI columns stay NULL when no model was called.

-- Earlier rows carry a local offset (+05:00); SQLite converts them to UTC.
UPDATE job_runs SET started_at = strftime('%Y-%m-%dT%H:%M:%SZ', started_at)
    WHERE started_at NOT LIKE '%Z' AND strftime('%s', started_at) IS NOT NULL;
UPDATE job_runs SET finished_at = strftime('%Y-%m-%dT%H:%M:%SZ', finished_at)
    WHERE finished_at IS NOT NULL AND finished_at NOT LIKE '%Z' AND strftime('%s', finished_at) IS NOT NULL;

ALTER TABLE job_runs ADD COLUMN trigger     TEXT;     -- scheduled | manual; NULL for rows before 009
ALTER TABLE job_runs ADD COLUMN duration_ms INTEGER;
ALTER TABLE job_runs ADD COLUMN ai_provider TEXT;
ALTER TABLE job_runs ADD COLUMN ai_model    TEXT;
ALTER TABLE job_runs ADD COLUMN ai_effort   TEXT;
ALTER TABLE job_runs ADD COLUMN ai_calls    INTEGER;
ALTER TABLE job_runs ADD COLUMN tokens_in   INTEGER;
ALTER TABLE job_runs ADD COLUMN tokens_out  INTEGER;
ALTER TABLE job_runs ADD COLUMN cost_usd    REAL;    -- only when the provider reports it

UPDATE job_runs SET duration_ms = CAST(ROUND((julianday(finished_at) - julianday(started_at)) * 86400000) AS INTEGER)
    WHERE finished_at IS NOT NULL;
