import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { useMemo, useState, type KeyboardEvent, type MouseEvent } from "react";
import type { WalletCharts as Charts, WalletSeries } from "../api";
import { fmtFixed, fmtRate } from "../lib/format";
import { oneOf, usePref } from "../lib/storage";
import { SERIES_SLOTS } from "../theme";
import { Segmented, niceStep, shortDay, usePalette, useSize } from "./ArenaCharts";
import { Money } from "./WalletDialogs";
import { DataTable, Na, Num, SectionCard } from "./ui";

/** Wallet history charts (WL-151): balances compared over time, then the selected wallet's result per day,
 * drawdown, money in and out, and its results by month and by pair. Hand-drawn SVG like the Arena graphs. */

type Range = "30" | "90" | "365" | "all";
const RANGES: [Range, string][] = [
  ["30", "30 d"],
  ["90", "90 d"],
  ["365", "1 y"],
  ["all", "All"],
];
const M = { top: 18, right: 12, bottom: 24, left: 56 };

type Line = { id: number | string; name: string; color: string; values: (number | null)[]; dash?: string };
type Kind = "lines" | "bars" | "area";

function money(v: number | null | undefined, digits = 2): string {
  return v === null || v === undefined ? "none" : (fmtFixed(v, digits) ?? "none");
}

/** One time chart on the shared day axis: lines (balances), bars (per day) or an area (drawdown below zero).
 * Hover or the arrow keys move a cursor; the figures above the chart follow it. */
