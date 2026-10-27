import Alert from "@mui/material/Alert";
import Autocomplete from "@mui/material/Autocomplete";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { alpha } from "@mui/material/styles";
import DeleteOutlined from "@mui/icons-material/DeleteOutlined";
import DoneAll from "@mui/icons-material/DoneAll";
import Refresh from "@mui/icons-material/Refresh";
import TrackChanges from "@mui/icons-material/TrackChanges";
import Update from "@mui/icons-material/Update";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, type Signal, type SignalReview, type Stats, type StrategyInfo } from "../api";
import { useFeedback } from "../components/feedback";
import {
  ActionButton,
  BiasPill,
  DataTable,
  EmptyState,
  KpiStrip,
  Na,
  Num,
  PageHeader,
  SectionCard,
  StatusPill,
  V,
} from "../components/ui";
import { fmtPx, fmtSigned, fmtWhen, humanize, isNum } from "../lib/format";

const TF_TABS = [
  { id: "all", label: "All" },
  { id: "15m", label: "15m" },
  { id: "1h", label: "1h" },
  { id: "4h", label: "4h" },
  { id: "1d", label: "1D" },
] as const;

type TfTab = (typeof TF_TABS)[number]["id"];

const STATUS_OPTIONS = [
  { id: "all", label: "All statuses" },
  { id: "open", label: "Open" },
  { id: "win", label: "Win" },
  { id: "loss", label: "Loss" },
  { id: "expired", label: "Expired" },
] as const;

type StatusFilter = (typeof STATUS_OPTIONS)[number]["id"];

const BOOK_TABS = [
  { id: "trades", label: "Trades" },
  { id: "neutral", label: "Neutral" },
] as const;

type BookTab = (typeof BOOK_TABS)[number]["id"];

const STANCE_META: Record<string, { glyph: string; label: string }> = {
  hold: { glyph: "○", label: "Hold" },
  caution: { glyph: "△", label: "Caution" },
  exit_early: { glyph: "▸", label: "Exit early" },
};

function normTf(tf: string | null | undefined): string {
  return (tf || "").trim().toLowerCase();
}

function normStrategy(id: string | null | undefined): string {
  const s = (id || "").trim().toLowerCase();
  return s || "desk";
}

function normSymbol(sym: string | null | undefined): string {
  return (sym || "").trim().toUpperCase().replace(".P", "").replace("/", "");
}

function strategyLabel(id: string | null | undefined, catalog: StrategyInfo[]): string {
  const sid = normStrategy(id);
  return catalog.find((s) => s.id === sid)?.label ?? (sid === "desk" ? "Desk" : humanize(sid));
}

function matchesTf(signalTf: string | null | undefined, tab: TfTab): boolean {
  if (tab === "all") return true;
  return normTf(signalTf) === tab;
}

function latestReview(s: Signal): SignalReview | null {
  const list = s.live_review_json;
  if (!Array.isArray(list) || !list.length) return null;
  return list[list.length - 1] ?? null;
}

/** Open + reviewed mark vs locked entry: profit / loss / flat (WL-070). */
function markTone(unrealizedR: number | null | undefined): "profit" | "loss" | "flat" | null {
  if (!isNum(unrealizedR)) return null;
  if (unrealizedR > 0.02) return "profit";
  if (unrealizedR < -0.02) return "loss";
  return "flat";
}

function markRowSx(tone: "profit" | "loss" | "flat" | null) {
  if (!tone || tone === "flat") return undefined;
  return {
    bgcolor: (t: { palette: { success: { main: string }; error: { main: string } } }) =>
      alpha(tone === "profit" ? t.palette.success.main : t.palette.error.main, 0.12),
    "&:hover": {
      bgcolor: (t: { palette: { success: { main: string }; error: { main: string } } }) =>
        alpha(tone === "profit" ? t.palette.success.main : t.palette.error.main, 0.18),
    },
  };
}

function markColor(tone: "profit" | "loss" | "flat" | null): string {
  if (tone === "profit") return "success.main";
  if (tone === "loss") return "error.main";
  return "text.secondary";
}

function StanceChip({ stance }: Readonly<{ stance: string | null | undefined }>) {
  if (!stance) return <Na reason="No live review yet" />;
  const meta = STANCE_META[stance] ?? { glyph: "●", label: humanize(stance) };
  return <Chip size="small" label={`${meta.glyph} ${meta.label}`} variant="outlined" />;
}

