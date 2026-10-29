import Box from "@mui/material/Box";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import { useEffect, useMemo, useRef, useState, type KeyboardEvent, type MouseEvent, type RefObject } from "react";
import type { ArenaAgent, ArenaCharts, ArenaFigureSet, ArenaStanding } from "../api";
import { STYLE_LABEL, fmtFixed, fmtR, fmtRate } from "../lib/format";
import { oneOf, usePref } from "../lib/storage";
import { SERIES_SLOTS, type SeriesSlot } from "../theme";
import { Na, Num, Pill, monoSx } from "./ui";

/** The Arena graphs (WL-094): standings as bars, agents compared over time, and agents by style. */

/** R is a win or a loss: green with ▲, red with ▼ (ruleset 9). */
export function RValue({ r, digits = 2, reason = "No trades" }: Readonly<{ r: number | null | undefined; digits?: number; reason?: string }>) {
  if (r === null || r === undefined) return <Na reason={reason} />;
  const flat = r === 0;
  const up = r > 0;
  return (
    <Num sx={{ color: flat ? "text.secondary" : up ? "success.main" : "error.main", fontWeight: 600 }}>
      {flat ? "" : up ? "▲ " : "▼ "}
      {fmtR(r, digits)}
    </Num>
  );
}

export function StancePill({ a }: Readonly<{ a: Pick<ArenaAgent, "stance"> }>) {
  if (a.stance === "bull") return <Pill glyph="▲" label="bull" tone="buy" title="Mostly long" />;
  if (a.stance === "bear") return <Pill glyph="▼" label="bear" tone="sell" title="Short only" />;
  if (a.stance === "meta") return <Pill glyph="◆" label="meta" tone="info" title="Copies the other agents" />;
  return <Pill glyph="◇" label="both sides" tone="neutral" />;
}

/** Theme colours as CSS variables, so light and dark switch without a re-render. */
export function usePalette() {
  const t = useTheme();
  return t.vars?.palette ?? t.palette;
}

export function useSize<T extends HTMLElement>(): [RefObject<T | null>, number, number] {
  const ref = useRef<T>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setSize({ w: e.contentRect.width, h: e.contentRect.height }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, size.w, size.h];
}

export function ChartSkeleton({ height = 280 }: Readonly<{ height?: number }>) {
  return (
    <Stack spacing={1} aria-busy="true" aria-label="Loading">
      <Skeleton variant="rounded" height={28} width="40%" />
      <Skeleton variant="rounded" height={height} />
    </Stack>
  );
}

