import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { alpha, useColorScheme } from "@mui/material/styles";
import ArrowBack from "@mui/icons-material/ArrowBack";
import DeleteOutlined from "@mui/icons-material/DeleteOutlined";
import ExpandMore from "@mui/icons-material/ExpandMore";
import Refresh from "@mui/icons-material/Refresh";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  api,
  type LevelAdviceItem,
  type Market,
  type Signal,
  type SignalReview,
  type SignalTape,
  type StrategyPackResult,
  type TradeLevels,
} from "../api";
import { FlowCard, LevelsBoard, LiquidityCard } from "../components/DeskCards";
import { useFeedback } from "../components/feedback";
import SignalLevelsChart from "../components/SignalLevelsChart";
import { ActionButton, EmptyState, Num, PageHeader, SectionCard, V } from "../components/ui";
import { GLYPH, biasClass, fmtPx, fmtSigned, humanize, isNum } from "../lib/format";

const OPT_LABEL: Record<string, string> = {
  local_score: "Local score",
  ai_ensemble: "Full AI ensemble",
  majority_vote: "Majority vote",
};

function stanceLabel(s: string | null | undefined): string {
  if (s === "hold") return "Hold";
  if (s === "caution") return "Caution";
  if (s === "exit_early") return "Exit early";
  if (s === "wait_entry") return "Wait entry";
  return "—";
}

function actionTone(action: string | undefined): "default" | "primary" | "warning" | "success" {
  const a = (action || "keep").toLowerCase();
  if (a === "locked" || a === "keep") return "default";
  if (a === "wait") return "warning";
  if (a === "widen" || a === "move") return "primary";
  if (a === "tighten") return "warning";
  return "default";
}

/** Derive fill status when older reviews omitted entry_status (WL-065). */
function resolveEntryStatus(sig: Signal, r: SignalReview): string {
  if (r.entry_status && r.entry_status !== "unknown") return r.entry_status;
  const entry = sig.entry;
  const price = r.price;
  if (!isNum(entry) || !isNum(price)) return r.entry_status ?? "unknown";
  const near = Math.abs(entry) * 0.0025;
  const atSignal = sig.price_at_signal;
  if (isNum(atSignal) && Math.abs(atSignal - entry) <= near) return "filled";
  if (sig.bias === "Buy") return price <= entry ? "filled" : "waiting";
  if (sig.bias === "Sell") return price >= entry ? "filled" : "waiting";
  return "unknown";
}

function fallbackAdvice(sig: Signal, r: SignalReview, entryStatus: string) {
  const advice = r.level_advice ?? {};
  const entryLocked = entryStatus === "filled";
  const entry: LevelAdviceItem = advice.entry ?? {
    action: entryLocked ? "locked" : entryStatus === "waiting" ? "wait" : "keep",
    price: entryLocked ? sig.entry ?? null : (r.revised_entry ?? sig.entry ?? null),
    reason: entryLocked
      ? "entry filled; leave entry, manage stop and target"
      : entryStatus === "waiting"
        ? "entry not filled yet (derived)"
        : "entry filled or market-style (derived)",
  };
  if (entryLocked && entry.action !== "locked") {
    entry.action = "locked";
    entry.price = sig.entry ?? entry.price;
    entry.reason = "entry filled; leave entry, manage stop and target";
  }
  const stop: LevelAdviceItem = advice.stop ?? {
    action: r.revised_stop_loss != null ? "move" : "keep",
    price: r.revised_stop_loss ?? sig.stop_loss ?? null,
    reason: r.revised_stop_loss != null ? "revised stop on review" : "original stop",
  };
  const target: LevelAdviceItem = advice.target ?? {
    action: r.revised_take_profit != null ? "move" : "keep",
    price: r.revised_take_profit ?? sig.take_profit ?? null,
    reason: r.revised_take_profit != null ? "revised target on review" : "original target",
  };
  return { entry, stop, target };
}

