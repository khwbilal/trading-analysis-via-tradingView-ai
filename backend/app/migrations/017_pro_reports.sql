-- 017: professional backtest reports (WL-079). One row per report, kept for good (decision 0010).

CREATE TABLE IF NOT EXISTS pro_reports (
    id          INTEGER PRIMARY KEY,
    created_at  TEXT NOT NULL,
    run_id      INTEGER,                 -- the agent run it came from; NULL when pooled over every run
    params      TEXT NOT NULL,           -- JSON: sample size, seed, split, folds
    report      TEXT NOT NULL            -- JSON: per agent figures (see app/evaluation.py)
);