export function Segmented<T extends string>({ value, options, onChange, label }: Readonly<{ value: T; options: [T, string][]; onChange: (v: T) => void; label: string }>) {
  return (
    <ToggleButtonGroup exclusive size="small" value={value} aria-label={label} onChange={(_e, v: T | null) => v && onChange(v)}>
      {options.map(([k, text]) => (
        <ToggleButton key={k} value={k} sx={{ px: 1.25, py: 0.25, fontSize: "0.75rem" }}>
          {text}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}

// --- standings as bars ----------------------------------------------------------------------

type Metric = "total_r" | "avg_r" | "points" | "win_rate" | "profit_factor";
const METRICS: [Metric, string][] = [
  ["total_r", "Total R"],
  ["avg_r", "Avg R"],
  ["points", "Points"],
  ["win_rate", "Win rate"],
  ["profit_factor", "Profit factor"],
];

function fmtMetric(m: Metric, v: number | null | undefined): string | null {
  if (v === null || v === undefined) return null;
  if (m === "total_r") return fmtR(v, 1);
  if (m === "avg_r") return fmtR(v, 3);
  if (m === "win_rate") return fmtRate(v);
  if (m === "profit_factor") return fmtFixed(v, 2);
  return v.toLocaleString();
}

/** Ranked bars, like the Unefy "Highest return temperature" list; R splits around a zero line. */
export function StandingsChart({
  board,
  selected,
  onPick,
  hover = null,
  dense = false,
}: Readonly<{ board: ArenaStanding[]; selected: string | null; onPick: (id: string) => void; hover?: ChartHover; dense?: boolean }>) {
  const [chosen, setMetric] = usePref<Metric>("cca_arena_bars_metric", "total_r", oneOf(...METRICS.map(([k]) => k)));
  // WL-098: while the compare chart has a cursor, the bars are each agent's R from the range start to that day.
  const metric: Metric = hover ? "total_r" : chosen;
  const valueOf = (r: ArenaStanding): number | null => (hover ? (hover.cum[r.id] ?? null) : (r[metric] ?? null));
  const polar = metric === "total_r" || metric === "avg_r";
  const rows = [...board].sort((a, b) => {
    const x = valueOf(a);
    const y = valueOf(b);
    if (x === null) return y === null ? 0 : 1;
    if (y === null) return -1;
    return y - x;
  });
  const vals = rows.map(valueOf).filter((v): v is number => v !== null);
  const maxPos = Math.max(0, ...vals);
  const maxNeg = polar ? Math.max(0, ...vals.map((v) => -v)) : 0;
  const span = maxPos + maxNeg || 1;
  const zero = (maxNeg / span) * 100;
  const typical = median(vals);
  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: { xs: "wrap", md: "nowrap" }, rowGap: 0.5, mb: dense ? 0.5 : 1.5 }}>
        <Segmented value={chosen} options={METRICS} onChange={setMetric} label="Measure" />
        <Typography variant="caption" noWrap sx={{ flex: 1, minWidth: 0, color: hover ? "text.primary" : "text.secondary", fontWeight: hover ? 600 : 400, ...(dense ? { fontSize: "0.6875rem" } : {}) }}>
          {hover
            ? `R ${hover.from} to ${hover.day}. Median ${fmtMetric(metric, typical) ?? "none"}.`
            : `Median ${fmtMetric(metric, typical) ?? "none"}. Click an agent for its rules.`}
        </Typography>
      </Stack>
      <Box role="list" aria-label={`Agents by ${METRICS.find(([k]) => k === metric)?.[1] ?? metric}`}>
        {rows.map((r) => {
          const v = valueOf(r);
          const has = v !== null;
          const w = has ? (Math.abs(v) / span) * 100 : 0;
          const neg = has && v < 0;
          let color = "primary.main";
          if (polar) color = neg ? "error.main" : "success.main";
          return (
            <Tooltip
              key={r.id}
              placement="top-start"
              title={
                <Box sx={{ typography: "caption" }}>
                  <b>{r.name}</b>, place {r.place ?? "none"}
                  <br />
                  {r.trades.toLocaleString()} trades, {fmtRate(r.win_rate) ?? "no"} won
                  <br />
                  Total {fmtR(r.total_r, 1) ?? "none"}, avg {fmtR(r.avg_r, 3) ?? "none"}, PF {fmtFixed(r.profit_factor, 2) ?? "none"}
                  <br />
                  {r.points} points, {r.days_won} days won
                </Box>
              }
            >
              <Box
                role="listitem"
                tabIndex={0}
                onClick={() => onPick(r.id)}
                onKeyDown={(e) => e.key === "Enter" && onPick(r.id)}
                sx={{
                  display: "grid",
                  gridTemplateColumns: dense ? { xs: "96px 1fr 72px", sm: "120px 1fr 84px" } : { xs: "96px 1fr 84px", sm: "150px 1fr 110px" },
                  alignItems: "center",
                  gap: dense ? 1 : 1.5,
                  px: 1,
                  minHeight: dense ? 15 : 32,
                  ...(dense ? { "& *": { fontSize: "0.6875rem", lineHeight: 1.25 } } : {}),
                  borderRadius: 1,
                  cursor: "pointer",
                  bgcolor: selected === r.id ? "surface.action" : "transparent",
                  "&:hover": { bgcolor: "action.hover" },
                  "&:focus-visible": { outline: 2, outlineColor: "primary.main" },
                }}
              >
                <Typography variant="body2" noWrap sx={{ fontWeight: selected === r.id ? 700 : 500 }}>
                  {r.name}
                </Typography>
                <Box sx={{ position: "relative", height: dense ? 12 : 14 }}>
                  {polar && maxNeg > 0 ? (
                    <Box sx={{ position: "absolute", left: `${String(zero)}%`, top: -4, bottom: -4, width: "1px", bgcolor: "divider" }} />
                  ) : null}
                  {has ? (
                    <Box
                      sx={{
                        position: "absolute",
                        top: 1,
                        bottom: 1,
                        left: neg ? `${String(zero - w)}%` : `${String(zero)}%`,
                        width: `max(2px, ${String(w)}%)`,
                        bgcolor: color,
                        borderRadius: neg ? "4px 0 0 4px" : "0 4px 4px 0",
                      }}
                    />
                  ) : null}
                </Box>
                <Box sx={{ textAlign: "right", whiteSpace: "nowrap" }}>
                  {polar ? <RValue r={v} digits={metric === "avg_r" ? 3 : 1} /> : <V2 value={fmtMetric(metric, v)} reason={r.trades ? "No losing trades" : "No trades"} />}
                </Box>
              </Box>
            </Tooltip>
          );
        })}
      </Box>
    </Box>
  );
}

function V2({ value, reason }: Readonly<{ value: string | null; reason: string }>) {
  return value === null ? <Na reason={reason} /> : <Num>{value}</Num>;
}

function median(xs: number[]): number | null {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

// --- agents compared over time ----------------------------------------------------------------

type Range = "30" | "90" | "365" | "all";
const RANGES: [Range, string][] = [
  ["30", "30 d"],
  ["90", "90 d"],
  ["365", "1 y"],
  ["all", "All"],
];
const M = { top: 18, right: 16, bottom: 24, left: 48 };

/** WL-098: the compare chart's cursor, shared with the standings bars: cumulative R per agent from `from` to `day`. */
export type ChartHover = { day: string; from: string; cum: Record<string, number> } | null;

/** Line look for the n-th agent: the 8 theme series colours solid, then the same colours dashed (WL-098: 14 agents). */
function lineLook(idx: number): { slot: SeriesSlot; dash?: string } {
  return { slot: SERIES_SLOTS[idx % SERIES_SLOTS.length], dash: idx >= SERIES_SLOTS.length ? "6 3" : undefined };
}

export function niceStep(span: number): number {
  const raw = span / 5 || 1;
  const p = 10 ** Math.floor(Math.log10(raw));
  const f = raw / p;
  return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p;
}

export function shortDay(d: string): string {
  const dt = new Date(`${d}T00:00:00`);
  return dt.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "2-digit" });
}