function TimeChart({
  days,
  lines,
  kind,
  height = 220,
  label,
  barColor,
  hidden,
  onToggle,
}: Readonly<{
  days: string[];
  lines: Line[];
  kind: Kind;
  height?: number;
  label: string;
  /** Bars: the colour of a value (green or red for profit and loss). */
  barColor?: (v: number) => string;
  hidden?: Set<string>;
  onToggle?: (id: string) => void;
}>) {
  const pal = usePalette();
  const [boxRef, width] = useSize<HTMLDivElement>();
  const [cursor, setCursor] = useState<number | null>(null);
  const n = days.length;
  const shown = lines.filter((l) => !hidden?.has(String(l.id)));
  const all = [...shown.flatMap((l) => l.values.filter((v): v is number => v !== null)), 0];
  const step = niceStep(Math.max(...all) - Math.min(...all));
  const lo = Math.floor(Math.min(...all) / step) * step;
  const hi = Math.ceil(Math.max(...all) / step) * step || step;
  const plotW = Math.max(10, width - M.left - M.right);
  const plotH = height - M.top - M.bottom;
  const slot = n > 0 ? plotW / n : plotW;
  const x = (i: number) => (kind === "bars" ? M.left + (i + 0.5) * slot : M.left + (n > 1 ? (i / (n - 1)) * plotW : plotW / 2));
  const y = (v: number) => M.top + plotH - ((v - lo) / (hi - lo || 1)) * plotH;
  const path = (vs: (number | null)[]) => {
    let d = "";
    let pen = false;
    vs.forEach((v, i) => {
      if (v === null) {
        pen = false;
        return;
      }
      d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
      pen = true;
    });
    return d;
  };
  const yTicks: number[] = [];
  for (let v = lo; v <= hi + step / 2; v += step) yTicks.push(Number(v.toFixed(6)));
  const tickCount = Math.min(6, n);
  const xTicks = n ? Array.from(new Set(Array.from({ length: tickCount }, (_v, k) => Math.round((k * (n - 1)) / Math.max(1, tickCount - 1))))) : [];
  const at = cursor ?? n - 1;

  const onMove = (e: MouseEvent<SVGRectElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const f = (e.clientX - r.left) / r.width;
    const i = kind === "bars" ? Math.floor(f * n) : Math.round(f * (n - 1));
    setCursor(Math.min(n - 1, Math.max(0, i)));
  };
  const onKey = (e: KeyboardEvent<SVGSVGElement>) => {
    if (e.key === "ArrowLeft") setCursor(Math.max(0, at - 1));
    else if (e.key === "ArrowRight") setCursor(Math.min(n - 1, at + 1));
    else if (e.key === "Escape") setCursor(null);
  };

  return (
    <Box>
      <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", alignItems: "baseline", mb: 0.75, minHeight: 24 }}>
        <Typography variant="caption" sx={{ fontWeight: 600, minWidth: 72 }}>
          {n ? shortDay(days[at]) : ""}
        </Typography>
        {lines.map((l) => {
          const off = hidden?.has(String(l.id));
          const v = n ? l.values[at] : null;
          const inner = (
            <>
              <Box component="span" sx={{ width: 12, flexShrink: 0, borderTop: 3, borderStyle: l.dash ? "dashed" : "solid", borderColor: l.color }} />
              <Typography component="span" variant="caption" noWrap sx={{ maxWidth: 140 }}>
                {l.name}
              </Typography>
              <Num sx={{ fontSize: "0.75rem", fontWeight: 600 }}>{v === null || v === undefined ? "none" : money(v)}</Num>
            </>
          );
          return onToggle ? (
            <Box
              key={l.id}
              component="button"
              type="button"
              aria-pressed={!off}
              onClick={() => onToggle(String(l.id))}
              sx={{ all: "unset", cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 0.5, opacity: off ? 0.4 : 1, border: 1, borderColor: "divider", borderRadius: 1, px: 0.75, "&:hover": { bgcolor: "action.hover" }, "&:focus-visible": { outline: 2, outlineColor: "primary.main" } }}
            >
              {inner}
            </Box>
          ) : (
            <Box key={l.id} component="span" sx={{ display: "inline-flex", alignItems: "center", gap: 0.5 }}>
              {inner}
            </Box>
          );
        })}
      </Stack>
      <Box ref={boxRef} sx={{ width: "100%" }}>
        {n < 2 ? (
          <Box sx={{ height, display: "grid", placeItems: "center", color: "text.secondary", typography: "body2" }}>Fewer than two days in this range.</Box>
        ) : (
          <Box
            component="svg"
            width={width}
            height={height}
            tabIndex={0}
            role="img"
            aria-label={`${label}, ${days[0]} to ${days[n - 1]}. Use the arrow keys to move the cursor.`}
            onKeyDown={onKey}
            sx={{ display: "block", fontFamily: "inherit", "&:focus-visible": { outline: 2, outlineColor: "primary.main" } }}
          >
            {yTicks.map((v) => (
              <g key={v}>
                <line x1={M.left} x2={M.left + plotW} y1={y(v)} y2={y(v)} stroke={pal.divider} strokeWidth={v === 0 ? 1.5 : 1} />
                <text x={M.left - 6} y={y(v) + 3} fontSize={10} textAnchor="end" fill={pal.text.secondary}>
                  {fmtFixed(v, Math.abs(step) < 1 ? 2 : 0)}
                </text>
              </g>
            ))}
            {xTicks.map((i) => (
              <text key={i} x={x(i)} y={height - 6} fontSize={10} textAnchor={i === 0 ? "start" : i === n - 1 ? "end" : "middle"} fill={pal.text.secondary}>
                {shortDay(days[i])}
              </text>
            ))}
            {kind === "bars"
              ? shown.map((l) =>
                  l.values.map((v, i) =>
                    v ? (
                      <rect
                        key={`${String(l.id)}-${String(i)}`}
                        x={M.left + i * slot + (slot > 3 ? slot * 0.15 : 0)}
                        width={Math.max(1, slot > 3 ? slot * 0.7 : slot)}
                        y={Math.min(y(v), y(0))}
                        height={Math.max(1, Math.abs(y(v) - y(0)))}
                        fill={barColor ? barColor(v) : l.color}
                      />
                    ) : null,
                  ),
                )
              : null}
            {kind === "area"
              ? shown.map((l) => (
                  <g key={l.id}>
                    <path d={`${path(l.values)}L${x(n - 1).toFixed(1)},${y(0).toFixed(1)}L${x(0).toFixed(1)},${y(0).toFixed(1)}Z`} fill={l.color} fillOpacity={0.18} />
                    <path d={path(l.values)} fill="none" stroke={l.color} strokeWidth={1.5} />
                  </g>
                ))
              : null}
            {kind === "lines"
              ? shown.map((l) => <path key={l.id} d={path(l.values)} fill="none" stroke={l.color} strokeWidth={1.75} strokeDasharray={l.dash} strokeLinejoin="round" />)
              : null}
            {cursor !== null ? (
              <g>
                <line x1={x(cursor)} x2={x(cursor)} y1={M.top} y2={M.top + plotH} stroke={pal.text.secondary} strokeWidth={1} />
                {kind === "bars"
                  ? null
                  : shown.map((l) => {
                      const v = l.values[cursor];
                      return v === null ? null : <circle key={l.id} cx={x(cursor)} cy={y(v)} r={3} fill={l.color} stroke={pal.background.paper} strokeWidth={1.5} />;
                    })}
              </g>
            ) : null}
            <rect x={M.left} y={M.top} width={plotW} height={plotH} fill="transparent" onMouseMove={onMove} onMouseLeave={() => setCursor(null)} />
          </Box>
        )}
      </Box>
    </Box>
  );
}

