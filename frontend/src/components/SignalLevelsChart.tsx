import Box from "@mui/material/Box";
import Checkbox from "@mui/material/Checkbox";
import Chip from "@mui/material/Chip";
import FormControlLabel from "@mui/material/FormControlLabel";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import {
  ColorType,
  CrosshairMode,
  createChart,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  type SeriesMarker,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Bar, DecisionLevel } from "../api";
import { EmptyState } from "./ui";

/** Default window so the setup isn't crushed on the far right. */
const VIEW_BARS = 80;

function fmtAxis(price: number): string {
  const a = Math.abs(price);
  if (a >= 1000) return price.toFixed(2);
  if (a >= 1) return price.toFixed(4);
  if (a >= 0.01) return price.toFixed(5);
  return price.toFixed(6);
}

function fmtWhen(ms: number): string {
  return new Date(ms).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function lineColorForKind(
  kind: string,
  levels: { entry: string; stop: string; target: string; support: string; res: string; ema20: string },
  textSecondary: string,
): string {
  if (kind === "entry") return levels.entry;
  if (kind === "stop") return levels.stop;
  if (kind === "target") return levels.target;
  if (kind === "support") return levels.support;
  if (kind === "resistance") return levels.res;
  if (kind === "fib" || kind === "trend") return levels.ema20;
  return textSecondary;
}

function indexAtOrAfter(bars: Bar[], ms: number): number {
  if (!bars.length) return -1;
  const i = bars.findIndex((b) => b[0] >= ms);
  return i < 0 ? bars.length - 1 : i;
}

function entryFillIndex(bars: Bar[], setupIdx: number, entry: number, bias?: string | null): number {
  if (setupIdx < 0 || !Number.isFinite(entry)) return -1;
  const buy = (bias || "").toLowerCase() !== "sell";
  for (let i = setupIdx; i < bars.length; i++) {
    const [, , h, l] = bars[i];
    if (buy && l <= entry) return i;
    if (!buy && h >= entry) return i;
  }
  return -1;
}

function focusRecent(chart: IChartApi, n: number) {
  if (n < 2) return;
  const from = Math.max(0, n - VIEW_BARS);
  const to = n - 1 + 6;
  chart.timeScale().setVisibleLogicalRange({ from, to });
}

/** Live decision chart: native left-axis labels (same as old right labels), pan/zoom. */
export default function SignalLevelsChart({
  bars,
  levels,
  calledAt,
  live,
  height = 420,
  timeframe,
  setup,
  bias,
  entry,
  symbol,
}: Readonly<{
  bars: Bar[];
  levels: DecisionLevel[];
  calledAt?: number | null;
  live?: boolean;
  height?: number;
  timeframe?: string | null;
  setup?: string | null;
  bias?: string | null;
  entry?: number | null;
  symbol?: string | null;
}>) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const tipRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const userPanned = useRef(false);
  const theme = useTheme();
  const [showFib, setShowFib] = useState(true);
  const [showSr, setShowSr] = useState(true);

  const visible = useMemo(
    () =>
      levels.filter((l) => {
        if (!Number.isFinite(l.price) || l.price <= 0) return false;
        if (l.kind === "fib" && !showFib) return false;
        if ((l.kind === "support" || l.kind === "resistance") && !showSr) return false;
        return true;
      }),
    [levels, showFib, showSr],
  );

  const colorOf = (kind: string) => lineColorForKind(kind, theme.palette.levels, theme.palette.text.secondary);

  const setupIdx = useMemo(() => (calledAt ? indexAtOrAfter(bars, calledAt) : -1), [bars, calledAt]);
  const entryPrice = useMemo(() => {
    if (entry != null && Number.isFinite(entry)) return entry;
    return levels.find((l) => l.kind === "entry")?.price ?? null;
  }, [entry, levels]);
  const fillIdx = useMemo(
    () => (entryPrice != null && setupIdx >= 0 ? entryFillIndex(bars, setupIdx, entryPrice, bias) : -1),
    [bars, setupIdx, entryPrice, bias],
  );

  const setupBar = setupIdx >= 0 ? bars[setupIdx] : null;
  const fillBar = fillIdx >= 0 ? bars[fillIdx] : null;
  const candlesAfterSetup = setupIdx >= 0 ? Math.max(0, bars.length - 1 - setupIdx) : 0;
  const candlesAfterEntry = fillIdx >= 0 ? Math.max(0, bars.length - 1 - fillIdx) : 0;

  // Create chart once per theme — never on live candle polls (that killed pan/zoom).
  useEffect(() => {
    const el = hostRef.current;
    if (!el) return;
    userPanned.current = false;
    const chart = createChart(el, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: theme.palette.background.paper },
        textColor: theme.palette.text.secondary,
      },
      grid: {
        vertLines: { color: theme.palette.divider },
        horzLines: { color: theme.palette.divider },
      },
      // Labels on the left (same native titles as the old right-axis style).
      leftPriceScale: {
        visible: true,
        borderVisible: false,
        scaleMargins: { top: 0.08, bottom: 0.12 },
      },
      rightPriceScale: { visible: false },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 8,
        barSpacing: 10,
        minBarSpacing: 2,
      },
      crosshair: { mode: CrosshairMode.Normal },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
      handleScale: {
        axisPressedMouseMove: { time: true, price: true },
        axisDoubleClickReset: true,
        mouseWheel: true,
        pinch: true,
      },
    });
    const series = chart.addCandlestickSeries({
      upColor: theme.palette.success.main,
      downColor: theme.palette.error.main,
      borderUpColor: theme.palette.success.main,
      borderDownColor: theme.palette.error.main,
      wickUpColor: theme.palette.success.main,
      wickDownColor: theme.palette.error.main,
      priceScaleId: "left",
      priceFormat: { type: "custom", minMove: 0.000001, formatter: fmtAxis },
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const markPanned = () => {
      userPanned.current = true;
    };
    el.addEventListener("wheel", markPanned, { passive: true });
    el.addEventListener("pointerdown", markPanned);

    const onMove = (param: {
      point?: { x: number; y: number } | undefined;
      time?: unknown;
      seriesData: Map<unknown, unknown>;
    }) => {
      const tip = tipRef.current;
      if (!tip) return;
      const data = param.seriesData.get(series) as
        | { open?: number; high?: number; low?: number; close?: number }
        | undefined;
      if (!param.point || !param.time || !data || data.close == null) {
        tip.style.display = "none";
        return;
      }
      const tSec = typeof param.time === "number" ? param.time : 0;
      tip.style.display = "block";
      tip.style.left = `${String(Math.min(param.point.x + 12, el.clientWidth - 220))}px`;
      tip.style.top = `${String(Math.max(8, param.point.y - 48))}px`;
      tip.textContent = `${fmtWhen(tSec * 1000)}  O ${fmtAxis(data.open ?? data.close)}  H ${fmtAxis(data.high ?? data.close)}  L ${fmtAxis(data.low ?? data.close)}  C ${fmtAxis(data.close)}`;
    };
    chart.subscribeCrosshairMove(onMove);

    return () => {
      el.removeEventListener("wheel", markPanned);
      el.removeEventListener("pointerdown", markPanned);
      chart.unsubscribeCrosshairMove(onMove);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [theme]);

  // Candles only — keep price lines / markers intact across live polls.
  useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    if (!series || !chart) return;
    if (!bars.length) {
      series.setData([]);
      return;
    }
    series.setData(
      bars.map((b) => ({
        time: Math.floor(b[0] / 1000) as UTCTimestamp,
        open: b[1],
        high: b[2],
        low: b[3],
        close: b[4],
      })),
    );
    if (!userPanned.current) focusRecent(chart, bars.length);
  }, [bars]);

  // Native left-axis labels (title + price), same as old right-axis style.
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;
    const handles: IPriceLine[] = [];
    for (const lvl of visible) {
      handles.push(
        series.createPriceLine({
          price: lvl.price,
          color: colorOf(lvl.kind),
          lineWidth: lvl.kind === "entry" || lvl.kind === "stop" || lvl.kind === "target" ? 2 : 1,
          lineStyle: lvl.kind === "fib" || lvl.kind === "trend" ? 2 : 0,
          axisLabelVisible: true,
          title: lvl.label,
        }),
      );
    }

    const markers: SeriesMarker<UTCTimestamp>[] = [];
    if (setupIdx >= 0 && bars[setupIdx]) {
      markers.push({
        time: Math.floor(bars[setupIdx][0] / 1000) as UTCTimestamp,
        position: "aboveBar",
        color: theme.palette.primary.main,
        shape: "arrowDown",
        text: "Setup",
      });
    }
    if (fillIdx >= 0 && bars[fillIdx]) {
      markers.push({
        time: Math.floor(bars[fillIdx][0] / 1000) as UTCTimestamp,
        position: fillIdx === setupIdx ? "belowBar" : "aboveBar",
        color: theme.palette.levels.entry,
        shape: "circle",
        text: fillIdx === setupIdx ? "Entry@setup" : "Entry",
      });
    }
    if (fillIdx >= 0) {
      for (let i = fillIdx + 1; i < bars.length; i++) {
        const n = i - fillIdx;
        if (n === 1 || n % 5 === 0 || i === bars.length - 1) {
          markers.push({
            time: Math.floor(bars[i][0] / 1000) as UTCTimestamp,
            position: "belowBar",
            color: theme.palette.text.secondary,
            shape: "circle",
            text: i === bars.length - 1 ? `Now +${String(n)}` : `+${String(n)}`,
          });
        }
      }
    } else if (setupIdx >= 0) {
      for (let i = setupIdx + 1; i < bars.length; i++) {
        const n = i - setupIdx;
        if (n === 1 || n % 5 === 0 || i === bars.length - 1) {
          markers.push({
            time: Math.floor(bars[i][0] / 1000) as UTCTimestamp,
            position: "belowBar",
            color: theme.palette.text.secondary,
            shape: "circle",
            text: i === bars.length - 1 ? `Now +${String(n)}` : `+${String(n)}`,
          });
        }
      }
    }
    markers.sort((a, b) => (a.time as number) - (b.time as number));
    series.setMarkers(markers);

    return () => {
      for (const h of handles) {
        try {
          series.removePriceLine(h);
        } catch {
          /* disposed */
        }
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, bars, setupIdx, fillIdx, theme.palette.primary.main, theme.palette.levels, theme.palette.text.secondary]);

  if (!bars.length) {
    return <EmptyState text="No candle tape for this timeframe yet." />;
  }

  return (
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", alignItems: "center" }}>
        {symbol ? <Chip size="small" label={symbol} sx={{ fontFamily: (t) => t.typography.fontFamilyMono }} /> : null}
        {timeframe ? <Chip size="small" variant="outlined" label={timeframe} /> : null}
        {setup ? <Chip size="small" variant="outlined" label={setup.replace(/_/g, " ")} /> : null}
        {bias ? <Chip size="small" color={bias === "Buy" ? "success" : bias === "Sell" ? "error" : "default"} label={bias} /> : null}
        {setupBar ? (
          <Typography variant="caption" color="text.secondary">
            Setup · {fmtWhen(setupBar[0])}
            {candlesAfterSetup ? ` · ${String(candlesAfterSetup)} new since setup` : ""}
          </Typography>
        ) : null}
        {fillBar ? (
          <Typography variant="caption" sx={{ color: "levels.entry" }}>
            Entry · {fmtWhen(fillBar[0])}
            {candlesAfterEntry ? ` · ${String(candlesAfterEntry)} new after entry` : " · just filled"}
          </Typography>
        ) : setupBar && entryPrice != null ? (
          <Typography variant="caption" color="warning.main">
            Entry {fmtAxis(entryPrice)} not filled yet
          </Typography>
        ) : null}
        {live ? (
          <Typography variant="caption" color="text.secondary">
            Live · drag to pan · wheel to zoom
          </Typography>
        ) : null}
      </Stack>
      <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap", alignItems: "center" }}>
        <FormControlLabel
          control={<Checkbox size="small" checked={showSr} onChange={(e) => setShowSr(e.target.checked)} />}
          label="Support / resistance"
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={showFib} onChange={(e) => setShowFib(e.target.checked)} />}
          label="Fibonacci"
        />
        <Typography
          variant="caption"
          color="primary"
          sx={{ cursor: "pointer", textDecoration: "underline" }}
          onClick={() => {
            userPanned.current = false;
            const chart = chartRef.current;
            if (chart) focusRecent(chart, bars.length);
          }}
        >
          Reset view
        </Typography>
      </Stack>
      <Box sx={{ position: "relative", height: { xs: 320, md: height }, width: "100%", borderRadius: 1, overflow: "hidden" }}>
        <Box ref={hostRef} sx={{ position: "absolute", inset: 0 }} />
        <Box
          ref={tipRef}
          sx={{
            display: "none",
            position: "absolute",
            zIndex: 2,
            pointerEvents: "none",
            px: 1,
            py: 0.5,
            borderRadius: 1,
            bgcolor: "background.paper",
            border: 1,
            borderColor: "divider",
            fontFamily: (t) => t.typography.fontFamilyMono,
            fontSize: "0.6875rem",
            color: "text.primary",
            whiteSpace: "nowrap",
            boxShadow: 1,
          }}
        />
      </Box>
      <Typography variant="caption" color="text.secondary">
        Left axis shows level name + price (same as the old right labels). Drag / wheel to move the chart; Reset view
        focuses recent candles.
      </Typography>
    </Stack>
  );
}