function Swatch({ color, dash }: Readonly<{ color: string; dash?: boolean }>) {
  return <Box component="span" sx={{ width: 14, flexShrink: 0, borderTop: 3, borderStyle: dash ? "dashed" : "solid", borderColor: color }} />;
}

const BOX_SX = {
  border: 1,
  borderColor: "divider",
  borderRadius: 1,
  px: 0.75,
  py: 0.25,
  minWidth: 0,
  textAlign: "left",
  cursor: "pointer",
  bgcolor: "transparent",
  color: "text.primary",
  font: "inherit",
  "&:hover": { bgcolor: "action.hover" },
  "&:focus-visible": { outline: 2, outlineColor: "primary.main" },
} as const;
const SMALL = { fontSize: "0.6875rem", lineHeight: 1.3, "& *": { fontSize: "inherit" } } as const;

/** Cumulative R over the scored days for every agent, with the median agent as a dashed line (like the Unefy HIU chart).
 * The boxes above it show each agent's figure at the cursor (the last day when the cursor is off the chart). */
export function CompareChart({
  charts,
  agents,
  initial,
  height = 260,
  fill = false,
  onHover,
}: Readonly<{ charts: ArenaCharts; agents: ArenaAgent[]; initial: string[]; height?: number; fill?: boolean; onHover?: (h: ChartHover) => void }>) {
  const pal = usePalette();
  // WL-101: hidden lines, range and the median line kept per browser.
  const [hiddenList, setHiddenList] = usePref<string[]>("cca_arena_compare_hidden", []);
  const hidden = useMemo(() => new Set(hiddenList), [hiddenList]);
  const setHidden = (h: Set<string>) => setHiddenList([...h]);
  const [range, setRange] = usePref<Range>("cca_arena_compare_range", "all", oneOf(...RANGES.map(([k]) => k)));
  const [showTypical, setShowTypical] = usePref("cca_arena_compare_median", true);
  const [cursor, setCursor] = useState<number | null>(null);
  const [boxRef, width, boxH] = useSize<HTMLDivElement>();
  const names = Object.fromEntries(agents.map((a) => [a.id, a.name]));
  // WL-099: with `fill` the chart takes the card's free height (set by the standings next to it), at least `height`.
  const H = fill ? Math.max(height, Math.floor(boxH)) : height;

  // Every agent with trades, leaders first (WL-098: all by default); a box hides or shows its line.
  const order = useMemo(() => {
    const seen = new Set(initial);
    return [...initial, ...agents.map((a) => a.id).filter((id) => !seen.has(id))].filter((id) => charts.series.r[id]);
  }, [initial, agents, charts]);
  const toggle = (id: string) => setHiddenList((h) => (h.includes(id) ? h.filter((x) => x !== id) : [...h, id]));

  const days = charts.series.days;
  const start = useMemo(() => {
    if (range === "all" || !days.length) return 0;
    const last = new Date(`${days[days.length - 1]}T00:00:00`);
    last.setDate(last.getDate() - Number(range));
    const cut = last.toISOString().slice(0, 10);
    const i = days.findIndex((d) => d > cut);
    return i < 0 ? 0 : i;
  }, [days, range]);
  const shown = useMemo(() => days.slice(start), [days, start]);
  const n = shown.length;

  const cum = useMemo(() => {
    const out: Record<string, number[]> = {};
    for (const [id, rs] of Object.entries(charts.series.r)) {
      let s = 0;
      out[id] = rs.slice(start).map((r) => (s += r ?? 0));
    }
    return out;
  }, [charts, start]);
  const typical = useMemo(
    () => shown.map((_d, i) => median(Object.values(cum).map((c) => c[i])) ?? 0),
    [cum, shown],
  );

  useEffect(() => {
    if (!onHover) return;
    if (cursor === null || cursor >= n) onHover(null);
    else onHover({ day: shown[cursor], from: shown[0], cum: Object.fromEntries(Object.entries(cum).map(([id, c]) => [id, c[cursor]])) });
  }, [cursor, cum, shown, n, onHover]);

  const lines = order.map((id, i) => ({ id, ...lineLook(i), values: cum[id] })).filter((l) => l.values && !hidden.has(l.id));
  const all = [...lines.flatMap((l) => l.values), ...(showTypical ? typical : []), 0];
  const step = niceStep(Math.max(...all) - Math.min(...all));
  const lo = Math.floor(Math.min(...all) / step) * step;
  const hi = Math.ceil(Math.max(...all) / step) * step || step;
  const plotW = Math.max(10, width - M.left - M.right);
  const plotH = H - M.top - M.bottom;
  const x = (i: number) => M.left + (n > 1 ? (i / (n - 1)) * plotW : plotW / 2);
  const y = (v: number) => M.top + plotH - ((v - lo) / (hi - lo || 1)) * plotH;
  const path = (vs: number[]) => vs.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
  const yTicks: number[] = [];
  for (let v = lo; v <= hi + step / 2; v += step) yTicks.push(Number(v.toFixed(6)));
  const xTicks = n ? Array.from(new Set(Array.from({ length: Math.min(6, n) }, (_v, k) => Math.round((k * (n - 1)) / Math.max(1, Math.min(6, n) - 1))))) : [];

  const at = cursor ?? n - 1;
  const onMove = (e: MouseEvent<SVGRectElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const i = Math.round(((e.clientX - r.left) / r.width) * (n - 1));
    setCursor(Math.min(n - 1, Math.max(0, i)));
  };
  const onKey = (e: KeyboardEvent<SVGSVGElement>) => {
    if (e.key === "ArrowLeft") setCursor(Math.max(0, at - 1));
    else if (e.key === "ArrowRight") setCursor(Math.min(n - 1, at + 1));
    else if (e.key === "Escape") setCursor(null);
  };
  const when = n ? shortDay(shown[at]) : "";

  // WL-099: every row keeps one line and every box two, hovered or not, so nothing on the page moves.
  return (
    <Box sx={fill ? { display: "flex", flexDirection: "column", height: "100%" } : undefined}>
      <Stack direction="row" spacing={0.75} sx={{ alignItems: "center", flexWrap: { xs: "wrap", md: "nowrap" }, rowGap: 0.5, mb: 1 }}>
        <Typography variant="caption" noWrap sx={{ color: "text.secondary", flex: 1, minWidth: 0 }}>
          <Box component="span" sx={{ fontWeight: 600, display: "inline-block", minWidth: 72 }}>
            {when}
          </Box>{" "}
          R summed over {n.toLocaleString()} days. Hover moves the figures; a box hides its line.
        </Typography>
        <Box component="button" type="button" onClick={() => setHidden(new Set())} sx={[BOX_SX, SMALL]}>
          All
        </Box>
        <Box component="button" type="button" onClick={() => setHidden(new Set(order))} sx={[BOX_SX, SMALL]}>
          None
        </Box>
        <Segmented value={range} options={RANGES} onChange={setRange} label="Time range" />
      </Stack>
      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(96px, 1fr))", gap: 0.5, mb: 1 }}>
        {order.map((id, i) => {
          const look = lineLook(i);
          const off = hidden.has(id);
          const v = n ? cum[id]?.[at] : null;
          const day = n ? charts.series.r[id]?.[start + at] : undefined;
          return (
            <Box key={id} component="button" type="button" aria-pressed={!off} onClick={() => toggle(id)} sx={[BOX_SX, { opacity: off ? 0.4 : 1, height: 36, overflow: "hidden" }]}>
              <Stack direction="row" spacing={0.5} sx={{ alignItems: "center", minWidth: 0 }}>
                <Swatch color={pal.series[look.slot]} dash={Boolean(look.dash)} />
                <Typography noWrap sx={[SMALL, { fontWeight: 600 }]}>
                  {names[id] ?? id}
                </Typography>
              </Stack>
              <Stack direction="row" spacing={0.5} sx={[SMALL, { alignItems: "baseline", whiteSpace: "nowrap", overflow: "hidden" }]}>
                <RValue r={v} digits={v !== null && v !== undefined && Math.abs(v) >= 100 ? 0 : 1} />
                {day === undefined ? null : (
                  <span title={`R on ${when}`}>
                    <Num sx={{ color: "text.secondary" }}>{day === null ? "none" : (fmtR(day, 1) ?? "").replace(/R$/, "")}</Num>
                  </span>
                )}
              </Stack>
            </Box>
          );
        })}
        <Box component="button" type="button" aria-pressed={showTypical} onClick={() => setShowTypical(!showTypical)} sx={[BOX_SX, { opacity: showTypical ? 1 : 0.4, height: 36, overflow: "hidden" }]}>
          <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
            <Box component="span" sx={{ width: 14, flexShrink: 0, borderTop: 2, borderStyle: "dashed", borderColor: "text.secondary" }} />
            <Typography noWrap sx={[SMALL, { fontWeight: 600 }]}>
              Median agent
            </Typography>
          </Stack>
          <Box sx={SMALL}>
            <RValue r={n ? typical[at] : null} digits={1} />
          </Box>
        </Box>
      </Box>
      <Box ref={boxRef} sx={{ position: "relative", width: "100%", ...(fill ? { flex: 1, minHeight: height } : {}) }}>
        {n < 2 ? (
          <Box sx={{ height: H, display: "grid", placeItems: "center", color: "text.secondary", typography: "body2" }}>
            Fewer than two scored days in this range.
          </Box>
        ) : (
          <Box
            component="svg"
            width={width}
            height={H}
            tabIndex={0}
            role="img"
            aria-label={`Cumulative R per scored day, ${shown[0]} to ${shown[n - 1]}. Use the arrow keys to move the cursor.`}
            onKeyDown={onKey}
            sx={{ display: "block", fontFamily: "inherit", ...(fill ? { position: "absolute", top: 0, left: 0 } : {}), "&:focus-visible": { outline: 2, outlineColor: "primary.main" } }}
          >
            {yTicks.map((v) => (
              <g key={v}>
                <line x1={M.left} x2={M.left + plotW} y1={y(v)} y2={y(v)} stroke={pal.divider} strokeWidth={v === 0 ? 1.5 : 1} />
                <text x={M.left - 6} y={y(v) + 3} fontSize={10} textAnchor="end" fill={pal.text.secondary}>
                  {fmtR(v, Math.abs(step) < 1 ? 1 : 0)}
                </text>
              </g>
            ))}
            {xTicks.map((i) => (
              <text key={i} x={x(i)} y={H - 6} fontSize={10} textAnchor={i === 0 ? "start" : i === n - 1 ? "end" : "middle"} fill={pal.text.secondary}>
                {shortDay(shown[i])}
              </text>
            ))}
            {showTypical ? <path d={path(typical)} fill="none" stroke={pal.text.secondary} strokeWidth={1.5} strokeDasharray="5 4" /> : null}
            {lines.map((l) => (
              <path key={l.id} d={path(l.values)} fill="none" stroke={pal.series[l.slot]} strokeWidth={1.75} strokeDasharray={l.dash} strokeLinejoin="round" />
            ))}
            {cursor !== null ? (
              <g>
                <line x1={x(cursor)} x2={x(cursor)} y1={M.top} y2={M.top + plotH} stroke={pal.text.secondary} strokeWidth={1} />
                <text x={x(cursor)} y={M.top - 6} fontSize={10} fontWeight={600} textAnchor={x(cursor) > width / 2 ? "end" : "start"} fill={pal.text.primary}>
                  {shortDay(shown[cursor])}
                </text>
                {lines.map((l) => (
                  <circle key={l.id} cx={x(cursor)} cy={y(l.values[cursor])} r={3} fill={pal.series[l.slot]} stroke={pal.background.paper} strokeWidth={1.5} />
                ))}
              </g>
            ) : null}
            <rect x={M.left} y={M.top} width={plotW} height={plotH} fill="transparent" onMouseMove={onMove} onMouseLeave={() => setCursor(null)} />
          </Box>
        )}
      </Box>
    </Box>
  );
}

