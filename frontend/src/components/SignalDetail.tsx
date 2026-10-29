import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import MenuItem from "@mui/material/MenuItem";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import Close from "@mui/icons-material/Close";
import { useEffect, useState, type ReactNode } from "react";
import { api, type ChartData, type DecisionLevel, type MarginMode, type PaperResult, type Signal, type StoredAnalysis } from "../api";
import { fmtFixed, fmtPx, fmtSigned, fmtWhen } from "../lib/format";
import { chartMarks, parseAnalysis, parseNotes } from "../lib/analysis";
import AnalysisView from "./AnalysisView";
import { AnalysisText } from "./ChatPanel";
import SignalLevelsChart from "./SignalLevelsChart";
import { PaperWalletPicker } from "./WalletDialogs";
import { useFeedback } from "./feedback";
import { ActionButton, BiasPill, Na, Num, SectionCard, StatusPill, V } from "./ui";

const LEVERAGES = [1, 2, 3, 5, 10, 15, 20, 25, 50, 75, 100, 125];

export function usd(n: number | null | undefined): string | null {
  return n === null || n === undefined || !Number.isFinite(n) ? null : `${fmtFixed(n, 2) ?? ""} USDT`;
}

/** Profit or loss in USDT: green with ▲, red with ▼ (ruleset 9). */
export function PnlText({ r, suffix }: Readonly<{ r: PaperResult | null | undefined; suffix?: ReactNode }>) {
  if (!r) return <Na reason="No price" />;
  const up = r.pnl > 0;
  const flat = r.pnl === 0;
  return (
    <Num sx={{ color: flat ? "text.secondary" : up ? "success.main" : "error.main", fontWeight: 600 }}>
      {flat ? "" : up ? "▲ " : "▼ "}
      {fmtSigned(r.pnl, 2)} USDT{suffix}
    </Num>
  );
}