function LevelCard({
  title,
  original,
  item,
  accent,
  lockedNote,
}: Readonly<{
  title: string;
  original: number | null | undefined;
  item: LevelAdviceItem;
  accent: "entry" | "stop" | "target";
  lockedNote?: string;
}>) {
  const changed = (item.action || "keep").toLowerCase() !== "keep" && (item.action || "").toLowerCase() !== "locked";
  const borderKey =
    accent === "entry" ? "levels.entry" : accent === "stop" ? "levels.stop" : "levels.target";
  return (
    <Box
      sx={{
        border: 1,
        borderColor: changed ? borderKey : "divider",
        borderRadius: 1,
        p: 1.25,
        bgcolor: "background.paper",
        minWidth: 0,
      }}
    >
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
      <Typography
        variant="body2"
        sx={{
          fontFamily: (t) => t.typography.fontFamilyMono,
          fontWeight: changed ? 700 : 400,
          color: changed ? borderKey : "text.primary",
        }}
      >
        <V value={fmtPx(item.price)} />
      </Typography>
      {item.reason ? (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.75, display: "block" }}>
          {item.reason}
        </Typography>
      ) : null}
      {lockedNote ? (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
          {lockedNote}
        </Typography>
      ) : null}
    </Box>
  );
}

function AiBlock({ r }: Readonly<{ r: SignalReview }>) {
  const hasAi = Boolean(r.ai_stance || r.ai_reasoning);
  if (hasAi) {
    return (
      <Box
        sx={{
          mt: 1.5,
          p: 1.25,
          borderRadius: 1,
          border: 1,
          borderColor: "divider",
          bgcolor: "action.hover",
        }}
      >
        <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", alignItems: "center", mb: 0.75 }}>
          <Typography variant="caption" color="text.secondary">
            AI view{r.ai_provider ? ` · ${r.ai_provider}` : ""}
          </Typography>
          {r.ai_stance ? (
            <Chip size="small" color="primary" variant="outlined" label={`AI: ${stanceLabel(r.ai_stance)}`} />
          ) : null}
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
  const why =
    r.ai_error ||
    (r.ai_status === "skipped"
      ? "AI skipped for this review"
      : "No AI view on this review (offline or skipped)");
  return (
    <Box sx={{ mt: 1.5 }}>
      <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
        AI: {why}
        {r.ai_provider ? ` · provider ${r.ai_provider}` : ""}
      </Typography>
    </Box>
  );
}

export default function SignalDetail({
  signalId,
  onBack,
  onReviewed,
  onDeleted,
}: Readonly<{
  signalId: string;
  onBack: () => void;
  onReviewed?: () => void;
  onDeleted?: () => void;
}>) {
  const { toast, ask } = useFeedback();
  const { mode, systemMode } = useColorScheme();
  const dark = (mode === "system" ? systemMode : mode) === "dark";
  const [sig, setSig] = useState<Signal | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [tape, setTape] = useState<SignalTape | null>(null);
  const [tapeErr, setTapeErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const res = await api.getSignal(signalId);
      setSig(res.signal);
    } catch (e) {
      setSig(null);
      setErr((e as Error).message);
    }
  }, [signalId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    let cancelled = false;
    let first = true;
    setTape(null);
    setTapeErr(null);

    const loadTape = () => {
      api
        .signalTape(signalId, 120, true)
        .then((t) => {
          if (cancelled) return;
          setTape(t);
          setTapeErr(null);
        })
        .catch((e) => {
          if (cancelled) return;
          // Keep last good candles on poll errors; surface only the first failure.
          if (first) setTapeErr((e as Error).message);
        })
        .finally(() => {
          first = false;
        });
    };

    loadTape();
    const timer = window.setInterval(loadTape, 5_000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [signalId]);

  const archivedMarket: Market | null = useMemo(() => {
    const ctx = sig?.market_context_json;
    if (!ctx) return null;
    const whales = ctx.whales;
    const traps = ctx.traps as Market["traps"] | undefined;
    return {
      flow: whales
        ? {
            available: whales.available !== false,
            whale_bias: whales.whale_bias,
            whale_long_pct: whales.whale_long_pct,
            retail_bias: whales.retail_bias,
            retail_long_pct: whales.retail_long_pct,
            funding_bias: whales.funding_bias,
            funding_apr_est: whales.funding_apr_est,
            oi_change_pct: whales.oi_change_pct,
            taker_bias: whales.taker_bias,
            oi_price_signal: whales.oi_price_signal,
            basis_pct: whales.basis_pct,
            price_change_24h_pct: whales.price_change_24h_pct,
            summary: whales.summary,
          }
        : { available: false },
      liquidity: ctx.liquidity,
      orderbook: ctx.orderbook,
      traps,
      setup: ctx.setup,
      confluence: ctx.confluence,
    };
  }, [sig]);

  const archivedLevels: TradeLevels | null = useMemo(() => {
    if (!sig?.market_context_json) return null;
    const ctx = sig.market_context_json;
    const hints = (ctx.level_hints as Record<string, number | null | undefined> | undefined) ?? {};
    return {
      bias: sig.bias,
      entry: sig.entry ?? null,
      stop_loss: sig.stop_loss ?? null,
      take_profit: sig.take_profit ?? null,
      support: (ctx.nearest_support as number | null | undefined) ?? hints.support ?? null,
      resistance: (ctx.nearest_resistance as number | null | undefined) ?? hints.resistance ?? null,
      support_2: (ctx.support_2 as number | null | undefined) ?? hints.support_2 ?? null,
      resistance_2: (ctx.resistance_2 as number | null | undefined) ?? hints.resistance_2 ?? null,
      trend: ctx.structure?.trend ?? (typeof ctx.trend === "string" ? ctx.trend : null),
      trend_line: typeof ctx.trend_line === "string" ? ctx.trend_line : null,
      ema20: typeof ctx.ema20 === "number" ? ctx.ema20 : null,
      ema50: typeof ctx.ema50 === "number" ? ctx.ema50 : null,
      confidence: sig.confidence ?? null,
      reasoning: "",
    };
  }, [sig]);

  async function runReview() {
    if (!sig || busy) return;
    setBusy(true);
    try {
      const res = await api.reviewSignal(sig.id);
      setSig(res.signal);
      const rev = res.review;
      if (rev?.ai_reasoning) {
        toast(`Review saved · AI via ${rev.ai_provider ?? "provider"}`);
      } else if (rev?.ai_error) {
        toast(`Review saved · AI: ${rev.ai_error.slice(0, 120)}`);
      } else {
        toast(rev?.summary ?? "Review saved");
      }
      onReviewed?.();
    } catch (e) {
      toast(`Review failed: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!sig || deleting) return;
    const ok = await ask({
      title: `Delete ${sig.symbol}?`,
      text: "Removes this signal and its live reviews and pack results. This cannot be undone.",
      okLabel: "Delete",
      danger: true,
    });
    if (!ok) return;
    setDeleting(true);
    try {
      await api.deleteSignal(sig.id);
      toast(`${sig.symbol} deleted.`);
      onDeleted?.();
      onBack();
    } catch (e) {
      toast(`Could not delete: ${(e as Error).message}`);
    } finally {
      setDeleting(false);
    }
  }

  if (err) {
    return (
      <Stack spacing={2}>
        <PageHeader
          title="Signal"
          subtitle={err}
          actions={
            <ActionButton icon={<ArrowBack />} onClick={onBack}>
              Back to Signals
            </ActionButton>
          }
        />
        <EmptyState text={err} />
      </Stack>
    );
  }

  if (!sig) {
    return (
      <Stack spacing={2}>
        <PageHeader title="Signal" subtitle="Loading…" />
        <EmptyState text="Loading signal…" />
      </Stack>
    );
  }

  const multi = sig.multi_analysis_json;
  const packs: StrategyPackResult[] = multi?.packs ?? [];
  const reviews = sig.live_review_json ?? [];
  const cls = biasClass(sig.bias);
  const optMode = multi?.optimize_mode ? OPT_LABEL[multi.optimize_mode] ?? multi.optimize_mode : null;
  const ctx = sig.market_context_json;
  const decisionLevels =
    tape?.decision_levels?.length
      ? tape.decision_levels
      : ctx?.decision_levels?.length
        ? ctx.decision_levels
        : [
            ...(isNum(sig.entry) ? [{ kind: "entry", label: "Entry", price: sig.entry }] : []),
            ...(isNum(sig.stop_loss) ? [{ kind: "stop", label: "Stop", price: sig.stop_loss }] : []),
            ...(isNum(sig.take_profit) ? [{ kind: "target", label: "Take profit", price: sig.take_profit }] : []),
          ];

  return (
    <Stack spacing={2}>
      <PageHeader
        title={`${sig.symbol} · ${sig.bias}`}
        subtitle={`${humanize(sig.strategy_id ?? "desk")} · ${sig.timeframe ?? "—"} · ${sig.status}${
          optMode ? ` · ${optMode}` : ""
        }`}
        actions={
          <>
            <ActionButton icon={<ArrowBack />} onClick={onBack}>
              Back
            </ActionButton>
            <ActionButton
              icon={<DeleteOutlined />}
              busy={deleting}
              busyLabel="Deleting…"
              disabled={busy}
              onClick={() => void remove()}
            >
              Delete
            </ActionButton>
            {sig.status === "open" ? (
              <ActionButton icon={<Refresh />} primary busy={busy} busyLabel="Reviewing…" onClick={() => void runReview()}>
                Live review
              </ActionButton>
            ) : null}
          </>
        }
      />

      <SectionCard
        title="Decision chart"
        right={
          <Typography variant="caption" color="text.secondary">
            Live candles · archived drawings
          </Typography>
        }
      >
        {tapeErr && !tape ? (
          <EmptyState
            text={
              tapeErr === "Not Found"
                ? "Candle tape API not available on this server. Restart the backend so GET /api/signals/{id}/tape is loaded, then refresh."
                : `Tape unavailable: ${tapeErr}`
            }
          />
        ) : !tape ? (
          <EmptyState text="Loading live candle tape…" />
        ) : (
          <SignalLevelsChart
            candles={tape.candles}
            levels={decisionLevels}
            createdAt={sig.created_at}
            live
            dark={Boolean(dark)}
          />
        )}
      </SectionCard>

      <SectionCard title="Original plan (frozen)">
        <Box
          sx={{
            display: "grid",
            gap: 1.5,
            gridTemplateColumns: { xs: "1fr 1fr", sm: "repeat(4, 1fr)" },
          }}
        >
          <Box>
            <Typography variant="caption" color="text.secondary">
              Bias
            </Typography>
            <Typography className={cls}>
              {GLYPH[cls]} {sig.bias}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Entry
            </Typography>
            <Typography>
              <V value={fmtPx(sig.entry)} />
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Stop
            </Typography>
            <Typography>
              <V value={fmtPx(sig.stop_loss)} />
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Target
            </Typography>
            <Typography>
              <V value={fmtPx(sig.take_profit)} />
            </Typography>
          </Box>
        </Box>
        {sig.notes ? (
          <Typography variant="body2" sx={{ mt: 1.5, color: "text.secondary" }}>
            {sig.notes}
          </Typography>
        ) : null}
        {multi?.reason ? (
          <Typography variant="body2" sx={{ mt: 1 }}>
            Optimize: {multi.reason}
          </Typography>
        ) : null}
      </SectionCard>

      {!ctx ? (
        <SectionCard title="Market at decision">
          <EmptyState text="No archived market context for this signal (saved before WL-077). Re-run Analyze on Desk to archive whales, liquidity, structure and Fib with a new signal. The decision chart above still draws entry, stop and target from the frozen plan." />
        </SectionCard>
      ) : (
        <>
          <Box
            sx={{
              display: "grid",
              gap: 2,
              gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
            }}
          >
            <FlowCard market={archivedMarket} />
            <LiquidityCard market={archivedMarket} />
          </Box>
          <SectionCard
            title="Structure at decision"
            right={<Typography variant="caption" color="text.secondary">Archived snapshot</Typography>}
          >
            <Stack spacing={1.5}>
              {(ctx.structure?.trend || ctx.structure?.note || typeof ctx.trend === "string") && (
                <Typography variant="body2" color="text.secondary">
                  Structure: {ctx.structure?.trend ?? String(ctx.trend ?? "—")}
                  {ctx.structure?.trend_strength ? ` · ${ctx.structure.trend_strength}` : ""}
                  {ctx.structure?.note ? ` · ${ctx.structure.note}` : ""}
                </Typography>
              )}
              <LevelsBoard levels={archivedLevels} market={archivedMarket} />
              {ctx.fibonacci?.available && ctx.fibonacci.levels ? (
                <Box>
                  <Typography variant="overline" color="text.secondary">
                    Fibonacci at decision
                  </Typography>
                  <Stack direction="row" spacing={1.5} useFlexGap sx={{ flexWrap: "wrap", mt: 0.5 }}>
                    {Object.entries(ctx.fibonacci.levels).map(([ratio, px]) => (
                      <Typography key={ratio} variant="caption" sx={{ fontFamily: (t) => t.typography.fontFamilyMono }}>
                        {ratio}: {fmtPx(px)}
                      </Typography>
                    ))}
                  </Stack>
                </Box>
              ) : null}
            </Stack>
          </SectionCard>
        </>
      )}

      {packs.length > 0 ? (
        <SectionCard title={`Strategy packs (${String(packs.length)})`}>
          {packs.map((p) => {
            const pCls = biasClass(p.bias);
            const winner = multi?.final_strategy_id === p.strategy_id;
            return (
              <Accordion key={p.strategy_id} disableGutters elevation={0} sx={{ "&:before": { display: "none" } }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
                    <Typography sx={{ fontWeight: winner ? 700 : 500 }}>{p.strategy_label || p.strategy_id}</Typography>
                    {winner ? <Chip size="small" label="Winner" color="primary" /> : null}
                    <Chip size="small" label={`${GLYPH[pCls]} ${p.bias}`} variant="outlined" />
                    <Typography variant="caption" color="text.secondary">
                      score {isNum(p.pack_score) ? String(p.pack_score) : "—"} · fit{" "}
                      {fmtSigned(p.fit_score) ?? "—"} · {p.timeframe ?? "—"}
                    </Typography>
                  </Stack>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2">
                    Entry <V value={fmtPx(p.entry)} /> · SL <V value={fmtPx(p.stop_loss)} /> · TP{" "}
                    <V value={fmtPx(p.take_profit)} />
                  </Typography>
                  {p.reasoning ? (
                    <Typography variant="body2" sx={{ mt: 1, color: "text.secondary" }}>
                      {p.reasoning}
                    </Typography>
                  ) : null}
                  {p.error ? (
                    <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                      {p.error}
                    </Typography>
                  ) : null}
                </AccordionDetails>
              </Accordion>
            );
          })}
        </SectionCard>
      ) : (
        <SectionCard title="Strategy packs">
          <Typography variant="body2" color="text.secondary">
            Single-strategy signal (no multi pack snapshot).
          </Typography>
        </SectionCard>
      )}

      <SectionCard title={`Live reviews (${String(reviews.length)})`}>
        {reviews.length === 0 ? (
          <EmptyState text="No live reviews yet. Use Live review to append stance, level cards and AI reasoning." />
        ) : (
          <Stack spacing={2}>
            {[...reviews].reverse().map((r) => {
              const entryStatus = resolveEntryStatus(sig, r);
              const advice = fallbackAdvice(sig, r, entryStatus);
              const entryLocked = entryStatus === "filled";
              const openMark =
                (sig.status || "").toLowerCase() === "open" &&
                entryStatus !== "waiting" &&
                isNum(r.unrealized_r);
              let markTone: "profit" | "loss" | "flat" | null = null;
              if (openMark && isNum(r.unrealized_r)) {
                if (r.unrealized_r > 0.02) markTone = "profit";
                else if (r.unrealized_r < -0.02) markTone = "loss";
                else markTone = "flat";
              }
              const markColor =
                markTone === "profit" ? "success.main" : markTone === "loss" ? "error.main" : "text.primary";
              return (
                <Box
                  key={r.at}
                  sx={{
                    border: 1,
                    borderColor:
                      markTone === "profit"
                        ? "success.main"
                        : markTone === "loss"
                          ? "error.main"
                          : "divider",
                    bgcolor: (t) =>
                      markTone === "profit"
                        ? alpha(t.palette.success.main, 0.08)
                        : markTone === "loss"
                          ? alpha(t.palette.error.main, 0.08)
                          : "transparent",
                    borderRadius: 1,
                    p: 1.5,
                  }}
                >
                  <Stack direction="row" spacing={1} useFlexGap sx={{ mb: 1.5, flexWrap: "wrap", alignItems: "center" }}>
                    <Typography variant="body2">
                      {r.at?.slice(0, 19)?.replace("T", " ") ?? "—"}
                    </Typography>
                    <Typography variant="body2">
                      Now <Num sx={{ color: markColor, fontWeight: 600 }}>{fmtPx(r.price)}</Num>
                      {isNum(sig.entry) ? (
                        <Typography component="span" variant="caption" sx={{ color: "text.secondary", ml: 0.75 }}>
                          vs entry {fmtPx(sig.entry)}
                        </Typography>
                      ) : null}
                    </Typography>
                    <Typography variant="body2" sx={{ color: markColor, fontWeight: 700 }}>
                      {markTone === "profit" ? "▲ profit " : markTone === "loss" ? "▼ loss " : ""}
                      {isNum(r.unrealized_r) ? `${fmtSigned(r.unrealized_r, 2)}R if closed now` : "—"}
                    </Typography>
                    <Chip size="small" label={`Rules: ${stanceLabel(r.stance)}`} />
                    {r.ai_stance ? (
                      <Chip size="small" color="primary" variant="outlined" label={`AI: ${stanceLabel(r.ai_stance)}`} />
                    ) : null}
                    <Chip
                      size="small"
                      variant="outlined"
                      color={entryLocked ? "success" : entryStatus === "waiting" ? "warning" : "default"}
                      label={entryLocked ? "Entry locked" : `Entry ${entryStatus}`}
                    />
                    {(sig.status || "").toLowerCase() === "open" ? (
                      <Chip size="small" variant="outlined" label="Levels not hit" />
                    ) : null}
                  </Stack>

                  <Box
                    sx={{
                      display: "grid",
                      gap: 1.25,
                      gridTemplateColumns: { xs: "1fr", sm: "repeat(3, 1fr)" },
                    }}
                  >
                    <LevelCard
                      title="Entry"
                      original={sig.entry}
                      item={advice.entry}
                      accent="entry"
                      lockedNote={
                        entryLocked
                          ? "Filled: do not chase a new entry; adjust stop/target only."
                          : entryStatus === "waiting"
                            ? "Not filled yet: wait for the limit/reclaim or move the working order."
                            : undefined
                      }
                    />
                    <LevelCard title="Stop" original={sig.stop_loss} item={advice.stop} accent="stop" />
                    <LevelCard title="Target" original={sig.take_profit} item={advice.target} accent="target" />
                  </Box>

                  <Typography variant="caption" sx={{ mt: 1.25, display: "block", color: "text.secondary" }}>
                    {r.summary}
                  </Typography>
                  <AiBlock r={r} />
                </Box>
              );
            })}
          </Stack>
        )}
      </SectionCard>
    </Stack>
  );
}