// --- agents by style -----------------------------------------------------------------------

type GridMetric = "avg_r" | "total_r" | "win_rate";
const GRID_STYLES = ["scalp", "day", "swing", "position", "hold"] as const;
const AVG_BINS = [0.02, 0.05, 0.1, 0.2];
const MIX = [0, 22, 45, 72, 100];

function level(metric: GridMetric, v: number, maxAbs: number): number {
  const a = Math.abs(v);
  if (metric === "avg_r") return AVG_BINS.filter((b) => a >= b).length;
  const rel = maxAbs ? a / maxAbs : 0;
  return [0.05, 0.25, 0.5, 0.75].filter((b) => rel >= b).length;
}

function sumFigures(cells: ArenaFigureSet[]): ArenaFigureSet | null {
  const n = cells.reduce((s, c) => s + c.trades, 0);
  if (!n) return null;
  const w = cells.reduce((s, c) => s + c.wins, 0);
  const r = cells.reduce((s, c) => s + c.total_r, 0);
  return { trades: n, wins: w, win_rate: (100 * w) / n, total_r: r, avg_r: r / n };
}

/** WL-100: each agent's figures per style over the close days from `from` to `day`, from the per-day style cells. */
function matrixBetween(charts: ArenaCharts, from: string, day: string): ArenaCharts["matrix"] {
  const out: ArenaCharts["matrix"] = [];
  for (const [agent_id, byStyle] of Object.entries(charts.styles)) {
    for (const [style, cells] of Object.entries(byStyle)) {
      let n = 0;
      let w = 0;
      let r = 0;
      for (const [d, dn, dw, dr] of cells ?? []) {
        if (d < from || d > day) continue;
        n += dn;
        w += dw;
        r += dr;
      }
      const f = sumFigures([{ trades: n, wins: w, total_r: r }]);
      if (f) out.push({ ...f, agent_id, style: style as ArenaCharts["matrix"][number]["style"] });
    }
  }
  return out;
}