/** Where price is between the stop (left) and the target (right), with the entry marked (WL-108). */
/** WL-147: the share of the way from the entry to the target (green) or to the stop (red). */
export function ProgressTrack({ progress, towards }: Readonly<{ progress: number | null; towards: "target" | "stop" }>) {
  if (progress === null) return null;
  const up = towards === "target";
  return (
    <Box sx={{ position: "relative", height: 6, borderRadius: 3, bgcolor: "action.selected", minWidth: 96 }} aria-label={`${String(Math.round(progress * 100))}% of the way from the entry to the ${towards}`}>
      <Box sx={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${String(progress * 100)}%`, borderRadius: 3, bgcolor: up ? "success.main" : "error.main" }} />
    </Box>
  );
}

function Fact({ label, children }: Readonly<{ label: string; children: ReactNode }>) {
  return (
    <Box>
      <Typography variant="caption" sx={{ color: "text.secondary" }}>
        {label}
      </Typography>
      <Typography component="div">{children}</Typography>
    </Box>
  );
}

/** One signal or stored analysis: its chart, the paper trade (editable), the analysis and the chat (WL-107 to WL-109). */
export default function SignalDetail({
  signal,
  analysisId,
  onClose,
  onChanged,
}: Readonly<{ signal: Signal | null; analysisId: number | null; onClose: () => void; onChanged?: (s: Signal) => void }>) {
  const phone = useMediaQuery((t) => t.breakpoints.down("sm"));
  const { toast } = useFeedback();
  const [sig, setSig] = useState<Signal | null>(signal);
  const aid = sig?.analysis_id ?? analysisId;
  const [analysis, setAnalysis] = useState<StoredAnalysis | null | "none">(aid ? null : "none");
  const [chart, setChart] = useState<ChartData | null>(null);
  const [chartError, setChartError] = useState<string | null>(null);
  const [margin, setMargin] = useState(String(signal?.paper?.margin ?? ""));
  const [leverage, setLeverage] = useState(signal?.paper?.leverage ?? 10);
  const [mode, setMode] = useState<MarginMode>(signal?.paper?.margin_mode ?? "isolated");
  const [wallet, setWallet] = useState(signal?.wallet_id ?? 0); // WL-150: the paper wallet it counts in, 0 for none
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!aid) return;
    api
      .analysis(aid)
      .then(setAnalysis)
      .catch(() => setAnalysis("none"));
  }, [aid]);

  // Live chart: refresh bars every 5s while the dialog is open (analysis log + open signals).
  useEffect(() => {
    let cancelled = false;
    const load = () => {
      const req = signal ? api.signalChart(signal.id) : analysisId ? api.analysisChart(analysisId) : null;
      req
        ?.then((c) => {
          if (!cancelled) {
            setChart(c);
            setChartError(null);
          }
        })
        .catch((err: Error) => {
          if (!cancelled) setChartError(err.message);
        });
    };
    load();
    const id = window.setInterval(load, 5_000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [signal, analysisId]);

  const a = analysis !== null && analysis !== "none" ? analysis : null;
  const lv =
    sig ??
    (a
      ? { entry: a.levels?.entry, stop_loss: a.levels?.stop_loss, take_profit: a.levels?.take_profit }
      : null);
  const levels: DecisionLevel[] = [];
  const seen = new Set<string>();
  const pushLevel = (kind: string, label: string, price: number | null | undefined) => {
    if (price == null || !Number.isFinite(price) || price <= 0) return;
    const key = `${kind}:${price.toFixed(8)}`;
    if (seen.has(key)) return;
    seen.add(key);
    levels.push({ kind, label, price });
  };
  pushLevel("target", "Take profit", lv?.take_profit);
  pushLevel("entry", "Entry", lv?.entry);
  pushLevel("stop", "Stop", lv?.stop_loss);
  pushLevel("stop", "Liq", sig?.paper?.liquidation);
  for (const d of chart?.decision_levels ?? []) {
    pushLevel(d.kind || "level", d.label, d.price);
  }
  // WL-106: TP ladder / final TP from the stored analysis text.
  const marks = a ? chartMarks(parseAnalysis(a.analysis)) : null;
  for (const tp of marks?.tps ?? []) {
    pushLevel("target", tp.label, tp.price);
  }
  if (marks?.finalTp) pushLevel("target", "Final TP", marks.finalTp);
  const p = sig?.paper;
  const symbol = sig?.symbol ?? a?.symbol ?? "";
  const timeframe = sig?.timeframe ?? a?.timeframe ?? "";
  const bias = sig?.bias ?? a?.bias;
  const dirty = p && (Number(margin) !== p.margin || leverage !== p.leverage || mode !== p.margin_mode || wallet !== (sig?.wallet_id ?? 0));
  // WL-115: the current price, from the live quote of a running trade, else the newest chart candle.
  const lastBar = chart?.bars.length ? chart.bars[chart.bars.length - 1] : null;
  const nowPrice = p?.live?.price ?? (lastBar ? lastBar[4] : null);
  const atCall = sig?.price_at_signal ?? a?.price ?? lv?.entry ?? null;
  const sinceCall = nowPrice !== null && atCall ? ((nowPrice - atCall) / atCall) * 100 : null;

  async function save() {
    if (!sig) return;
    setSaving(true);
    try {
      const res = await api.updateSignal(sig.id, { margin: Number(margin), leverage, margin_mode: mode, wallet_id: wallet });
      setSig(res.signal);
      onChanged?.(res.signal);
      toast("Paper trade updated.");
    } catch (err) {
      toast(`Not saved: ${(err as Error).message}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open onClose={onClose} fullScreen={phone} fullWidth maxWidth="lg" aria-labelledby="sigTitle">
      <DialogTitle id="sigTitle" sx={{ display: "flex", alignItems: "center", gap: 1.5, pr: 1 }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
            <Num sx={{ fontWeight: 700 }}>{symbol}</Num>
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              {timeframe}
            </Typography>
            {bias ? <BiasPill bias={bias} /> : null}
            {sig ? <StatusPill status={sig.status} title={sig.outcome ?? undefined} /> : null}
            <Typography variant="body2" component="span" sx={{ color: "text.secondary" }} title={lastBar && !p?.live ? `Close of the newest ${chart?.source ?? ""} candle` : "Live price"}>
              Now <V value={fmtPx(nowPrice)} reason={chartError ? "Chart unavailable" : "Loading the price"} />
              {sinceCall !== null ? ` (${fmtSigned(sinceCall, 1) ?? ""}% since the call)` : ""}
            </Typography>
          </Stack>
          <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
            {fmtWhen(sig?.created_at ?? a?.created_at)}
            {a ? ` · ${a.provider}${a.agent ? ` · thinking like ${a.agent}` : ""}` : ""}
          </Typography>
        </Box>
        <IconButton aria-label="Close" onClick={onClose}>
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          <SectionCard title="Live chart" noPadding>
            <Box sx={{ p: 1.5 }}>
              {chartError ? <Alert severity="warning">Chart unavailable: {chartError}</Alert> : null}
              {chart ? (
                <SignalLevelsChart
                  bars={chart.bars}
                  levels={levels}
                  calledAt={chart.called_at}
                  live={chart.live ?? true}
                  symbol={symbol}
                  timeframe={timeframe}
                  setup={sig?.setup ?? a?.setup ?? null}
                  bias={bias}
                  entry={lv?.entry ?? null}
                />
              ) : chartError ? null : (
                <Skeleton variant="rounded" height={320} />
              )}
              {marks?.pattern ? (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  <strong>Pattern:</strong> {marks.pattern}
                </Typography>
              ) : null}
            </Box>
          </SectionCard>

          {sig && p ? (
            <SectionCard title="Paper trade">
              <Stack spacing={2}>
                <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ alignItems: { md: "center" } }}>
                  <TextField
                    label="Margin"
                    size="small"
                    value={margin}
                    onChange={(e) => setMargin(e.target.value.replace(/[^\d.]/g, ""))}
                    slotProps={{ input: { endAdornment: <InputAdornment position="end">USDT</InputAdornment> } }}
                    sx={{ width: 160 }}
                  />
                  <TextField select label="Leverage" size="small" value={leverage} onChange={(e) => setLeverage(Number(e.target.value))} sx={{ width: 120 }}>
                    {LEVERAGES.map((l) => (
                      <MenuItem key={l} value={l}>
                        {l}x
                      </MenuItem>
                    ))}
                  </TextField>
                  <ToggleButtonGroup exclusive size="small" value={mode} onChange={(_e, v: MarginMode | null) => v && setMode(v)} aria-label="Margin mode">
                    <ToggleButton value="isolated">Isolated</ToggleButton>
                    <ToggleButton value="cross">Cross</ToggleButton>
                  </ToggleButtonGroup>
                  <PaperWalletPicker value={wallet} onChange={setWallet} label="Counts in" />
                  <Box sx={{ flex: 1 }} />
                  <ActionButton primary busy={saving} busyLabel="Saving…" disabled={!dirty || !(Number(margin) > 0)} onClick={() => void save()}>
                    Save
                  </ActionButton>
                </Stack>
                <Stack direction="row" spacing={4} useFlexGap sx={{ flexWrap: "wrap" }}>
                  <Fact label="Margin">
                    <Num>{usd(p.margin)}</Num> · {p.leverage}x
                  </Fact>
                  <Fact label="Position">
                    <Num>{usd(p.notional)}</Num>
                  </Fact>
                  <Fact label="Liquidation">
                    {p.liquidation ? <Num>{fmtPx(p.liquidation)}</Num> : <Na reason="The cross balance covers any price" />}
                  </Fact>
                  <Fact label="At the target">
                    <PnlText r={p.at_target} suffix={` (${fmtSigned(p.at_target.roe, 1) ?? ""}%)`} />
                  </Fact>
                  <Fact label="At the stop">
                    <PnlText r={p.at_stop} suffix={` (${fmtSigned(p.at_stop.roe, 1) ?? ""}%)`} />
                  </Fact>
                  {p.live ? (
                    <Fact label={`Now at ${fmtPx(p.live.price) ?? ""}`}>
                      <PnlText r={p.live} suffix={` · ${fmtSigned(p.live.r, 2) ?? ""}R`} />
                    </Fact>
                  ) : null}
                  {p.closed ? (
                    <Fact label="Closed at">
                      <PnlText r={p.closed} />
                    </Fact>
                  ) : null}
                </Stack>
                {p.live ? <ProgressTrack progress={p.live.progress} towards={p.live.towards} /> : null}
                {p.liquidated_before_stop ? (
                  <Alert severity="error">
                    At {p.leverage}x {p.margin_mode} this trade is liquidated at {fmtPx(p.liquidation)} before the stop at {fmtPx(sig.stop_loss)}. Lower the leverage or use cross.
                  </Alert>
                ) : null}
                {p.margin_mode === "cross" ? (
                  <Typography variant="caption" sx={{ color: "text.secondary" }}>
                    Cross on {usd(p.cross_balance)}: the other open cross signals&apos; maintenance and results are counted, as on Binance.
                  </Typography>
                ) : null}
              </Stack>
            </SectionCard>
          ) : null}

          <SectionCard title="Analysis">
            {analysis === null ? <Skeleton variant="rounded" height={160} /> : null}
            {analysis === "none" && sig?.notes ? <AnalysisView p={parseNotes(sig.notes)} /> : null}
            {analysis === "none" && !sig?.notes ? (
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                This signal is from before analyses were kept (WL-107), so only its levels are stored.
              </Typography>
            ) : null}
            {a ? <AnalysisText text={a.analysis} /> : null}
          </SectionCard>

          {a ? (
            <SectionCard title={`Chat (${String(a.chat?.length ?? 0)})`}>
              {a.chat?.length ? (
                <Stack spacing={1.5}>
                  {a.chat.map((m) => (
                    <Box
                      key={m.id}
                      sx={{
                        alignSelf: m.role === "user" ? "flex-end" : "stretch",
                        maxWidth: m.role === "user" ? "80%" : "100%",
                        bgcolor: m.role === "user" ? "surface.action" : "transparent",
                        borderRadius: 2,
                        px: m.role === "user" ? 1.5 : 0,
                        py: m.role === "user" ? 1 : 0,
                      }}
                    >
                      <Typography variant="caption" sx={{ color: "text.secondary" }}>
                        {m.role === "user" ? "You" : "Analyst"} · {fmtWhen(m.created_at)}
                      </Typography>
                      {m.role === "user" ? <Typography variant="body2">{m.content}</Typography> : <AnalysisText text={m.content} />}
                    </Box>
                  ))}
                </Stack>
              ) : (
                <Typography variant="body2" sx={{ color: "text.secondary" }}>
                  No questions were asked after this analysis.
                </Typography>
              )}
            </SectionCard>
          ) : null}
        </Stack>
      </DialogContent>
    </Dialog>
  );
}
