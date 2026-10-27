import Box from "@mui/material/Box";
import Checkbox from "@mui/material/Checkbox";
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
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useMemo, useRef, useState } from "react";
import type { DecisionLevel, SignalTapeCandle } from "../api";
import { EmptyState } from "./ui";

const AXIS_DECIMALS = 3;
const HOVER_DECIMALS = 5;

function fmtAxis(price: number): string {
  return Number(price).toFixed(AXIS_DECIMALS);
}

function fmtHover(price: number): string {
  return Number(price).toFixed(HOVER_DECIMALS);
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
  if (kind === "fib") return levels.ema20;
  return textSecondary;
}

export default function SignalLevelsChart({
  candles,
  levels,
  createdAt,
  live,
}: Readonly<{
  candles: SignalTapeCandle[];
  levels: DecisionLevel[];
  createdAt?: string | null;
  live?: boolean;
  dark?: boolean;
}>) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const tipRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const fittedRef = useRef(false);
  const theme = useTheme();
  const [showFib, setShowFib] = useState(true);
  const [showSr, setShowSr] = useState(true);

  const visible = useMemo(
    () =>
      levels.filter((l) => {
        if (l.kind === "fib" && !showFib) return false;
        if ((l.kind === "support" || l.kind === "resistance") && !showSr) return false;
        return true;
      }),
    [levels, showFib, showSr],
  );

  const colorOf = (kind: string) =>
    lineColorForKind(kind, theme.palette.levels, theme.palette.text.secondary);

  useEffect(() => {
    const el = hostRef.current;
    if (!el) return;
    fittedRef.current = false;
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
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false },
      crosshair: { mode: CrosshairMode.Normal },
    });
    const series = chart.addCandlestickSeries({
      upColor: theme.palette.success.main,
      downColor: theme.palette.error.main,
      borderUpColor: theme.palette.success.main,
      borderDownColor: theme.palette.error.main,
      wickUpColor: theme.palette.success.main,
      wickDownColor: theme.palette.error.main,
      priceFormat: {
        type: "custom",
        minMove: 0.001,
        formatter: fmtAxis,
      },
    });
    chartRef.current = chart;
    seriesRef.current = series;

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
      tip.style.display = "block";
      tip.style.left = `${String(Math.min(param.point.x + 12, el.clientWidth - 160))}px`;
      tip.style.top = `${String(Math.max(8, param.point.y - 48))}px`;
      tip.textContent = `O ${fmtHover(data.open ?? data.close)}  H ${fmtHover(data.high ?? data.close)}  L ${fmtHover(data.low ?? data.close)}  C ${fmtHover(data.close)}`;
    };
    chart.subscribeCrosshairMove(onMove);

    const onResize = () => {
      chart.applyOptions({ width: el.clientWidth, height: el.clientHeight });
    };
    onResize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.unsubscribeCrosshairMove(onMove);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [theme]);

  // Candles only: keep price lines intact across live polls (WL-078).
  useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    if (!series || !chart) return;
    if (!candles.length) {
      series.setData([]);
      return;
    }
    series.setData(
      candles.map((c) => ({
        time: Math.floor(c.t / 1000) as UTCTimestamp,
        open: c.o,
        high: c.h,
        low: c.l,
        close: c.c,
      })),
    );
    if (!fittedRef.current) {
      chart.timeScale().fitContent();
      fittedRef.current = true;
    }
  }, [candles]);

  // Decision lines + signal marker; do not depend on candle refreshes.
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;
    const handles: IPriceLine[] = [];
    for (const lvl of visible) {
      if (!Number.isFinite(lvl.price)) continue;
      handles.push(
        series.createPriceLine({
          price: lvl.price,
          color: colorOf(lvl.kind),
          lineWidth: lvl.kind === "entry" || lvl.kind === "stop" || lvl.kind === "target" ? 2 : 1,
          lineStyle: lvl.kind === "fib" ? 2 : 0,
          axisLabelVisible: true,
          title: lvl.label,
        }),
      );
    }
    if (createdAt) {
      const ms = Date.parse(createdAt);
      if (!Number.isNaN(ms)) {
        const t = Math.floor(ms / 1000) as UTCTimestamp;
        series.setMarkers([
          {
            time: t,
            position: "aboveBar",
            color: theme.palette.primary.main,
            shape: "arrowDown",
            text: "Signal",
          },
        ]);
      }
    } else {
      series.setMarkers([]);
    }
    return () => {
      for (const h of handles) {
        try {
          series.removePriceLine(h);
        } catch {
          /* series may already be disposed */
        }
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- palette tokens listed below
  }, [visible, createdAt, theme.palette.primary.main, theme.palette.levels, theme.palette.text.secondary]);

  if (!candles.length) {
    return <EmptyState text="No candle tape for this signal timeframe yet." />;
  }

  return (
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap", alignItems: "center" }}>
        <FormControlLabel
          control={<Checkbox size="small" checked={showSr} onChange={(e) => setShowSr(e.target.checked)} />}
          label="Support / resistance"
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={showFib} onChange={(e) => setShowFib(e.target.checked)} />}
          label="Fibonacci"
        />
        {live ? (
          <Typography variant="caption" color="text.secondary">
            Live · drawings frozen from archive
          </Typography>
        ) : null}
      </Stack>
      <Box sx={{ position: "relative", height: { xs: 320, md: 420 }, width: "100%", borderRadius: 1, overflow: "hidden" }}>
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
      <Stack direction="row" spacing={1.5} useFlexGap sx={{ flexWrap: "wrap" }}>
        {visible.map((l) => (
          <Typography
            key={`${l.kind}-${l.label}-${String(l.price)}`}
            variant="caption"
            sx={{ color: colorOf(l.kind), fontWeight: 600, fontFamily: (t) => t.typography.fontFamilyMono }}
          >
            {l.label} {fmtHover(l.price)}
          </Typography>
        ))}
      </Stack>
    </Stack>
  );
}