/** Agents by style as a tile grid, like the Unefy HIU network: diverging loss and win colour with glyphs.
 * WL-100: while the compare chart has a cursor, the tiles cover the range start to that day. */
export function StyleGrid({
  charts,
  board,
  selected,
  onPick,
  hover = null,
  dense = false,
}: Readonly<{ charts: ArenaCharts; board: ArenaStanding[]; selected: string | null; onPick: (id: string) => void; hover?: ChartHover; dense?: boolean }>) {
  const pal = usePalette();
  const [metric, setMetric] = usePref<GridMetric>("cca_arena_grid_metric", "avg_r", oneOf("avg_r", "total_r", "win_rate"));
  const hoverMatrix = useMemo(() => (hover ? matrixBetween(charts, hover.from, hover.day) : null), [charts, hover]);
  const matrix = hoverMatrix ?? charts.matrix;
  const cell = (agent: string, style: string) => matrix.find((m) => m.agent_id === agent && m.style === style) ?? null;
  const rows = board.filter((r) => charts.matrix.some((m) => m.agent_id === r.id));
  const valueOf = (f: ArenaFigureSet | null) => (f ? (metric === "win_rate" ? (f.win_rate ?? null) : (f[metric] ?? null)) : null);
  const allVals = matrix.map((m) => valueOf(m)).filter((v): v is number => v !== null);
  const maxAbs = Math.max(0, ...allVals.map(Math.abs));

  const tileSx = (v: number | null) => {
    if (v === null) return { bgcolor: "transparent", border: 1, borderStyle: "dashed", borderColor: "divider", color: "text.secondary" };
    if (metric === "win_rate") {
      const lv = [20, 40, 60, 80].filter((b) => v >= b).length;
      return {
        bgcolor: `color-mix(in srgb, ${pal.primary.main} ${String(MIX[lv])}%, ${pal.background.paper})`,
        color: lv >= 3 ? pal.primary.contrastText : pal.text.primary,
      };
    }
    const lv = level(metric, v, maxAbs);
    const base = v > 0 ? pal.success : pal.error;
    return {
      bgcolor: lv ? `color-mix(in srgb, ${base.main} ${String(MIX[lv])}%, ${pal.background.paper})` : "surface.paper2",
      color: lv >= 3 ? base.contrastText : pal.text.primary,
    };
  };
  const show = (v: number | null) => {
    if (v === null) return "";
    if (metric === "win_rate") return fmtRate(v) ?? "";
    const s = metric === "avg_r" ? fmtR(v, 3) : fmtR(v, 0);
    return `${v > 0 ? "▲" : v < 0 ? "▼" : ""} ${s ?? ""}`;
  };
  const cols: { key: string; label: string; get: (id: string) => ArenaFigureSet | null }[] = [
    ...GRID_STYLES.map((s) => ({ key: s, label: STYLE_LABEL[s] ?? s, get: (id: string) => cell(id, s) })),
    { key: "all", label: "All styles", get: (id: string) => sumFigures(matrix.filter((m) => m.agent_id === id)) },
  ];
  const colTotal = (key: string) => sumFigures(matrix.filter((m) => key === "all" || m.style === key));
  const legend =
    metric === "win_rate"
      ? ["< 20%", "20 to 40%", "40 to 60%", "60 to 80%", "≥ 80%"].map((t, i) => ({ t, sx: { bgcolor: `color-mix(in srgb, ${pal.primary.main} ${String(MIX[i])}%, ${pal.background.paper})` } }))
      : [
          ...[4, 3, 2, 1].map((lv) => ({ t: `▼ ${metric === "avg_r" ? `≤ -${String(AVG_BINS[lv - 1])}` : `${String([5, 25, 50, 75][lv - 1])}%+ of max`}`, sx: { bgcolor: `color-mix(in srgb, ${pal.error.main} ${String(MIX[lv])}%, ${pal.background.paper})` } })),
          { t: "about 0", sx: { bgcolor: "surface.paper2" } },
          ...[1, 2, 3, 4].map((lv) => ({ t: `▲ ${metric === "avg_r" ? `≥ +${String(AVG_BINS[lv - 1])}` : `${String([5, 25, 50, 75][lv - 1])}%+ of max`}`, sx: { bgcolor: `color-mix(in srgb, ${pal.success.main} ${String(MIX[lv])}%, ${pal.background.paper})` } })),
        ];

  const small = dense ? { fontSize: "0.6875rem" } : {};
  const legendEl = (
    <Stack direction="row" spacing={dense ? 1 : 1.5} sx={{ flexWrap: "wrap", rowGap: 0.5, alignItems: "center" }}>
      {legend.map((l) => (
        <Stack key={l.t} direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
          <Box sx={[l.sx, { width: 12, height: 12, borderRadius: 0.5, border: 1, borderColor: "divider" }]} />
          <Typography variant="caption" sx={{ color: "text.secondary", ...small }}>
            {l.t}
          </Typography>
        </Stack>
      ))}
      <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
        <Box sx={{ width: 12, height: 12, borderRadius: 0.5, border: 1, borderStyle: "dashed", borderColor: "divider" }} />
        <Typography variant="caption" sx={{ color: "text.secondary", ...small }}>
          no trades
        </Typography>
      </Stack>
    </Stack>
  );

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap", rowGap: 1, mb: dense ? 0.75 : 1.5 }}>
        <Segmented
          value={metric}
          options={[
            ["avg_r", "Avg R a trade"],
            ["total_r", "Total R"],
            ["win_rate", "Win rate"],
          ]}
          onChange={setMetric}
          label="Measure"
        />
        <Typography variant="caption" noWrap sx={{ minWidth: 0, color: hover ? "text.primary" : "text.secondary", fontWeight: hover ? 600 : 400, ...small }}>
          {hover ? `Every style, ${hover.from} to ${hover.day}.` : "Every style, whatever the style tab says. Hover a tile for its figures."}
        </Typography>
        {dense ? (
          <>
            <Box sx={{ flex: 1 }} />
            {legendEl}
          </>
        ) : null}
      </Stack>
      <Box sx={{ overflowX: "auto" }}>
        <Box
          role="table"
          aria-label="Agents by style"
          sx={{ display: "grid", gridTemplateColumns: `minmax(120px, 160px) repeat(${String(cols.length)}, minmax(84px, 1fr))`, gap: dense ? "2px" : 0.75, minWidth: 600 }}
        >
          <Box role="columnheader" />
          {cols.map((c) => {
            const tot = colTotal(c.key);
            return (
              <Box role="columnheader" key={c.key} sx={{ textAlign: "center", pb: dense ? 0.25 : 0.5, ...(dense ? { display: "flex", justifyContent: "center", alignItems: "baseline", gap: 0.75 } : {}) }}>
                <Typography variant={dense ? "caption" : "body2"} component="div" sx={{ fontWeight: 700, ...(c.key === "all" ? { color: "text.secondary" } : {}) }}>
                  {c.label}
                </Typography>
                <Typography variant="caption" component="div" sx={[monoSx, { color: "text.secondary", ...small }]}>
                  {tot ? show(valueOf(tot)) : "no trades"}
                </Typography>
              </Box>
            );
          })}
          {rows.map((r) => (
            <Box role="row" key={r.id} sx={{ display: "contents" }}>
              <Box
                role="rowheader"
                tabIndex={0}
                onClick={() => onPick(r.id)}
                onKeyDown={(e) => e.key === "Enter" && onPick(r.id)}
                sx={{ display: "flex", alignItems: "center", cursor: "pointer", pr: 1, borderRadius: 1, "&:hover": { bgcolor: "action.hover" } }}
              >
                <Typography variant={dense ? "caption" : "body2"} noWrap sx={{ fontWeight: selected === r.id ? 700 : 500, color: selected === r.id ? "primary.main" : "text.primary", ...small, ...(dense ? { lineHeight: 1.25 } : {}) }}>
                  {r.name}
                </Typography>
              </Box>
              {cols.map((c) => {
                const f = c.get(r.id);
                const v = valueOf(f);
                return (
                  <Tooltip
                    key={c.key}
                    title={
                      f ? (
                        <Box sx={{ typography: "caption" }}>
                          <b>{r.name}</b>, {c.label}
                          <br />
                          {f.trades.toLocaleString()} trades, {fmtRate(f.win_rate) ?? "no"} won
                          <br />
                          Total {fmtR(f.total_r, 1)}, avg {fmtR(f.avg_r, 3) ?? "none"}
                        </Box>
                      ) : (
                        "No trades in this style for these filters"
                      )
                    }
                  >
                    <Box
                      role="cell"
                      tabIndex={0}
                      sx={[
                        tileSx(v),
                        {
                          borderRadius: 1,
                          px: 1,
                          py: dense ? 0 : 0.75,
                          minHeight: dense ? 15 : 48,
                          ...(dense ? { display: "flex", alignItems: "center", justifyContent: "center", gap: 0.75 } : {}),
                          textAlign: "center",
                          outline: selected === r.id ? 2 : 0,
                          outlineColor: "primary.main",
                          outlineOffset: -2,
                          "&:focus-visible": { outline: 2, outlineColor: "primary.main" },
                        },
                      ]}
                    >
                      <Typography variant="caption" component="div" sx={[monoSx, { opacity: 0.8, lineHeight: 1.2, ...(dense ? { fontSize: "0.625rem" } : {}) }]}>
                        {f ? `${f.trades.toLocaleString()} tr` : ""}
                      </Typography>
                      <Box sx={[monoSx, { fontWeight: 700, fontSize: dense ? "0.6875rem" : "0.875rem", lineHeight: dense ? 1.2 : 1.4 }]}>{v === null ? "—" : show(v)}</Box>
                    </Box>
                  </Tooltip>
                );
              })}
            </Box>
          ))}
        </Box>
      </Box>
      {dense ? null : <Box sx={{ mt: 1.5 }}>{legendEl}</Box>}
    </Box>
  );
}