function filterStats(rows: Signal[]): Stats {
  const closed = rows.filter((r) => r.status === "win" || r.status === "loss" || r.status === "expired");
  const wins = closed.filter((r) => r.status === "win");
  const losses = closed.filter((r) => r.status === "loss");
  const expired = closed.filter((r) => r.status === "expired");
  const open = rows.filter((r) => r.status === "open").length;
  const decided = [...wins, ...losses];
  const hit = decided.length ? wins.length / decided.length : null;
  const rs = closed.map((r) => r.r_multiple).filter((v): v is number => typeof v === "number" && !Number.isNaN(v));
  const avg_r = rs.length ? Math.round((rs.reduce((a, b) => a + b, 0) / rs.length) * 100) / 100 : null;
  return {
    total: rows.length,
    open,
    wins: wins.length,
    losses: losses.length,
    expired: expired.length,
    hit_rate: hit,
    avg_r,
  };
}

type OpenBook = {
  open: number;
  reviewed: number;
  waiting: number;
  noReview: number;
  inProfit: number;
  inLoss: number;
  flat: number;
  sumR: number | null;
  avgR: number | null;
  bestR: number | null;
  worstR: number | null;
  stanceHold: number;
  stanceCaution: number;
  stanceExit: number;
  stanceNone: number;
  aiHold: number;
  aiCaution: number;
  aiExit: number;
  aiWait: number;
  aiNone: number;
};

/** Mark-to-market book for open rows in the current filter (WL-072). */
function openBookStats(rows: Signal[]): OpenBook {
  const openRows = rows.filter((r) => (r.status || "").toLowerCase() === "open");
  let reviewed = 0;
  let waiting = 0;
  let noReview = 0;
  let inProfit = 0;
  let inLoss = 0;
  let flat = 0;
  let stanceHold = 0;
  let stanceCaution = 0;
  let stanceExit = 0;
  let stanceNone = 0;
  let aiHold = 0;
  let aiCaution = 0;
  let aiExit = 0;
  let aiWait = 0;
  let aiNone = 0;
  const marks: number[] = [];
  for (const s of openRows) {
    const latest = latestReview(s);
    if (!latest || latest.price == null) {
      noReview += 1;
      stanceNone += 1;
      aiNone += 1;
      continue;
    }
    const rule = (latest.stance || "").toLowerCase();
    if (rule === "hold") stanceHold += 1;
    else if (rule === "caution") stanceCaution += 1;
    else if (rule === "exit_early") stanceExit += 1;
    else stanceNone += 1;

    const ai = (latest.ai_stance || "").toLowerCase();
    if (ai === "hold") aiHold += 1;
    else if (ai === "caution") aiCaution += 1;
    else if (ai === "exit_early") aiExit += 1;
    else if (ai === "wait_entry") aiWait += 1;
    else aiNone += 1;

    if (latest.entry_status === "waiting") {
      waiting += 1;
      continue;
    }
    reviewed += 1;
    if (!isNum(latest.unrealized_r)) {
      flat += 1;
      continue;
    }
    marks.push(latest.unrealized_r);
    const tone = markTone(latest.unrealized_r);
    if (tone === "profit") inProfit += 1;
    else if (tone === "loss") inLoss += 1;
    else flat += 1;
  }
  const sumRaw = marks.length ? marks.reduce((a, b) => a + b, 0) : null;
  const sumR = sumRaw == null ? null : Math.round(sumRaw * 100) / 100;
  const avgR = sumRaw == null ? null : Math.round((sumRaw / marks.length) * 100) / 100;
  const bestR = marks.length ? Math.max(...marks) : null;
  const worstR = marks.length ? Math.min(...marks) : null;
  return {
    open: openRows.length,
    reviewed,
    waiting,
    noReview,
    inProfit,
    inLoss,
    flat,
    sumR,
    avgR,
    bestR,
    worstR,
    stanceHold,
    stanceCaution,
    stanceExit,
    stanceNone,
    aiHold,
    aiCaution,
    aiExit,
    aiWait,
    aiNone,
  };
}

