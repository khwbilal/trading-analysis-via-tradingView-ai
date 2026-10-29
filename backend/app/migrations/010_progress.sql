-- 010: progress of a running job or backtest (WL-053), written by app/progress.py while it runs.
-- NULL when the run reports no steps; the portal then shows an open-ended bar.

ALTER TABLE job_runs ADD COLUMN progress_done  INTEGER;
ALTER TABLE job_runs ADD COLUMN progress_total INTEGER;
ALTER TABLE job_runs ADD COLUMN progress_note  TEXT;

ALTER TABLE backtest_runs ADD COLUMN progress_done  INTEGER;
ALTER TABLE backtest_runs ADD COLUMN progress_total INTEGER;
ALTER TABLE backtest_runs ADD COLUMN progress_note  TEXT;
