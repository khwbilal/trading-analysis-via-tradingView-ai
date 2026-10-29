import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useEffect, useRef, useState, type MouseEvent } from "react";
import type { Bar } from "../api";
import { fmtPx } from "../lib/format";
import { usePalette } from "./ArenaCharts";

/** A level drawn across the chart. `tone` picks the theme colour: green and red only for target and stop. */
export type ChartLevel = { label: string; price: number; tone: "buy" | "sell" | "primary" | "warn" | "neutral"; dash?: boolean };

const M = { top: 12, right: 104, bottom: 22, left: 8 };
const LABEL_GAP = 11; // px between two level labels

/** The final TP projection (WL-106): a dashed line from the entry at the call to the target, past the last candle. */
export type ChartProjection = { from: number; to: number; label: string };

/** Label heights pushed apart so no two overlap, keeping their order (WL-106). */
function spread(ys: number[], top: number, bottom: number): number[] {
  const order = ys.map((v, i) => [v, i] as const).sort((a, b) => a[0] - b[0]);
  const out = [...ys];
  let prev = -Infinity;
  for (const [v, i] of order) {
    const at = Math.max(v, prev + LABEL_GAP);
    out[i] = at;
    prev = at;
  }
  const over = prev - bottom;
  if (over > 0) for (const [, i] of order) out[i] = Math.max(top, out[i] - over);
  return out;
}

/**
 * Candles from before the call up to now, with the call time and the plan's levels (WL-107), drawn from the
 * call onward as on Nadeem Gujjar's charts, with the entry zone and the final TP projection (WL-106).
 * Plain SVG, theme colours.
 */
