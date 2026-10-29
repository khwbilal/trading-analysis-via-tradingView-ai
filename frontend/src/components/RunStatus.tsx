import Box from "@mui/material/Box";
import LinearProgress from "@mui/material/LinearProgress";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";
import { Pill, type Tone } from "./ui";

/** The state of a job or backtest run (WL-053), as the API computes it. */
export type RunState = "running" | "success" | "failed" | "interrupted";
export type RunFilter = RunState | "all";

// Success stays neutral and failure uses the warning tone: green and red mean Buy/win and Sell/loss only (ruleset 9.3).
const STATE: Record<RunState, { label: string; glyph: string; tone: Tone; hint: string }> = {
  running: { label: "Running", glyph: "↻", tone: "info", hint: "Started and not finished yet" },
  success: { label: "Success", glyph: "✓", tone: "neutral", hint: "Finished with exit code 0" },
  failed: { label: "Failed", glyph: "✕", tone: "warn", hint: "Finished with an error" },
  interrupted: {
    label: "Interrupted",
    glyph: "⊘",
    tone: "neutral",
    hint: "No end recorded 35 minutes after the start: the PC slept or the process was stopped",
  },
};

export function StatePill({ state, title }: Readonly<{ state: RunState; title?: string }>) {
  const s = STATE[state];
  return <Pill glyph={s.glyph} label={s.label} tone={s.tone} title={title ?? s.hint} />;
}

/** Tabs All / Running / Success / Failed / Interrupted, each with its count. */
export function StateTabs({
  value,
  onChange,
  counts,
}: Readonly<{ value: RunFilter; onChange: (v: RunFilter) => void; counts: Record<RunFilter, number> }>) {
  const order: RunFilter[] = ["all", "running", "success", "failed", "interrupted"];
  return (
    <Tabs
      value={value}
      onChange={(_e, v: RunFilter) => onChange(v)}
      variant="scrollable"
      allowScrollButtonsMobile
      aria-label="Run status"
      sx={{ borderBottom: 1, borderColor: "divider", minHeight: 44 }}
    >
      {order.map((k) => (
        <Tab
          key={k}
          value={k}
          sx={{ minHeight: 44, textTransform: "none" }}
          label={
            <Box component="span" sx={{ display: "inline-flex", gap: 0.75, alignItems: "center" }}>
              {k === "all" ? "All" : `${STATE[k].glyph} ${STATE[k].label}`}
              <Box component="span" sx={{ color: "text.secondary", fontVariantNumeric: "tabular-nums" }}>
                {counts[k]}
              </Box>
            </Box>
          }
        />
      ))}
    </Tabs>
  );
}

export function countStates<T>(rows: readonly T[], stateOf: (r: T) => RunState): Record<RunFilter, number> {
  const counts: Record<RunFilter, number> = { all: rows.length, running: 0, success: 0, failed: 0, interrupted: 0 };
  for (const r of rows) counts[stateOf(r)] += 1;
  return counts;
}

/** A bar with "step 12 of 40 · what it is doing"; open-ended when the run reports no steps. */
export function RunProgress({
  done,
  total,
  note,
  startedAt,
}: Readonly<{ done?: number | null; total?: number | null; note?: string | null; startedAt?: string | null }>) {
  const known = typeof done === "number" && typeof total === "number" && total > 0;
  const pct = known ? Math.min(100, Math.round((done / total) * 100)) : null;
  const elapsed = startedAt ? Math.max(0, Math.round((Date.now() - new Date(startedAt).getTime()) / 1000)) : null;
  const parts = [
    known ? `${String(pct)}% · step ${String(done)} of ${String(total)}` : "No step count reported",
    note,
    elapsed !== null && !Number.isNaN(elapsed) ? `${String(Math.floor(elapsed / 60))} m ${String(elapsed % 60)} s so far` : null,
  ].filter(Boolean);
  return (
    <Box sx={{ minWidth: 180 }}>
      <LinearProgress
        variant={known ? "determinate" : "indeterminate"}
        value={pct ?? undefined}
        aria-label="Run progress"
        sx={{ height: 6, borderRadius: 3 }}
      />
      <Typography variant="caption" component="div" sx={{ color: "text.secondary", mt: 0.5, overflowWrap: "anywhere" }}>
        {parts.join(" · ")}
      </Typography>
    </Box>
  );
}
