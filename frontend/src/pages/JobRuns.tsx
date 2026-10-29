import Alert from "@mui/material/Alert";
import Card from "@mui/material/Card";
import MenuItem from "@mui/material/MenuItem";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import HistoryOutlined from "@mui/icons-material/HistoryOutlined";
import Refresh from "@mui/icons-material/Refresh";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, type JobRun, type JobStatus } from "../api";
import { RunProgress, StatePill, StateTabs, countStates, type RunFilter } from "../components/RunStatus";
import { ActionButton, DataTable, EmptyState, KpiStrip, Na, Num, PageHeader, Pill, V } from "../components/ui";
import { fmtCompact } from "../lib/format";
import { PROVIDER_LABEL } from "../lib/nav";
import { usePref } from "../lib/storage";

const NO_AI = "No AI call in this run";

/** "2026-10-22 15:00:01 UTC"; the local time is in the tooltip. */
function utc(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return `${d.toISOString().slice(0, 19).replace("T", " ")} UTC`;
}

function local(iso: string): string {
  return `Local: ${new Date(iso).toLocaleString()}`;
}

function fmtDuration(ms: number | null | undefined): string | null {
  if (ms === null || ms === undefined) return null;
  if (ms < 1000) return `${String(ms)} ms`;
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)} s`;
  return `${String(Math.floor(s / 60))} m ${String(Math.round(s % 60))} s`;
}

function fmtTokens(n: number | null | undefined): string | null {
  return n === null || n === undefined ? null : n < 10000 ? n.toLocaleString() : fmtCompact(n);
}

const POLL_MS = 3000;

function TriggerPill({ trigger }: Readonly<{ trigger: string | null | undefined }>) {
  if (!trigger) return <Na reason="Recorded before triggers were stored (WL-052)" />;
  return trigger === "scheduled" ? <Pill glyph="◷" label="scheduled" /> : <Pill glyph="▸" label="manual" />;
}

/** Every scheduled job run from job_runs, newest first, with UTC times, duration and AI usage (WL-052); status tabs and live progress (WL-053). */
export default function JobRuns({ active }: Readonly<{ active: boolean }>) {
  const [runs, setRuns] = useState<JobRun[] | null>(null);
  const [jobs, setJobs] = useState<JobStatus[]>([]);
  const [job, setJob] = usePref("cca_jobs_job", ""); // WL-101: kept per browser
  const [filter, setFilter] = usePref<RunFilter>("cca_jobs_tab", "all");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async () => {
    setBusy(true);
    try {
      const [r, j] = await Promise.all([api.jobRuns(job), api.jobs()]);
      setRuns(r.runs);
      setJobs(j.jobs);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }, [job]);

  useEffect(() => {
    if (active) load().catch(() => undefined);
  }, [active, load]);

  // While a run is going, reload every few seconds so its bar moves.
  const anyRunning = (runs ?? []).some((r) => r.status === "running");
  useEffect(() => {
    if (!active || !anyRunning) return undefined;
    timer.current = setTimeout(() => void load(), POLL_MS);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [active, anyRunning, runs, load]);

  const list = runs ?? [];
  const counts = countStates(list, (r) => r.status);
  const shownRuns = filter === "all" ? list : list.filter((r) => r.status === filter);
  const failed = counts.failed;
  const scheduled = list.filter((r) => r.trigger === "scheduled").length;
  const aiRuns = list.filter((r) => r.ai_calls);
  const sum = (k: "tokens_in" | "tokens_out" | "cost_usd") =>
    aiRuns.some((r) => r[k] !== null && r[k] !== undefined) ? aiRuns.reduce((a, r) => a + (r[k] ?? 0), 0) : null;
  const tokensIn = sum("tokens_in");
  const tokensOut = sum("tokens_out");
  const shown = job ? `${job} runs` : "runs";

  return (
    <Stack spacing={2}>
      <PageHeader
        title="Job runs"
        subtitle="Every run of the scheduled jobs, from the job_runs table. Times are UTC (hover for local time). AI columns fill only when a job calls a model."
        actions={
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <TextField select size="small" label="Job" value={job} onChange={(e) => setJob(e.target.value)}
              slotProps={{ select: { displayEmpty: true }, inputLabel: { shrink: true } }}
              sx={{ minWidth: 150 }}
            >
              <MenuItem value="">All jobs</MenuItem>
              {jobs.map((j) => (
                <MenuItem key={j.job} value={j.job}>
                  {j.job}
                </MenuItem>
              ))}
            </TextField>
            <ActionButton icon={<Refresh />} busy={busy} busyLabel="Loading…" onClick={() => void load()}>
              Refresh
            </ActionButton>
          </Stack>
        }
      />
      {error ? <Alert severity="warning">Job runs unavailable: {error}</Alert> : null}
      <KpiStrip
        tiles={[
          { label: "Runs", value: runs ? String(list.length) : <Na />, note: `Latest ${shown}, up to 200` },
          { label: "Scheduled", value: runs ? String(scheduled) : <Na />, note: "Started by Task Scheduler" },
          { label: "Running", value: runs ? String(counts.running) : <Na />, note: anyRunning ? "Refreshing every 3 s" : "Nothing running now" },
          { label: "Failed", value: runs ? String(failed) : <Na />, note: "Exit code other than 0" },
          { label: "AI calls", value: runs ? String(aiRuns.reduce((a, r) => a + (r.ai_calls ?? 0), 0)) : <Na />, note: `In ${String(aiRuns.length)} runs` },
          {
            label: "Tokens in / out",
            value: <V value={tokensIn === null && tokensOut === null ? null : `${fmtTokens(tokensIn) ?? "?"} / ${fmtTokens(tokensOut) ?? "?"}`} reason={NO_AI} />,
            note: "Over the runs shown",
          },
        ]}
      />
      <Card>
        <StateTabs value={filter} onChange={setFilter} counts={counts} />
        {!runs && !error ? <Skeleton height={160} sx={{ mx: 2 }} /> : null}
        {runs && !shownRuns.length ? (
          <EmptyState icon={<HistoryOutlined />} text={runs.length ? "No runs with this status." : "No job runs recorded yet."} />
        ) : null}
        {shownRuns.length ? (
          <DataTable minWidth={1280}>
            <TableHead>
              <TableRow>
                <TableCell>Started (UTC)</TableCell>
                <TableCell>Job</TableCell>
                <TableCell>Trigger</TableCell>
                <TableCell>Result</TableCell>
                <TableCell align="right">Duration</TableCell>
                <TableCell>AI provider</TableCell>
                <TableCell>Model</TableCell>
                <TableCell>Effort</TableCell>
                <TableCell align="right">Calls</TableCell>
                <TableCell align="right">Tokens in</TableCell>
                <TableCell align="right">Tokens out</TableCell>
                <TableCell align="right">Cost</TableCell>
                <TableCell>Message</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {shownRuns.map((r) => (
                <TableRow key={r.id} hover>
                  <TableCell sx={{ whiteSpace: "nowrap" }} title={local(r.started_at)}>
                    <Num>{utc(r.started_at) ?? r.started_at}</Num>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{r.job}</TableCell>
                  <TableCell>
                    <TriggerPill trigger={r.trigger} />
                  </TableCell>
                  <TableCell>
                    <Stack spacing={0.75} sx={{ alignItems: "flex-start" }}>
                      <StatePill
                        state={r.status}
                        title={r.exit_code !== null && r.exit_code !== undefined ? `Exit code ${String(r.exit_code)}` : undefined}
                      />
                      {r.status === "running" ? (
                        <RunProgress done={r.progress_done} total={r.progress_total} note={r.progress_note} startedAt={r.started_at} />
                      ) : null}
                    </Stack>
                  </TableCell>
                  <TableCell align="right" title={r.finished_at ? `Ended ${utc(r.finished_at) ?? r.finished_at}` : undefined}>
                    <V value={fmtDuration(r.duration_ms)} reason={r.status === "running" ? "Still running" : "No end recorded"} />
                  </TableCell>
                  <TableCell>
                    <V value={r.ai_provider ? (PROVIDER_LABEL[r.ai_provider] ?? r.ai_provider) : null} reason={NO_AI} mono={false} />
                  </TableCell>
                  <TableCell>
                    <V value={r.ai_model ?? null} reason={NO_AI} />
                  </TableCell>
                  <TableCell>
                    <V value={r.ai_effort ?? null} reason={r.ai_calls ? "The provider takes no effort setting" : NO_AI} mono={false} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={r.ai_calls ? String(r.ai_calls) : null} reason={NO_AI} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtTokens(r.tokens_in)} reason={r.ai_calls ? "The provider reports no token counts" : NO_AI} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtTokens(r.tokens_out)} reason={r.ai_calls ? "The provider reports no token counts" : NO_AI} />
                  </TableCell>
                  <TableCell align="right" title={r.ai_provider === "claude_code" ? "Estimate at API prices; the subscription is not billed per call" : undefined}>
                    <V value={r.cost_usd === null || r.cost_usd === undefined ? null : `$${r.cost_usd.toFixed(4)}`} reason={r.ai_calls ? "The provider reports no cost" : NO_AI} />
                  </TableCell>
                  <TableCell sx={{ maxWidth: 360 }}>
                    <Typography variant="body2" sx={{ overflowWrap: "anywhere", color: "text.secondary" }}>
                      {r.message ?? <Na reason="No message recorded" />}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </DataTable>
        ) : null}
      </Card>
    </Stack>
  );
}