export default function Signals({
  active,
  version,
  onStats,
  onOpenSignal,
}: Readonly<{
  active: boolean;
  version: number;
  onStats: (s: Stats) => void;
  onOpenSignal: (id: string) => void;
}>) {
  const { toast, ask } = useFeedback();
  const [signals, setSignals] = useState<Signal[] | null>(null);
  const [stats, setStats] = useState<Stats>({});
  const [error, setError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [checking, setChecking] = useState<string | null>(null);
  const [reviewingId, setReviewingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [bookTab, setBookTab] = useState<BookTab>("trades");
  const [tfTab, setTfTab] = useState<TfTab>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [strategyFilter, setStrategyFilter] = useState<string>("all");
  const [symbolFilter, setSymbolFilter] = useState<string[]>([]);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const isNeutralBook = bookTab === "neutral";

  const refresh = useCallback(async () => {
    try {
      const kind = bookTab === "neutral" ? "neutral" : "trades";
      const res = await api.signals({ kind });
      setSignals(res.signals);
      setStats(res.stats);
      if (kind === "trades") onStats(res.stats);
      else {
        // Keep rail trade KPIs intact while browsing Neutral holds.
        const tradeStats = await api.signals({ kind: "trades", limit: 1 });
        onStats(tradeStats.stats);
      }
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [onStats, bookTab]);

  useEffect(() => {
    api
      .strategies()
      .then((res) => setStrategies(res.strategies))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    setSignals(null);
    refresh().catch(() => undefined);
  }, [active, version, refresh]);

  const coinOptions = useMemo(() => {
    if (!signals?.length) return [];
    const set = new Set<string>();
    for (const s of signals) {
      const sym = normSymbol(s.symbol);
      if (sym) set.add(sym);
    }
    return [...set].sort((a, b) => a.localeCompare(b));
  }, [signals]);

  const filtered = useMemo(() => {
    if (!signals) return null;
    const want = new Set(symbolFilter.map(normSymbol).filter(Boolean));
    return signals.filter((s) => {
      if (!matchesTf(s.timeframe, tfTab)) return false;
      if (
        !isNeutralBook &&
        statusFilter !== "all" &&
        (s.status || "").toLowerCase() !== statusFilter
      ) {
        return false;
      }
      if (strategyFilter !== "all" && normStrategy(s.strategy_id) !== strategyFilter) return false;
      if (want.size && !want.has(normSymbol(s.symbol))) return false;
      return true;
    });
  }, [signals, tfTab, statusFilter, strategyFilter, symbolFilter, isNeutralBook]);

  const viewStats = useMemo(() => {
    if (!filtered) return stats;
    if (isNeutralBook) {
      return {
        total: filtered.length,
        open: 0,
        wins: 0,
        losses: 0,
        expired: 0,
        neutral: filtered.length,
        hit_rate: null,
        avg_r: null,
      };
    }
    if (tfTab === "all" && statusFilter === "all" && strategyFilter === "all" && !symbolFilter.length) {
      return stats;
    }
    return filterStats(filtered);
  }, [filtered, stats, tfTab, statusFilter, strategyFilter, symbolFilter, isNeutralBook]);

  const openBook = useMemo(
    () => (isNeutralBook ? null : openBookStats(filtered ?? [])),
    [filtered, isNeutralBook],
  );

  const tabCounts = useMemo(() => {
    const counts: Record<TfTab, number> = { all: 0, "15m": 0, "1h": 0, "4h": 0, "1d": 0 };
    if (!signals) return counts;
    const want = new Set(symbolFilter.map(normSymbol).filter(Boolean));
    const statusOk = (s: Signal) =>
      isNeutralBook || statusFilter === "all" || (s.status || "").toLowerCase() === statusFilter;
    const strategyOk = (s: Signal) =>
      strategyFilter === "all" || normStrategy(s.strategy_id) === strategyFilter;
    const symbolOk = (s: Signal) => !want.size || want.has(normSymbol(s.symbol));
    for (const s of signals) {
      if (!statusOk(s) || !strategyOk(s) || !symbolOk(s)) continue;
      counts.all += 1;
      const tf = normTf(s.timeframe);
      if (tf === "15m" || tf === "1h" || tf === "4h" || tf === "1d") counts[tf] += 1;
    }
    return counts;
  }, [signals, statusFilter, strategyFilter, symbolFilter, isNeutralBook]);

  async function verifyAll() {
    setVerifying(true);
    try {
      const res = await api.verifySignals();
      toast(`Checked ${String(res.checked)} signals, ${String(res.updated)} updated.`);
    } catch (err) {
      toast(`Verify failed: ${(err as Error).message}`);
    } finally {
      setVerifying(false);
    }
    await refresh();
  }

  async function reviewAll() {
    setReviewing(true);
    try {
      const res = await api.reviewOpenSignals();
      toast(`Live review on ${String(res.checked)} open, ${String(res.updated)} updated.`);
    } catch (err) {
      toast(`Live review failed: ${(err as Error).message}`);
    } finally {
      setReviewing(false);
    }
    await refresh();
  }

  async function check(id: string) {
    setChecking(id);
    try {
      const res = await api.verifySignal(id);
      toast(`${res.signal.symbol}: ${res.signal.status} (${res.signal.outcome ?? "checked"})`);
    } catch (err) {
      toast(`Check failed: ${(err as Error).message}`);
    } finally {
      setChecking(null);
    }
    await refresh();
  }

  async function reviewOne(id: string) {
    setReviewingId(id);
    try {
      const res = await api.reviewSignal(id);
      const stance = res.review?.stance ? STANCE_META[res.review.stance]?.label ?? res.review.stance : "no price";
      toast(`${res.signal.symbol}: ${stance}${res.review?.unrealized_r != null ? ` (${fmtSigned(res.review.unrealized_r, 2)}R)` : ""}`);
      onOpenSignal(res.signal.id);
    } catch (err) {
      toast(`Review failed: ${(err as Error).message}`);
    } finally {
      setReviewingId(null);
    }
    await refresh();
  }

  async function remove(id: string, symbol: string) {
    const ok = await ask({
      title: `Delete ${symbol}?`,
      text: "Removes this signal and its live reviews and pack results. This cannot be undone.",
      okLabel: "Delete",
      danger: true,
    });
    if (!ok) return;
    setDeletingId(id);
    try {
      const res = await api.deleteSignal(id);
      setStats(res.stats);
      onStats(res.stats);
      toast(`${symbol} deleted.`);
    } catch (err) {
      toast(`Could not delete: ${(err as Error).message}`);
    } finally {
      setDeletingId(null);
    }
    await refresh();
  }

  let table: React.ReactNode;
  if (error)
    table = (
      <Alert severity="warning" sx={{ m: 2 }}>
        Signals unavailable: {error}
      </Alert>
    );
  else if (!filtered)
    table = (
      <Box sx={{ p: 2 }}>
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} height={40} />
        ))}
      </Box>
    );
  else if (!signals?.length)
    table = (
      <EmptyState
        text={
          isNeutralBook
            ? "No Neutral holds yet. A full analysis that finishes Neutral saves one here."
            : "No archived signals yet. A full analysis with a Buy or Sell bias saves one here."
        }
        icon={<TrackChanges />}
      />
    );
  else if (!filtered.length) {
    const tfLabel = TF_TABS.find((t) => t.id === tfTab)?.label ?? tfTab;
    const statusLabel = isNeutralBook || statusFilter === "all" ? "" : ` / ${statusFilter}`;
    const stratLabel =
      strategyFilter === "all" ? "" : ` / ${strategyLabel(strategyFilter, strategies)}`;
    const coinLabel = symbolFilter.length ? ` / ${symbolFilter.join(", ")}` : "";
    table = (
      <EmptyState
        text={`No ${isNeutralBook ? "Neutral holds" : "signals"} match ${tfLabel}${statusLabel}${stratLabel}${coinLabel}.`}
        icon={<TrackChanges />}
      />
    );
  } else if (isNeutralBook)
    table = (
      <DataTable minWidth={960}>
        <TableHead>
          <TableRow>
            <TableCell>Created</TableCell>
            <TableCell>Pair</TableCell>
            <TableCell>Strategy</TableCell>
            <TableCell>Bias</TableCell>
            <TableCell align="right">Price</TableCell>
            <TableCell align="right">Confluence</TableCell>
            <TableCell align="right">Confidence</TableCell>
            <TableCell>Why</TableCell>
            <TableCell>Status</TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {filtered.map((s) => (
            <TableRow key={s.id} hover sx={{ cursor: "pointer" }} onClick={() => onOpenSignal(s.id)}>
              <TableCell>
                <V value={fmtWhen(s.created_at)} mono={false} />
              </TableCell>
              <TableCell>
                <Num sx={{ fontWeight: 700 }}>{s.symbol}</Num>{" "}
                <Typography component="span" variant="caption" sx={{ color: "text.secondary" }}>
                  {s.timeframe}
                </Typography>
              </TableCell>
              <TableCell>
                <Chip size="small" label={strategyLabel(s.strategy_id, strategies)} variant="outlined" />
              </TableCell>
              <TableCell>
                <BiasPill bias={s.bias} />
              </TableCell>
              <TableCell align="right">
                <V value={fmtPx(s.price_at_signal)} reason="No mark at archive" />
              </TableCell>
              <TableCell align="right">
                <V value={isNum(s.confluence) ? fmtSigned(s.confluence, 1) : null} reason="No score" />
              </TableCell>
              <TableCell align="right">
                <V
                  value={isNum(s.confidence) ? `${String(Math.round(s.confidence * 100))}%` : null}
                  reason="No confidence"
                />
              </TableCell>
              <TableCell sx={{ maxWidth: 280 }}>
                <Typography
                  variant="body2"
                  sx={{
                    color: "text.secondary",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                  title={s.notes || undefined}
                >
                  {s.notes?.trim() ? s.notes.trim() : <Na reason="No reasoning stored" />}
                </Typography>
              </TableCell>
              <TableCell>
                <StatusPill status={s.status} />
              </TableCell>
              <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                <Button
                  size="small"
                  variant="outlined"
                  color="inherit"
                  aria-label={`Delete ${s.symbol}`}
                  sx={{ borderColor: "divider", minWidth: 0, px: 1 }}
                  disabled={deletingId === s.id}
                  onClick={() => void remove(s.id, s.symbol)}
                >
                  {deletingId === s.id ? (
                    <CircularProgress size={12} color="inherit" />
                  ) : (
                    <DeleteOutlined fontSize="small" />
                  )}
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </DataTable>
    );
  else
    table = (
      <DataTable minWidth={1280}>
        <TableHead>
          <TableRow>
            <TableCell>Created</TableCell>
            <TableCell>Pair</TableCell>
            <TableCell>Strategy</TableCell>
            <TableCell>Bias</TableCell>
            <TableCell align="right">Entry</TableCell>
            <TableCell align="right">Stop</TableCell>
            <TableCell align="right">Target</TableCell>
            <TableCell align="right">Now</TableCell>
            <TableCell>Stance</TableCell>
            <TableCell>Status</TableCell>
            <TableCell align="right">R</TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {filtered.map((s) => {
            const latest = latestReview(s);
            const isOpen = (s.status || "").toLowerCase() === "open";
            const waitingEntry = latest?.entry_status === "waiting";
            const showMark = isOpen && !waitingEntry && isNum(latest?.unrealized_r);
            const tone = showMark ? markTone(latest?.unrealized_r) : null;
            const toneColor = markColor(tone);
            return (
              <TableRow
                key={s.id}
                hover
                sx={{ cursor: "pointer", ...markRowSx(tone) }}
                onClick={() => onOpenSignal(s.id)}
              >
                <TableCell>
                  <V value={fmtWhen(s.created_at)} mono={false} />
                </TableCell>
                <TableCell>
                  <Num sx={{ fontWeight: 700 }}>{s.symbol}</Num>{" "}
                  <Typography component="span" variant="caption" sx={{ color: "text.secondary" }}>
                    {s.timeframe}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip size="small" label={strategyLabel(s.strategy_id, strategies)} variant="outlined" />
                </TableCell>
                <TableCell>
                  <BiasPill bias={s.bias} />
                </TableCell>
                <TableCell align="right">
                  <V value={fmtPx(s.entry)} />
                </TableCell>
                <TableCell align="right">
                  <V value={fmtPx(s.stop_loss)} />
                </TableCell>
                <TableCell align="right">
                  <V value={fmtPx(s.take_profit)} />
                </TableCell>
                <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                  {latest?.price != null ? (
                    <Stack spacing={0} sx={{ alignItems: "flex-end" }}>
                      <Num sx={{ fontWeight: 600, color: showMark ? toneColor : "text.primary" }}>
                        {fmtPx(latest.price)}
                      </Num>
                      {waitingEntry ? (
                        <Typography variant="caption" sx={{ color: "text.secondary" }}>
                          Entry waiting · vs {fmtPx(s.entry)}
                        </Typography>
                      ) : showMark && isNum(latest.unrealized_r) ? (
                        <Typography variant="caption" sx={{ color: toneColor, fontWeight: 600 }}>
                          {tone === "profit" ? "▲ profit" : tone === "loss" ? "▼ loss" : "◆ flat"}{" "}
                          {fmtSigned(latest.unrealized_r, 2)}R
                        </Typography>
                      ) : (
                        <Typography variant="caption" sx={{ color: "text.secondary" }}>
                          vs entry {fmtPx(s.entry)}
                        </Typography>
                      )}
                    </Stack>
                  ) : (
                    <Na reason="Run live review" />
                  )}
                </TableCell>
                <TableCell onClick={(e) => e.stopPropagation()}>
                  <Stack spacing={0.25}>
                    <StanceChip stance={latest?.stance} />
                    {latest?.ai_stance ? (
                      <Typography variant="caption" sx={{ color: "text.secondary" }}>
                        AI {humanize(latest.ai_stance)}
                      </Typography>
                    ) : null}
                    {latest?.entry_status === "waiting" ? (
                      <Typography variant="caption" sx={{ color: "text.secondary" }}>
                        Entry waiting
                      </Typography>
                    ) : null}
                    {latest?.level_advice?.stop?.action &&
                    latest.level_advice.stop.action !== "keep" &&
                    latest.level_advice.stop.action !== "locked" ? (
                      <Typography variant="caption" sx={{ color: "text.secondary" }}>
                        SL {latest.level_advice.stop.action}
                      </Typography>
                    ) : null}
                  </Stack>
                </TableCell>
                <TableCell>
                  <Stack spacing={0.25}>
                    <StatusPill status={s.status} title={s.outcome ?? undefined} />
                    {isOpen && latest ? (
                      <Typography variant="caption" sx={{ color: "text.secondary" }}>
                        {latest.verify_status === "win" || latest.verify_status === "loss"
                          ? humanize(latest.verify_status)
                          : "Levels not hit"}
                      </Typography>
                    ) : null}
                  </Stack>
                </TableCell>
                <TableCell align="right">
                  {isOpen && isNum(latest?.unrealized_r) ? (
                    <Box component="span" title="If closed at last review price">
                      <Num sx={{ color: toneColor, fontWeight: 700 }}>{fmtSigned(latest.unrealized_r, 2)}R</Num>
                    </Box>
                  ) : (
                    <V value={fmtSigned(s.r_multiple, 2)} reason={s.status === "open" ? "Still open" : "Not decided"} />
                  )}
                </TableCell>
                <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                  <Stack direction="row" spacing={0.75} sx={{ justifyContent: "flex-end" }}>
                    {isOpen ? (
                      <Button
                        size="small"
                        variant="outlined"
                        color="inherit"
                        sx={{ borderColor: "divider" }}
                        disabled={reviewingId === s.id}
                        startIcon={reviewingId === s.id ? <CircularProgress size={12} color="inherit" /> : <Update sx={{ fontSize: 14 }} />}
                        onClick={() => void reviewOne(s.id)}
                      >
                        Review
                      </Button>
                    ) : null}
                    <Button
                      size="small"
                      variant="outlined"
                      color="inherit"
                      sx={{ borderColor: "divider" }}
                      disabled={checking === s.id}
                      startIcon={checking === s.id ? <CircularProgress size={12} color="inherit" /> : undefined}
                      onClick={() => void check(s.id)}
                    >
                      Check
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      color="inherit"
                      aria-label={`Delete ${s.symbol}`}
                      sx={{ borderColor: "divider", minWidth: 0, px: 1 }}
                      disabled={deletingId === s.id}
                      onClick={() => void remove(s.id, s.symbol)}
                    >
                      {deletingId === s.id ? (
                        <CircularProgress size={12} color="inherit" />
                      ) : (
                        <DeleteOutlined fontSize="small" />
                      )}
                    </Button>
                  </Stack>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </DataTable>
    );

  return (
    <Stack spacing={2}>
      <PageHeader
        title="Signals"
        subtitle={
          isNeutralBook
            ? "Neutral holds from full analysis. Kept apart from tradeable Buy/Sell signals. Click a row for the archived context."
            : "Every Buy or Sell from a full analysis. Click a row for pack details and live review history. Original plan stays frozen."
        }
        actions={
          <>
            <ActionButton icon={<Refresh />} onClick={() => void refresh()}>
              Refresh
            </ActionButton>
            {!isNeutralBook ? (
              <>
                <ActionButton icon={<Update />} busy={reviewing} busyLabel="Reviewing…" onClick={() => void reviewAll()}>
                  Live review open
                </ActionButton>
                <ActionButton icon={<DoneAll />} primary busy={verifying} busyLabel="Verifying…" onClick={() => void verifyAll()}>
                  Verify open signals
                </ActionButton>
              </>
            ) : null}
          </>
        }
      />
      <Tabs
        value={bookTab}
        onChange={(_, v: BookTab) => {
          setBookTab(v);
          setTfTab("all");
          setStatusFilter("all");
          setSymbolFilter([]);
        }}
        aria-label="Trades or Neutral holds"
        sx={{ minHeight: 44, borderBottom: 1, borderColor: "divider", "& .MuiTab-root": { minHeight: 44, textTransform: "none" } }}
      >
        {BOOK_TABS.map((t) => (
          <Tab key={t.id} value={t.id} label={t.label} />
        ))}
      </Tabs>
      <KpiStrip
        tiles={
          isNeutralBook
            ? [
                {
                  label: "Neutral holds",
                  value: String(viewStats.neutral ?? viewStats.total ?? 0),
                  note: "Archived, not traded",
                },
                {
                  label: "In view",
                  value: String(filtered?.length ?? 0),
                  note: "After filters",
                },
                {
                  label: "Strategies",
                  value: String(
                    new Set((filtered ?? []).map((s) => normStrategy(s.strategy_id))).size,
                  ),
                  note: "Distinct packs",
                },
                {
                  label: "Coins",
                  value: String(new Set((filtered ?? []).map((s) => normSymbol(s.symbol))).size),
                  note: "Distinct pairs",
                },
              ]
            : [
                {
                  label: "Hit rate",
                  value: isNum(viewStats.hit_rate) ? `${String(Math.round(viewStats.hit_rate * 100))}%` : <Na reason="No decided signals yet" />,
                  note: "Target before stop",
                },
                {
                  label: "Wins / losses",
                  value: `${String(viewStats.wins ?? 0)} / ${String(viewStats.losses ?? 0)}`,
                  note: `${String(viewStats.expired ?? 0)} expired`,
                },
                { label: "Open", value: String(viewStats.open ?? 0), note: "Neither level hit yet" },
                {
                  label: "Average R",
                  value: <V value={fmtSigned(viewStats.avg_r, 2)} reason="No closed signals" />,
                  note: `${String(viewStats.total ?? 0)} in view`,
                },
              ]
        }
      />
      <Card>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1.5}
          sx={{
            px: 2,
            pt: 1.5,
            borderBottom: 1,
            borderColor: "divider",
            alignItems: { xs: "stretch", sm: "center" },
            justifyContent: "space-between",
          }}
        >
          <Tabs
            value={tfTab}
            onChange={(_, v: TfTab) => setTfTab(v)}
            variant="scrollable"
            scrollButtons="auto"
            aria-label="Filter signals by timeframe"
            sx={{ minHeight: 44, "& .MuiTab-root": { minHeight: 44, textTransform: "none" } }}
          >
            {TF_TABS.map((t) => (
              <Tab
                key={t.id}
                value={t.id}
                label={
                  <Stack direction="row" spacing={0.75} sx={{ alignItems: "center" }}>
                    <span>{t.label}</span>
                    <Chip size="small" label={tabCounts[t.id]} sx={{ height: 20, "& .MuiChip-label": { px: 0.75 } }} />
                  </Stack>
                }
              />
            ))}
          </Tabs>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mb: { xs: 1.5, sm: 1.5 }, mr: { sm: 0.5 } }}>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel id="signal-strategy-filter-label">Strategy</InputLabel>
              <Select
                labelId="signal-strategy-filter-label"
                label="Strategy"
                value={strategyFilter}
                onChange={(e) => setStrategyFilter(String(e.target.value))}
              >
                <MenuItem value="all">All strategies</MenuItem>
                {(strategies.length
                  ? strategies
                  : [{ id: "desk", label: "Desk (default)", summary: "" }]
                ).map((s) => (
                  <MenuItem key={s.id} value={s.id}>
                    {s.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {!isNeutralBook ? (
              <FormControl size="small" sx={{ minWidth: 160 }}>
                <InputLabel id="signal-status-filter-label">Status</InputLabel>
                <Select
                  labelId="signal-status-filter-label"
                  label="Status"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                >
                  {STATUS_OPTIONS.map((o) => (
                    <MenuItem key={o.id} value={o.id}>
                      {o.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            ) : null}
          </Stack>
        </Stack>
        <Box sx={{ px: 2, py: 1.5, borderBottom: 1, borderColor: "divider" }}>
          <Autocomplete
            multiple
            size="small"
            options={coinOptions}
            value={symbolFilter}
            onChange={(_, v) => setSymbolFilter(v.map(normSymbol).filter(Boolean))}
            disableCloseOnSelect
            renderInput={(params) => (
              <TextField
                {...params}
                label="Coins"
                placeholder={symbolFilter.length ? undefined : "All coins in archive"}
              />
            )}
          />
        </Box>
        {table}
      </Card>

      {openBook ? (
      <SectionCard
        title="Open book"
        right={
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            Mark vs locked entry from the latest live review · current filters
          </Typography>
        }
      >
        {openBook.open === 0 ? (
          <EmptyState text="No open signals in this view. Open positions will show mark R and profit counts here." />
        ) : (
          <Stack spacing={1.5}>
            <KpiStrip
              tiles={[
                {
                  label: "Open",
                  value: String(openBook.open),
                  note: `${String(openBook.reviewed)} reviewed · ${String(openBook.waiting)} waiting entry · ${String(openBook.noReview)} not reviewed`,
                },
                {
                  label: "In profit",
                  value: String(openBook.inProfit),
                  note: "Unrealized R above +0.02",
                  tone: openBook.inProfit > 0 ? "buy" : "text",
                },
                {
                  label: "In loss",
                  value: String(openBook.inLoss),
                  note: "Unrealized R below -0.02",
                  tone: openBook.inLoss > 0 ? "sell" : "text",
                },
                {
                  label: "Flat",
                  value: String(openBook.flat),
                  note: "Around entry or no mark R",
                },
              ]}
            />
            <KpiStrip
              tiles={[
                {
                  label: "Book R",
                  value:
                    openBook.sumR == null ? (
                      <Na reason="Run live review on open rows" />
                    ) : (
                      <Num sx={{ color: markColor(markTone(openBook.sumR)), fontWeight: 700 }}>
                        {fmtSigned(openBook.sumR, 2)}R
                      </Num>
                    ),
                  note: "Sum of mark R if closed now",
                  tone: openBook.sumR == null ? "text" : openBook.sumR > 0 ? "buy" : openBook.sumR < 0 ? "sell" : "text",
                },
                {
                  label: "Avg mark R",
                  value:
                    openBook.avgR == null ? (
                      <Na reason="No reviewed marks" />
                    ) : (
                      <Num sx={{ color: markColor(markTone(openBook.avgR)), fontWeight: 700 }}>
                        {fmtSigned(openBook.avgR, 2)}R
                      </Num>
                    ),
                  note: "Mean across reviewed open",
                  tone: openBook.avgR == null ? "text" : openBook.avgR > 0 ? "buy" : openBook.avgR < 0 ? "sell" : "text",
                },
                {
                  label: "Best mark",
                  value:
                    openBook.bestR == null ? (
                      <Na reason="No reviewed marks" />
                    ) : (
                      <Num sx={{ color: "success.main", fontWeight: 700 }}>{fmtSigned(openBook.bestR, 2)}R</Num>
                    ),
                  note: "Highest unrealized R",
                  tone: openBook.bestR != null ? "buy" : "text",
                },
                {
                  label: "Worst mark",
                  value:
                    openBook.worstR == null ? (
                      <Na reason="No reviewed marks" />
                    ) : (
                      <Num sx={{ color: "error.main", fontWeight: 700 }}>{fmtSigned(openBook.worstR, 2)}R</Num>
                    ),
                  note: "Lowest unrealized R",
                  tone: openBook.worstR != null ? "sell" : "text",
                },
              ]}
            />
            <KpiStrip
              tiles={[
                {
                  label: "Rules Hold",
                  value: String(openBook.stanceHold),
                  note: `○ ${STANCE_META.hold.label} · latest review`,
                },
                {
                  label: "Rules Caution",
                  value: String(openBook.stanceCaution),
                  note: `△ ${STANCE_META.caution.label}`,
                },
                {
                  label: "Rules Exit early",
                  value: String(openBook.stanceExit),
                  note: `▸ ${STANCE_META.exit_early.label}`,
                  tone: openBook.stanceExit > 0 ? "sell" : "text",
                },
                {
                  label: "No rule stance",
                  value: String(openBook.stanceNone),
                  note: "Not reviewed or no stance",
                },
              ]}
            />
            <KpiStrip
              tiles={[
                {
                  label: "AI Hold",
                  value: String(openBook.aiHold),
                  note: "AI stance on latest review",
                },
                {
                  label: "AI Caution",
                  value: String(openBook.aiCaution),
                  note: "AI stance",
                },
                {
                  label: "AI Exit / wait",
                  value: String(openBook.aiExit + openBook.aiWait),
                  note: `${String(openBook.aiExit)} exit · ${String(openBook.aiWait)} wait entry`,
                  tone: openBook.aiExit + openBook.aiWait > 0 ? "sell" : "text",
                },
                {
                  label: "No AI stance",
                  value: String(openBook.aiNone),
                  note: "Brief off, skipped, or none",
                },
              ]}
            />
          </Stack>
        )}
      </SectionCard>
      ) : null}
    </Stack>
  );
}