function sliceFrom(days: string[], range: Range): number {
  if (range === "all" || !days.length) return 0;
  const last = new Date(`${days[days.length - 1]}T00:00:00`);
  last.setDate(last.getDate() - Number(range));
  const cut = last.toISOString().slice(0, 10);
  const i = days.findIndex((d) => d > cut);
  return i < 0 ? 0 : i;
}

/** The deepest fall of the trading result (closed trades only, not withdrawals) from its high so far. */
function drawdown(pnl: number[]): { values: number[]; max: number } {
  let cum = 0;
  let peak = 0;
  let max = 0;
  const values = pnl.map((p) => {
    cum += p;
    peak = Math.max(peak, cum);
    const dd = cum - peak;
    max = Math.min(max, dd);
    return Number(dd.toFixed(2));
  });
  return { values, max };
}

export function WalletBalanceChart({ charts }: Readonly<{ charts: Charts }>) {
  const pal = usePalette();
  const [range, setRange] = usePref<Range>("cca_wallet_chart_range", "all", oneOf(...RANGES.map(([k]) => k)));
  const [hiddenList, setHiddenList] = usePref<string[]>("cca_wallet_chart_hidden", []);
  const hidden = useMemo(() => new Set(hiddenList), [hiddenList]);
  const start = sliceFrom(charts.days, range);
  const days = charts.days.slice(start);
  const lines: Line[] = charts.wallets.map((w, i) => ({
    id: w.id,
    name: `${w.name} (${w.currency})`,
    color: pal.series[SERIES_SLOTS[i % SERIES_SLOTS.length]],
    dash: i >= SERIES_SLOTS.length ? "6 3" : undefined,
    values: w.balance.slice(start),
  }));
  return (
    <SectionCard
      title="Balance over time"
      right={<Segmented value={range} options={RANGES} onChange={setRange} label="Time range" />}
    >
      <Typography variant="body2" sx={{ color: "text.secondary", mb: 1 }}>
        Every wallet&apos;s balance at the end of each day: start, deposits, withdrawals and closed trades. A box hides or shows its line.
      </Typography>
      <TimeChart
        days={days}
        lines={lines}
        kind="lines"
        height={260}
        label="Wallet balances per day"
        hidden={hidden}
        onToggle={(id) => setHiddenList((h) => (h.includes(id) ? h.filter((x) => x !== id) : [...h, id]))}
      />
    </SectionCard>
  );
}