export default function SignalChart({
  bars,
  calledAt,
  levels,
  hitAt,
  zone = null,
  projection = null,
  height = 320,
}: Readonly<{
  bars: Bar[];
  calledAt: number;
  levels: ChartLevel[];
  hitAt?: number | null;
  zone?: [number, number] | null;
  projection?: ChartProjection | null;
  height?: number;
}>) {
  const pal = usePalette();
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  const [cursor, setCursor] = useState<number | null>(null);
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const n = bars.length;
  const future = projection ? Math.max(8, Math.round(n * 0.25)) : 0; // room for the projection
  const prices = [
    ...bars.flatMap((b) => [b[2], b[3]]),
    ...levels.map((l) => l.price),
    ...(zone ?? []),
    ...(projection ? [projection.to] : []),
  ];
  const lo = Math.min(...prices);
  const hi = Math.max(...prices);
  const pad = (hi - lo) * 0.04 || hi * 0.01 || 1;
  const yLo = lo - pad;
  const yHi = hi + pad;
  const plotW = Math.max(10, width - M.left - M.right);
  const plotH = height - M.top - M.bottom;
  const slot = n ? plotW / (n + future) : plotW;
  const x = (i: number) => M.left + (i + 0.5) * slot;
  const y = (v: number) => M.top + ((yHi - v) / (yHi - yLo || 1)) * plotH;
  const indexAt = (t: number) => {
    const i = bars.findIndex((b) => b[0] >= t);
    return i < 0 ? n - 1 : i;
  };
  const callIdx = n ? indexAt(calledAt) : 0;
  const hitIdx = hitAt && n ? indexAt(hitAt) : null;
  const toneColor = (tone: ChartLevel["tone"]) =>
    ({ buy: pal.success.main, sell: pal.error.main, primary: pal.primary.main, warn: pal.warning.main, neutral: pal.text.secondary })[tone];
  const shown = cursor !== null ? bars[cursor] : bars[n - 1];
  const fromX = x(callIdx);
  const endX = M.left + plotW;
  const labelY = spread(levels.map((l) => y(l.price)), M.top + 4, M.top + plotH);
  const onMove = (e: MouseEvent<SVGRectElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    setCursor(Math.min(n - 1, Math.max(0, Math.floor(((e.clientX - r.left) / r.width) * (n + future)))));
  };

  return (
    <Box>
      <Stack direction="row" spacing={1.5} sx={{ mb: 0.5, typography: "caption", color: "text.secondary", flexWrap: "wrap" }}>
        {shown ? (
          <>
            <span>{new Date(shown[0]).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}</span>
            <span>O {fmtPx(shown[1])}</span>
            <span>H {fmtPx(shown[2])}</span>
            <span>L {fmtPx(shown[3])}</span>
            <span>C {fmtPx(shown[4])}</span>
          </>
        ) : null}
      </Stack>
      <Box ref={box} sx={{ width: "100%" }}>
        {n < 2 ? (
          <Box sx={{ height, display: "grid", placeItems: "center", color: "text.secondary", typography: "body2" }}>
            No candles for this pair from Binance.
          </Box>
        ) : (
          <svg width={width} height={height} role="img" aria-label="Candles since the call with entry, stop and target" style={{ display: "block" }}>
            {/* the time after the call */}
            <rect x={x(callIdx) - slot / 2} y={M.top} width={Math.max(0, M.left + plotW - (x(callIdx) - slot / 2))} height={plotH} fill={pal.action.hover} />
            <line x1={x(callIdx)} x2={x(callIdx)} y1={M.top} y2={M.top + plotH} stroke={pal.text.secondary} strokeDasharray="3 3" />
            <text x={x(callIdx) + 4} y={M.top + 10} fontSize={10} fill={pal.text.secondary}>
              call
            </text>
            {hitIdx !== null ? <line x1={x(hitIdx)} x2={x(hitIdx)} y1={M.top} y2={M.top + plotH} stroke={pal.text.primary} strokeDasharray="1 3" /> : null}
            {bars.map((b, i) => {
              const up = b[4] >= b[1];
              const color = up ? pal.success.main : pal.error.main;
              const top = y(Math.max(b[1], b[4]));
              return (
                <g key={b[0]}>
                  <line x1={x(i)} x2={x(i)} y1={y(b[2])} y2={y(b[3])} stroke={color} strokeWidth={1} />
                  <rect x={x(i) - Math.max(1, slot * 0.35)} y={top} width={Math.max(2, slot * 0.7)} height={Math.max(1, y(Math.min(b[1], b[4])) - top)} fill={color} />
                </g>
              );
            })}
            {zone ? (
              <rect x={fromX} y={y(zone[1])} width={Math.max(0, endX - fromX)} height={Math.max(1, y(zone[0]) - y(zone[1]))} fill={pal.primary.main} opacity={0.14}>
                <title>
                  Entry zone {fmtPx(zone[0])} to {fmtPx(zone[1])}
                </title>
              </rect>
            ) : null}
            {levels.map((l, i) => (
              <g key={l.label}>
                <line x1={fromX} x2={endX} y1={y(l.price)} y2={y(l.price)} stroke={toneColor(l.tone)} strokeWidth={1.25} strokeDasharray={l.dash ? "5 4" : undefined} />
                <text x={endX + 4} y={labelY[i] + 3} fontSize={10} fill={toneColor(l.tone)}>
                  {l.label} {fmtPx(l.price)}
                </text>
              </g>
            ))}
            {projection ? (
              <g>
                <defs>
                  <marker id="projArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                    <path d="M0,0 L10,5 L0,10 z" fill={pal.primary.main} />
                  </marker>
                </defs>
                <line x1={fromX} y1={y(projection.from)} x2={endX - 2} y2={y(projection.to)} stroke={pal.primary.main} strokeWidth={1.5} strokeDasharray="6 4" markerEnd="url(#projArrow)">
                  <title>{projection.label}</title>
                </line>
              </g>
            ) : null}
            {cursor !== null ? <line x1={x(cursor)} x2={x(cursor)} y1={M.top} y2={M.top + plotH} stroke={pal.text.secondary} /> : null}
            <rect x={M.left} y={M.top} width={plotW} height={plotH} fill="transparent" onMouseMove={onMove} onMouseLeave={() => setCursor(null)} />
          </svg>
        )}
      </Box>
      <Typography variant="caption" sx={{ color: "text.secondary" }}>
        The shaded part is after the call{projection ? "; the dashed arrow is the projection to the final TP" : ""}. Hover for a candle&apos;s prices.
      </Typography>
    </Box>
  );
}
