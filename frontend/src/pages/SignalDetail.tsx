import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import ArrowBack from "@mui/icons-material/ArrowBack";
import DeleteOutlined from "@mui/icons-material/DeleteOutlined";
import ExpandMore from "@mui/icons-material/ExpandMore";
import RateReviewOutlined from "@mui/icons-material/RateReviewOutlined";
import { useEffect, useState } from "react";
import {
  api,
  type ChartData,
  type DecisionLevel,
  type LevelAdviceItem,
  type Signal,
  type SignalReview,
  type StrategyPackResult,
} from "../api";
import SignalLevelsChart from "../components/SignalLevelsChart";
import { useFeedback } from "../components/feedback";
import { ActionButton, EmptyState, Na, PageHeader, Pill, SectionCard, V } from "../components/ui";
import { GLYPH, biasClass, fmtPx, fmtR, fmtSigned, humanize, isNum } from "../lib/format";

function stanceLabel(s: string | null | undefined): string {
  if (s === "hold") return "Hold";
  if (s === "caution") return "Caution";
  if (s === "exit_early") return "Exit early";
  if (s === "bank") return "Bank";
  if (s === "wait_entry") return "Wait entry";
  return "—";
}

function actionTone(action: string | undefined): "default" | "primary" | "warning" | "success" {
  const a = (action || "keep").toLowerCase();
  if (a === "locked" || a === "keep") return "default";
  if (a === "wait" || a === "tighten") return "warning";
  if (a === "widen" || a === "move") return "primary";
  return "default";
}

function LevelCard({
  title,
  original,
  item,
}: Readonly<{ title: string; original: number | null | undefined; item: LevelAdviceItem }>) {
  const changed = (item.action || "keep").toLowerCase() !== "keep" && (item.action || "").toLowerCase() !== "locked";
  return (
    <Box sx={{ border: 1, borderColor: changed ? "primary.main" : "divider", borderRadius: 1, p: 1.25, minWidth: 0 }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", mb: 0.75, flexWrap: "wrap" }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
          {title}
        </Typography>
        <Chip size="small" color={actionTone(item.action)} label={humanize(item.action || "keep")} />
      </Stack>
      <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
        Original
      </Typography>
      <Typography variant="body2" sx={{ fontFamily: (t) => t.typography.fontFamilyMono, mb: 0.75 }}>
        <V value={fmtPx(original)} />
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
        {changed ? "Suggested" : item.action === "locked" ? "Locked" : "Advice"}
      </Typography>
      <Typography variant="body2" sx={{ fontFamily: (t) => t.typography.fontFamilyMono, fontWeight: changed ? 700 : 400 }}>
        <V value={fmtPx(item.price)} />
      </Typography>
      {item.reason ? (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.75, display: "block" }}>
          {item.reason}
        </Typography>
      ) : null}
    </Box>
  );
}

function AiBlock({ r }: Readonly<{ r: SignalReview }>) {
  const hasAi = Boolean(r.ai_stance || r.ai_reasoning);
  if (hasAi) {
    return (
      <Box sx={{ mt: 1.5, p: 1.25, borderRadius: 1, border: 1, borderColor: "divider", bgcolor: "action.hover" }}>
        <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", alignItems: "center", mb: 0.75 }}>
          <Typography variant="caption" color="text.secondary">
            AI view{r.ai_provider ? ` · ${r.ai_provider}` : ""}
          </Typography>
          {r.ai_stance ? <Chip size="small" color="primary" variant="outlined" label={`AI: ${stanceLabel(r.ai_stance)}`} /> : null}
        </Stack>
        {r.ai_stance_reason ? (
          <Typography variant="body2" sx={{ mb: 0.75 }}>
            {r.ai_stance_reason}
          </Typography>
        ) : null}
        {r.ai_reasoning && r.ai_reasoning !== r.ai_stance_reason ? (
          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", color: "text.secondary" }}>
            {r.ai_reasoning}
          </Typography>
        ) : null}
      </Box>
    );
  }
  const why = r.ai_error || (r.ai_status === "skipped" ? "AI skipped for this review" : "No AI view on this review");
  return (
    <Box sx={{ mt: 1.5 }}>
      <Typography variant="caption" color="text.secondary">
        AI: {why}
        {r.ai_provider ? ` · provider ${r.ai_provider}` : ""}
      </Typography>
    </Box>
  );
}

function decisionChartLevels(chart: ChartData | null, sig: Signal): DecisionLevel[] {
  const out: DecisionLevel[] = [];
  const seen = new Set<string>();
  const push = (kind: string, label: string, price: number | null | undefined) => {
    if (price == null || !Number.isFinite(price) || price <= 0) return;
    const key = `${kind}:${price.toFixed(8)}`;
    if (seen.has(key)) return;
    seen.add(key);
    out.push({ kind, label, price });
  };
  push("entry", "Entry", sig.entry);
  push("stop", "Stop", sig.stop_loss);
  push("target", "Take profit", sig.take_profit);
  for (const d of chart?.decision_levels ?? []) {
    push(d.kind || "level", d.label, d.price);
  }
  return out;
}