/** The selected wallet: result per day, drawdown, money in and out, and results by month and by pair. */
export function WalletHistoryCharts({ charts, wallet }: Readonly<{ charts: Charts; wallet: WalletSeries }>) {
  const pal = usePalette();
  const [range] = usePref<Range>("cca_wallet_chart_range", "all", oneOf(...RANGES.map(([k]) => k)));
  const start = sliceFrom(charts.days, range);
  const days = charts.days.slice(start);
  const pnl = wallet.pnl.slice(start);
  const dd = drawdown(wallet.pnl);
  const ddShown = dd.values.slice(start);
  const cur = wallet.currency;
  const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
  const tradeDays = pnl.filter((v) => v !== 0);
  const rangeLabel = RANGES.find(([k]) => k === range)?.[1] ?? "";

  return (
    <>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "minmax(0, 1fr)", lg: "repeat(2, minmax(0, 1fr))" } }}>
        <SectionCard title="Profit or loss per day">
          <Typography variant="body2" sx={{ color: "text.secondary", mb: 1 }}>
            Closed trades after fees, {rangeLabel}: <Money pnl={tradeDays.length ? sum(pnl) : null} reason="No closed trades in this range" /> over {tradeDays.length} trading days
            {tradeDays.length ? `, ${String(tradeDays.filter((v) => v > 0).length)} up` : ""}.
          </Typography>
          <TimeChart
            days={days}
            lines={[{ id: "pnl", name: `Result (${cur})`, color: pal.text.secondary, values: pnl }]}
            kind="bars"
            label="Profit or loss per day"
            barColor={(v) => (v > 0 ? pal.success.main : pal.error.main)}
          />
        </SectionCard>
        <SectionCard title="Drawdown">
          <Typography variant="body2" sx={{ color: "text.secondary", mb: 1 }}>
            How far the summed trade result sits below its best so far (money in and out left out). Deepest:{" "}
            <Money pnl={dd.max < 0 ? dd.max : null} reason="No drawdown yet" />.
          </Typography>
          <TimeChart days={days} lines={[{ id: "dd", name: `Below the high (${cur})`, color: pal.error.main, values: ddShown }]} kind="area" label="Drawdown per day" />
        </SectionCard>
        <SectionCard title="Money in and out">
          <Typography variant="body2" sx={{ color: "text.secondary", mb: 1 }}>
            The starting balance and deposits above the line, withdrawals below, {rangeLabel}: in {money(sum(wallet.deposits.slice(start)))}, out{" "}
            {money(-sum(wallet.withdrawals.slice(start)))} {cur}.
          </Typography>
          <TimeChart
            days={days}
            lines={[
              { id: "in", name: "In", color: pal.info.main, values: wallet.deposits.slice(start) },
              { id: "out", name: "Out", color: pal.text.secondary, values: wallet.withdrawals.slice(start) },
            ]}
            kind="bars"
            label="Deposits and withdrawals per day"
          />
        </SectionCard>
        <SectionCard title="By month" noPadding>
          {wallet.by_month.length ? (
            <DataTable minWidth={560} maxHeight={330}>
              <TableHead>
                <TableRow>
                  <TableCell>Month</TableCell>
                  <TableCell align="right">Trades</TableCell>
                  <TableCell align="right">Win rate</TableCell>
                  <TableCell align="right">Result</TableCell>
                  <TableCell align="right">In</TableCell>
                  <TableCell align="right">Out</TableCell>
                  <TableCell align="right">Balance at the end</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {[...wallet.by_month].reverse().map((m) => (
                  <TableRow key={m.month}>
                    <TableCell>
                      <Num>{m.month}</Num>
                    </TableCell>
                    <TableCell align="right">
                      <Num>{m.trades}</Num>
                    </TableCell>
                    <TableCell align="right">{m.trades ? <Num>{fmtRate((100 * m.won) / m.trades)}</Num> : <Na reason="No closed trades" />}</TableCell>
                    <TableCell align="right">{m.trades ? <Money pnl={m.pnl} /> : <Na reason="No closed trades" />}</TableCell>
                    <TableCell align="right">
                      <Num>{money(m.deposits)}</Num>
                    </TableCell>
                    <TableCell align="right">
                      <Num>{money(-m.withdrawals)}</Num>
                    </TableCell>
                    <TableCell align="right">
                      <Num sx={{ fontWeight: 600 }}>{money(m.end_balance)}</Num>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </DataTable>
          ) : (
            <Typography variant="body2" sx={{ color: "text.secondary", p: 2 }}>
              Nothing booked yet.
            </Typography>
          )}
        </SectionCard>
      </Box>
      <SectionCard title="By pair" noPadding>
        {wallet.by_pair.length ? (
          <DataTable minWidth={560} maxHeight={360}>
            <TableHead>
              <TableRow>
                <TableCell>Pair</TableCell>
                <TableCell align="right">Trades</TableCell>
                <TableCell align="right">Won</TableCell>
                <TableCell align="right">Lost</TableCell>
                <TableCell align="right">Win rate</TableCell>
                <TableCell align="right">Fees</TableCell>
                <TableCell align="right">Result</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {wallet.by_pair.map((p) => (
                <TableRow key={p.symbol}>
                  <TableCell>
                    <Num sx={{ fontWeight: 700 }}>{p.symbol}</Num>
                  </TableCell>
                  <TableCell align="right">
                    <Num>{p.trades}</Num>
                  </TableCell>
                  <TableCell align="right">
                    <Num>{p.won}</Num>
                  </TableCell>
                  <TableCell align="right">
                    <Num>{p.lost}</Num>
                  </TableCell>
                  <TableCell align="right">
                    <Num>{fmtRate((100 * p.won) / p.trades)}</Num>
                  </TableCell>
                  <TableCell align="right">
                    <Num>{money(p.fees)}</Num>
                  </TableCell>
                  <TableCell align="right">
                    <Money pnl={p.pnl} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </DataTable>
        ) : (
          <Typography variant="body2" sx={{ color: "text.secondary", p: 2 }}>
            No closed trades yet.
          </Typography>
        )}
      </SectionCard>
    </>
  );
}