export default function SignalDetail({
  signalId,
  onBack,
  onChanged,
}: Readonly<{ signalId: string; onBack: () => void; onChanged?: () => void }>) {
  const { toast, ask } = useFeedback();
  const [sig, setSig] = useState<Signal | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [chart, setChart] = useState<ChartData | null>(null);
  const [chartError, setChartError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api
      .signal(signalId)
      .then((r) => setSig(r.signal))
      .catch((e: Error) => setError(e.message));
  }, [signalId]);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      api
        .signalChart(signalId)
        .then((c) => {
          if (!cancelled) {
            setChart(c);
            setChartError(null);
          }
        })
        .catch((e: Error) => {
          if (!cancelled) setChartError(e.message);
        });
    };
    load();
    const id = window.setInterval(load, 5_000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [signalId]);

  async function review() {
    setBusy(true);
    try {
      const r = await api.reviewSignal(signalId);
      setSig(r.signal);
      toast(r.review?.summary ?? "Review saved");
      onChanged?.();
    } catch (e) {
      toast((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    const ok = await ask({
      title: "Delete signal",
      text: "Removes this signal and its live reviews and pack results. This cannot be undone.",
      okLabel: "Delete",
      danger: true,
    });
    if (!ok) return;
    try {
      await api.deleteSignal(signalId);
      toast("Signal deleted");
      onChanged?.();
      onBack();
    } catch (e) {
      toast((e as Error).message);
    }
  }

  if (error) return <EmptyState text={error} />;
  if (!sig) return <EmptyState text="Loading…" />;

  const multi = sig.multi_analysis_json;
  const reviews = Array.isArray(sig.live_review_json) ? sig.live_review_json : [];
  const packs: StrategyPackResult[] = multi?.packs ?? [];
  const ranked = [...packs].sort((a, b) => (b.pack_score ?? -999) - (a.pack_score ?? -999));
  const chartLevels = decisionChartLevels(chart, sig);

  return (
    <Stack spacing={2}>
      <PageHeader
        title={`${sig.symbol} · ${sig.bias}`}
        subtitle={`${sig.timeframe ?? "—"} · ${sig.strategy_id ?? "desk"} · ${sig.status}`}
        actions={
          <>
            <ActionButton icon={<ArrowBack />} onClick={onBack}>
              Back
            </ActionButton>
            {sig.status === "open" ? (
              <ActionButton icon={<RateReviewOutlined />} busy={busy} busyLabel="Reviewing…" onClick={() => void review()}>
                Live review
              </ActionButton>
            ) : null}
            <ActionButton icon={<DeleteOutlined />} onClick={() => void remove()}>
              Delete
            </ActionButton>
          </>
        }
      />

      <SectionCard title="Live chart" noPadding>
        <Box sx={{ p: 1.5 }}>
          {chartError ? <Alert severity="warning">Chart unavailable: {chartError}</Alert> : null}
          {chart ? (
            <SignalLevelsChart
              bars={chart.bars}
              levels={chartLevels}
              calledAt={chart.called_at}
              live={chart.live ?? true}
              symbol={sig.symbol}
              timeframe={sig.timeframe}
              setup={sig.setup}
              bias={sig.bias}
              entry={sig.entry}
            />
          ) : chartError ? null : (
            <Skeleton variant="rounded" height={320} />
          )}
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>
            Live Binance candles refresh every 5s. Left/right price axes; coloured lines are the frozen plan plus S/R / fib from the call.
          </Typography>
        </Box>
      </SectionCard>

      <Card sx={{ p: 2 }}>
        <Typography variant="h3" component="h3" sx={{ mb: 1 }}>
          Plan
        </Typography>
        <Stack spacing={0.5}>
          <Row label="Entry" value={fmtPx(sig.entry) ?? "—"} />
          <Row label="Stop" value={fmtPx(sig.stop_loss) ?? "—"} />
          <Row label="Target" value={fmtPx(sig.take_profit) ?? "—"} />
          <Row label="R" value={fmtR(sig.r_multiple, 2) ?? "—"} />
          <Row label="Paper" value={sig.paper ? `${String(sig.paper.margin)} USDT · ${String(sig.paper.leverage)}x` : "—"} />
          {sig.notes ? <Row label="Notes" value={sig.notes} /> : null}
        </Stack>
      </Card>

      {ranked.length ? (
        <Card sx={{ p: 2 }}>
          <Typography variant="h3" component="h3" sx={{ mb: 1 }}>
            Multi-analyze packs{multi?.optimize_mode ? ` · ${multi.optimize_mode}` : ""}
          </Typography>
          {multi?.reason ? (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {multi.reason}
            </Typography>
          ) : null}
          <Stack spacing={0.5}>
            {ranked.map((p) => {
              const cls = biasClass(p.bias);
              const winner = multi?.final_strategy_id === p.strategy_id;
              return (
                <Accordion key={p.strategy_id} disableGutters elevation={0} sx={{ "&:before": { display: "none" }, bgcolor: "transparent" }}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }} useFlexGap>
                      <Typography
                        variant="body2"
                        sx={{ fontFamily: (t) => t.typography.fontFamilyMono, fontWeight: winner ? 700 : 500, minWidth: 120 }}
                      >
                        {p.strategy_id}
                      </Typography>
                      {winner ? <Chip size="small" label="Winner" color="primary" /> : null}
                      <Pill
                        glyph={GLYPH[cls] || "·"}
                        label={String(p.bias ?? "—")}
                        tone={cls === "buy" ? "buy" : cls === "sell" ? "sell" : "neutral"}
                      />
                      <Typography variant="caption" color="text.secondary">
                        score {isNum(p.pack_score) ? String(p.pack_score) : "—"} · fit {fmtSigned(p.fit_score) ?? "—"}
                        {p.timeframe ? ` · ${p.timeframe}` : ""}
                      </Typography>
                    </Stack>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2">
                      Entry <V value={fmtPx(p.entry)} /> · SL <V value={fmtPx(p.stop_loss)} /> · TP <V value={fmtPx(p.take_profit)} />
                    </Typography>
                    {p.reasoning ? (
                      <Typography variant="body2" sx={{ mt: 1, color: "text.secondary", whiteSpace: "pre-wrap" }}>
                        {p.reasoning}
                      </Typography>
                    ) : (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                        No pack reasoning stored for this row.
                      </Typography>
                    )}
                    {p.error ? (
                      <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                        {p.error}
                      </Typography>
                    ) : null}
                  </AccordionDetails>
                </Accordion>
              );
            })}
          </Stack>
        </Card>
      ) : null}

      <Card sx={{ p: 2 }}>
        <Typography variant="h3" component="h3" sx={{ mb: 1 }}>
          Live reviews
        </Typography>
        {!reviews.length ? (
          <EmptyState text="No live reviews yet. Use Live review on an open trade for rule stance + AI re-read." />
        ) : (
          <Stack spacing={1.5}>
            {[...reviews].reverse().map((r, i) => {
              const advice = r.level_advice ?? {};
              return (
                <Stack key={`${r.at}-${String(i)}`} spacing={1} sx={{ borderBottom: 1, borderColor: "divider", pb: 1.5 }}>
                  <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", alignItems: "center" }}>
                    <Typography variant="caption" color="text.secondary">
                      {r.at}
                    </Typography>
                    <Chip size="small" label={`Rules: ${stanceLabel(r.stance)}`} />
                    {r.entry_status ? <Chip size="small" variant="outlined" label={`Entry ${r.entry_status}`} /> : null}
                    {r.unrealized_r != null ? (
                      <Typography variant="body2">
                        {fmtSigned(r.unrealized_r, 2)}R · mark {fmtPx(r.price) ?? "—"}
                      </Typography>
                    ) : null}
                  </Stack>
                  {r.summary ? (
                    <Typography variant="body2" color="text.secondary">
                      {r.summary}
                    </Typography>
                  ) : null}
                  <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: { xs: "1fr", sm: "repeat(3, minmax(0, 1fr))" } }}>
                    <LevelCard
                      title="Entry"
                      original={sig.entry}
                      item={advice.entry ?? { action: "keep", price: sig.entry, reason: "original entry" }}
                    />
                    <LevelCard
                      title="Stop"
                      original={sig.stop_loss}
                      item={advice.stop ?? { action: "keep", price: sig.stop_loss, reason: "original stop" }}
                    />
                    <LevelCard
                      title="Target"
                      original={sig.take_profit}
                      item={advice.target ?? { action: "keep", price: sig.take_profit, reason: "original target" }}
                    />
                  </Box>
                  <AiBlock r={r} />
                </Stack>
              );
            })}
          </Stack>
        )}
      </Card>
    </Stack>
  );
}

function Row({ label, value }: Readonly<{ label: string; value: React.ReactNode }>) {
  return (
    <Stack direction="row" spacing={2}>
      <Typography variant="caption" color="text.secondary" sx={{ minWidth: 72 }}>
        {label}
      </Typography>
      <Typography variant="body2">{value ?? <Na />}</Typography>
    </Stack>
  );
}
