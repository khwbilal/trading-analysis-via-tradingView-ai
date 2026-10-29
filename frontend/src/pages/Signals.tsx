import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import InputAdornment from "@mui/material/InputAdornment";
import MenuItem from "@mui/material/MenuItem";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Tab from "@mui/material/Tab";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Tabs from "@mui/material/Tabs";
import TextField from "@mui/material/TextField";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import DeleteOutlined from "@mui/icons-material/DeleteOutlined";
import DoneAll from "@mui/icons-material/DoneAll";
import RateReviewOutlined from "@mui/icons-material/RateReviewOutlined";
import Refresh from "@mui/icons-material/Refresh";
import Tune from "@mui/icons-material/Tune";
import TrackChanges from "@mui/icons-material/TrackChanges";
import { useCallback, useEffect, useState } from "react";
import { api, type MarginMode, type PaperSettings, type Signal, type Stats, type StoredAnalysis } from "../api";
import SignalDetailDialog, { PnlText, ProgressTrack, usd } from "../components/SignalDetail";
import { PaperWalletPicker } from "../components/WalletDialogs";
import { useFeedback } from "../components/feedback";
import { ActionButton, BiasPill, DataTable, EmptyState, KpiStrip, Na, Num, PageHeader, Pill, StatusPill, V } from "../components/ui";
import { fmtPx, fmtSigned, fmtWhen, humanize, isNum } from "../lib/format";
import { oneOf, usePref } from "../lib/storage";
import SignalDetailPage from "./SignalDetail";

const PAGE = 50;
const LIVE_MS = 30_000; // WL-108: running signals refresh their price this often while the page is open

/** The paper defaults new signals get (WL-109). */
function PaperSettingsDialog({ value, onClose, onSaved }: Readonly<{ value: PaperSettings; onClose: () => void; onSaved: (v: PaperSettings) => void }>) {
  const { toast } = useFeedback();
  const [margin, setMargin] = useState(String(value.margin));
  const [leverage, setLeverage] = useState(String(value.leverage));
  const [mode, setMode] = useState<MarginMode>(value.margin_mode);
  const [balance, setBalance] = useState(String(value.cross_balance));
  const [wallet, setWallet] = useState(value.wallet_id || 0);
  const [busy, setBusy] = useState(false);
  const num = (s: string) => Number(s.replace(",", "."));
  async function save() {
    setBusy(true);
    try {
      onSaved(await api.savePaperSettings({ margin: num(margin), leverage: num(leverage), margin_mode: mode, cross_balance: num(balance), wallet_id: wallet }));
      toast("Paper defaults saved. New signals use them.");
      onClose();
    } catch (err) {
      toast(`Not saved: ${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  }
  const usdt = { input: { endAdornment: <InputAdornment position="end">USDT</InputAdornment> } };
  return (
    <Dialog open onClose={onClose} fullWidth maxWidth="xs" aria-labelledby="paperTitle">
      <DialogTitle id="paperTitle">Paper trade defaults</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <Typography variant="body2" sx={{ color: "text.secondary" }}>
            Every new signal is a paper USD-M futures trade with these. Each signal can be changed on its own.
          </Typography>
          <TextField label="Margin" value={margin} onChange={(e) => setMargin(e.target.value)} slotProps={usdt} />
          <TextField select label="Leverage" value={leverage} onChange={(e) => setLeverage(e.target.value)}>
            {[1, 2, 3, 5, 10, 15, 20, 25, 50, 75, 100, 125].map((l) => (
              <MenuItem key={l} value={String(l)}>
                {l}x
              </MenuItem>
            ))}
          </TextField>
          <Typography variant="body2">
            Position: <Num sx={{ fontWeight: 700 }}>{usd(num(margin) * num(leverage)) ?? "none"}</Num>
          </Typography>
          <ToggleButtonGroup exclusive value={mode} onChange={(_e, v: MarginMode | null) => v && setMode(v)} aria-label="Margin mode" size="small">
            <ToggleButton value="isolated" sx={{ px: 2 }}>
              Isolated
            </ToggleButton>
            <ToggleButton value="cross" sx={{ px: 2 }}>
              Cross
            </ToggleButton>
          </ToggleButtonGroup>
          <TextField label="Cross balance" value={balance} onChange={(e) => setBalance(e.target.value)} slotProps={usdt} helperText="The paper wallet behind every cross signal" />
          <PaperWalletPicker value={wallet} onChange={setWallet} label="New signals count in" />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button color="inherit" onClick={onClose}>
          Cancel
        </Button>
        <ActionButton primary busy={busy} busyLabel="Saving…" onClick={() => void save()}>
          Save
        </ActionButton>
      </DialogActions>
    </Dialog>
  );
}

/** WL-108: how a running trade is going, or what a closed one made. */
function Going({ s }: Readonly<{ s: Signal }>) {
  const p = s.paper;
  if (!p) return <Na reason="No complete levels" />;
  if (p.live)
    return (
      <Stack spacing={0.5} sx={{ minWidth: 150 }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: "baseline" }}>
          <Num>{fmtPx(p.live.price)}</Num>
          <PnlText r={p.live} />
        </Stack>
        <ProgressTrack progress={p.live.progress} towards={p.live.towards} />
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          {fmtSigned(p.live.r, 2)}R · {fmtSigned(p.live.roe, 1)}% on margin
        </Typography>
        {p.live.liquidated ? <Pill glyph="⚠" label="past liquidation" tone="error" title={`Liquidation at ${fmtPx(p.liquidation) ?? ""}`} /> : null}
      </Stack>
    );
  if (p.closed) return <PnlText r={p.closed} />;
  if (s.outcome === "waiting_for_entry") return <Na reason="Entry not reached yet" />;
  return <Na reason={s.status === "open" ? "No live price" : "Not decided"} />;
}

function SignalsTable({
  signals,
  onOpen,
  onCheck,
  onDelete,
  checking,
  deleting,
}: Readonly<{
  signals: Signal[];
  onOpen: (s: Signal) => void;
  onCheck: (id: string) => void;
  onDelete: (id: string, symbol: string) => void;
  checking: string | null;
  deleting: string | null;
}>) {
  return (
    <DataTable minWidth={1280}>
      <TableHead>
        <TableRow>
          <TableCell>Created</TableCell>
          <TableCell>Pair</TableCell>
          <TableCell>Bias</TableCell>
          <TableCell>Setup</TableCell>
          <TableCell align="right">Entry</TableCell>
          <TableCell align="right">Stop</TableCell>
          <TableCell align="right">Target</TableCell>
          <TableCell>Paper trade</TableCell>
          <TableCell>How it is going</TableCell>
          <TableCell>Status</TableCell>
          <TableCell align="right">R</TableCell>
          <TableCell />
        </TableRow>
      </TableHead>
      <TableBody>
        {signals.map((s) => (
          <TableRow key={s.id} hover onClick={() => onOpen(s)} sx={{ cursor: "pointer" }} title="Open the chart, analysis and chat">
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
              <BiasPill bias={s.bias} />
            </TableCell>
            <TableCell>{s.setup ? <Chip size="small" label={humanize(s.setup)} /> : <Na />}</TableCell>
            <TableCell align="right">
              <V value={fmtPx(s.entry)} />
            </TableCell>
            <TableCell align="right">
              <V value={fmtPx(s.stop_loss)} />
            </TableCell>
            <TableCell align="right">
              <V value={fmtPx(s.take_profit)} />
            </TableCell>
            <TableCell sx={{ whiteSpace: "nowrap" }}>
              {s.paper ? (
                <>
                  <Num>
                    {usd(s.paper.margin)} · {s.paper.leverage}x
                  </Num>
                  <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                    {usd(s.paper.notional)} {s.paper.margin_mode}
                  </Typography>
                  {s.paper.liquidated_before_stop ? <Pill glyph="⚠" label="liquidated before stop" tone="warn" /> : null}
                </>
              ) : (
                <Na reason="No complete levels" />
              )}
            </TableCell>
            <TableCell>
              <Going s={s} />
            </TableCell>
            <TableCell>
              <StatusPill status={s.status} title={s.outcome ?? undefined} />
            </TableCell>
            <TableCell align="right">
              <V value={fmtSigned(s.r_multiple, 2)} reason={s.status === "open" ? "Still open" : "Not decided"} />
            </TableCell>
            <TableCell align="right" onClick={(e) => e.stopPropagation()}>
              <Stack direction="row" spacing={0.75} sx={{ justifyContent: "flex-end" }}>
                <Button
                  size="small"
                  variant="outlined"
                  color="inherit"
                  sx={{ borderColor: "divider" }}
                  disabled={checking === s.id}
                  startIcon={checking === s.id ? <CircularProgress size={12} color="inherit" /> : undefined}
                  onClick={() => onCheck(s.id)}
                >
                  Check
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  color="inherit"
                  aria-label={`Delete ${s.symbol}`}
                  sx={{ borderColor: "divider", minWidth: 0, px: 1 }}
                  disabled={deleting === s.id}
                  onClick={() => onDelete(s.id, s.symbol)}
                >
                  {deleting === s.id ? <CircularProgress size={12} color="inherit" /> : <DeleteOutlined fontSize="small" />}
                </Button>
              </Stack>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </DataTable>
  );
}

type Tab = "signals" | "neutral" | "watch" | "all" | "analyses";

/** WL-117: the side a Neutral call's levels lean, from where its stop sits. */
function lean(a: StoredAnalysis): string | null {
  const { entry, stop_loss: stop } = a.levels;
  if (!isNum(entry) || !isNum(stop) || entry === stop) return null;
  return stop > entry ? "short" : "long";
}

function WatchPill({ a }: Readonly<{ a: StoredAnalysis }>) {
  const side = lean(a);
  return (
    <Pill
      glyph="◷"
      label={side ? `On watch, leans ${side}` : "On watch"}
      tone="neutral"
      title="Neutral call: a setup waiting for its trigger, not a paper trade"
    />
  );
}

function SignalCell({ a, kind }: Readonly<{ a: StoredAnalysis; kind: "all" | "watch" }>) {
  if (kind === "watch") return <WatchPill a={a} />;
  return a.signal_id ? <Num>{a.signal_id}</Num> : <Na reason="Neutral or offline: no signal" />;
}

/** WL-107: every stored analysis, newest first, with paging. kind=watch: only the calls on watch (WL-117). */
function AnalysesTable({ active, onOpen, kind = "all" }: Readonly<{ active: boolean; onOpen: (id: number) => void; kind?: "all" | "watch" }>) {
  const [offset, setOffset] = usePref(`cca_analyses_offset_${kind}`, 0);
  const [symbol, setSymbol] = usePref(`cca_analyses_symbol_${kind}`, "");
  const [data, setData] = useState<{ analyses: StoredAnalysis[]; total: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!active) return;
    const id = setTimeout(() => {
      api
        .analyses(PAGE, offset, symbol.trim(), kind)
        .then((d) => {
          setData(d);
          setError(null);
        })
        .catch((err: Error) => setError(err.message));
    }, 250);
    return () => clearTimeout(id);
  }, [active, offset, symbol, kind]);
  return (
    <>
      <Box sx={{ p: 2 }}>
        <TextField
          size="small"
          label="Pair"
          placeholder="SOLUSDT"
          value={symbol}
          onChange={(e) => {
            setOffset(0);
            setSymbol(e.target.value.toUpperCase());
          }}
        />
      </Box>
      {error ? <Alert severity="warning" sx={{ m: 2 }}>Analyses unavailable: {error}</Alert> : null}
      {!data && !error ? <Skeleton height={200} sx={{ mx: 2 }} /> : null}
      {data && !data.analyses.length ? (
        <EmptyState
          text={
            kind === "watch"
              ? "No calls on watch. A full analysis that ends Neutral (a setup still waiting for its trigger) shows here."
              : "No analyses kept yet. Every full analysis from now on is stored here with its chat."
          }
          icon={<TrackChanges />}
        />
      ) : null}
      {data?.analyses.length ? (
        <DataTable minWidth={1040}>
          <TableHead>
            <TableRow>
              <TableCell>Created</TableCell>
              <TableCell>Pair</TableCell>
              <TableCell>Bias</TableCell>
              <TableCell align="right">Entry</TableCell>
              <TableCell align="right">Stop</TableCell>
              <TableCell align="right">Target</TableCell>
              <TableCell>By</TableCell>
              <TableCell align="right">Chat</TableCell>
              <TableCell>{kind === "watch" ? "Call" : "Signal"}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.analyses.map((a) => (
              <TableRow key={a.id} hover onClick={() => onOpen(a.id)} sx={{ cursor: "pointer" }}>
                <TableCell>
                  <V value={fmtWhen(a.created_at)} mono={false} />
                </TableCell>
                <TableCell>
                  <Num sx={{ fontWeight: 700 }}>{a.symbol}</Num>{" "}
                  <Typography component="span" variant="caption" sx={{ color: "text.secondary" }}>
                    {a.timeframe}
                  </Typography>
                </TableCell>
                <TableCell>{a.bias ? <BiasPill bias={a.bias} /> : <Na />}</TableCell>
                <TableCell align="right">
                  <V value={fmtPx(a.levels.entry)} />
                </TableCell>
                <TableCell align="right">
                  <V value={fmtPx(a.levels.stop_loss)} />
                </TableCell>
                <TableCell align="right">
                  <V value={fmtPx(a.levels.take_profit)} />
                </TableCell>
                <TableCell sx={{ color: "text.secondary" }}>
                  {a.provider}
                  {a.agent ? ` · ${a.agent}` : ""}
                </TableCell>
                <TableCell align="right">
                  <Num>{a.chats ?? 0}</Num>
                </TableCell>
                <TableCell>
                  <SignalCell a={a} kind={kind} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </DataTable>
      ) : null}
      {data && data.total > PAGE ? (
        <Stack direction="row" spacing={1} sx={{ p: 1.5, justifyContent: "flex-end", alignItems: "center" }}>
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            {String(offset + 1)} to {String(Math.min(offset + PAGE, data.total))} of {data.total.toLocaleString()}
          </Typography>
          <ActionButton compact disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
            Newer
          </ActionButton>
          <ActionButton compact disabled={offset + PAGE >= data.total} onClick={() => setOffset(offset + PAGE)}>
            Older
          </ActionButton>
        </Stack>
      ) : null}
    </>
  );
}

type CallRow = { at: string; signal: Signal | null; analysis: StoredAnalysis | null };

function CallStatus({ s }: Readonly<{ s: Signal | null }>) {
  if (s) return <StatusPill status={s.status} title={s.outcome ?? undefined} />;
  return (
    <Typography variant="body2" sx={{ color: "text.secondary" }}>
      Watching
    </Typography>
  );
}

/** WL-117: the trades and the calls on watch in one list, newest first. */
function AllCalls({ active, signals, onOpen }: Readonly<{ active: boolean; signals: Signal[]; onOpen: (signal: Signal | null, analysisId: number | null) => void }>) {
  const [watch, setWatch] = useState<StoredAnalysis[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!active) return;
    api
      .analyses(500, 0, "", "watch")
      .then((d) => {
        setWatch(d.analyses);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, [active]);
  if (error)
    return (
      <Alert severity="warning" sx={{ m: 2 }}>
        Calls on watch unavailable: {error}
      </Alert>
    );
  if (!watch) return <Skeleton height={200} sx={{ mx: 2 }} />;
  const rows: CallRow[] = [
    ...signals.map((s) => ({ at: s.created_at ?? "", signal: s, analysis: null })),
    ...watch.map((a) => ({ at: a.created_at, signal: null, analysis: a })),
  ].sort((x, y) => (Date.parse(y.at) || 0) - (Date.parse(x.at) || 0));
  if (!rows.length) return <EmptyState text="No trades or calls on watch yet." icon={<TrackChanges />} />;
  return (
    <DataTable minWidth={980}>
      <TableHead>
        <TableRow>
          <TableCell>Created</TableCell>
          <TableCell>Pair</TableCell>
          <TableCell>Call</TableCell>
          <TableCell align="right">Entry</TableCell>
          <TableCell align="right">Stop</TableCell>
          <TableCell align="right">Target</TableCell>
          <TableCell>Status</TableCell>
          <TableCell align="right">R</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map(({ signal: s, analysis: a, at }) => (
          <TableRow
            key={s ? `s-${s.id}` : `a-${String(a?.id)}`}
            hover
            onClick={() => onOpen(s, a ? a.id : null)}
            sx={{ cursor: "pointer" }}
            title="Open the chart, analysis and chat"
          >
            <TableCell>
              <V value={fmtWhen(at)} mono={false} />
            </TableCell>
            <TableCell>
              <Num sx={{ fontWeight: 700 }}>{s?.symbol ?? a?.symbol}</Num>{" "}
              <Typography component="span" variant="caption" sx={{ color: "text.secondary" }}>
                {s?.timeframe ?? a?.timeframe}
              </Typography>
            </TableCell>
            <TableCell>{s || !a ? <BiasPill bias={s?.bias} /> : <WatchPill a={a} />}</TableCell>
            <TableCell align="right">
              <V value={fmtPx(s ? s.entry : a?.levels.entry)} />
            </TableCell>
            <TableCell align="right">
              <V value={fmtPx(s ? s.stop_loss : a?.levels.stop_loss)} />
            </TableCell>
            <TableCell align="right">
              <V value={fmtPx(s ? s.take_profit : a?.levels.take_profit)} />
            </TableCell>
            <TableCell>
              <CallStatus s={s} />
            </TableCell>
            <TableCell align="right">
              {s ? <V value={fmtSigned(s.r_multiple, 2)} reason={s.status === "open" ? "Still open" : "Not decided"} /> : <Na reason="Not a paper trade" />}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </DataTable>
  );
}

export default function Signals({
  active,
  version,
  onStats,
}: Readonly<{ active: boolean; version: number; onStats: (s: Stats) => void }>) {
  const { toast, ask } = useFeedback();
  const [tab, setTab] = usePref<Tab>("cca_signals_tab", "signals", oneOf("signals", "watch", "all", "analyses", "neutral"));
  const [detailId, setDetailId] = useState<string | null>(() => {
    const parts = window.location.hash.replace(/^#\/?/, "").split("/");
    return parts[0] === "signals" && parts[1] ? parts[1] : null;
  });
  const [signals, setSignals] = useState<Signal[] | null>(null);
  const [stats, setStats] = useState<Stats>({});
  const [error, setError] = useState<string | null>(null);
  const [priceError, setPriceError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [reviewingOpen, setReviewingOpen] = useState(false);
  const [checking, setChecking] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [settings, setSettings] = useState<PaperSettings | null>(null);
  const [editing, setEditing] = useState(false);
  const [open, setOpen] = useState<{ signal: Signal | null; analysisId: number | null } | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await api.signals({ kind: tab === "neutral" ? "neutral" : "trades" });
      setSignals(res.signals);
      setStats(res.stats);
      setPriceError(res.price_error ?? null);
      onStats(res.stats);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [onStats, tab]);

  useEffect(() => {
    const onHash = () => {
      const parts = window.location.hash.replace(/^#\/?/, "").split("/");
      setDetailId(parts[0] === "signals" && parts[1] ? parts[1] : null);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  function openDetail(s: Signal) {
    window.location.hash = `#/signals/${s.id}`;
    setDetailId(s.id);
  }

  useEffect(() => {
    // Load on mount (rail counts), when the page is opened, and after outside changes.
    refresh().catch(() => undefined);
  }, [active, version, refresh]);
  const running = Boolean(signals?.some((s) => s.status === "open"));
  useEffect(() => {
    if (!active || !running || tab !== "signals") return;
    const id = setInterval(() => void refresh(), LIVE_MS);
    return () => clearInterval(id);
  }, [active, running, tab, refresh]);
  useEffect(() => {
    if (!active || settings) return;
    api
      .paperSettings()
      .then(setSettings)
      .catch(() => undefined);
  }, [active, settings]);

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

  async function reviewOpen() {
    setReviewingOpen(true);
    try {
      const res = await api.reviewOpenSignals();
      toast(`Live-reviewed ${String(res.reviewed)} of ${String(res.open)} open trades.`);
      if (res.errors?.length) toast(res.errors.slice(0, 2).join("; "));
    } catch (err) {
      toast(`Live review failed: ${(err as Error).message}`);
    } finally {
      setReviewingOpen(false);
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

  async function remove(id: string, symbol: string) {
    const ok = await ask({
      title: `Delete ${symbol}?`,
      text: "Removes this signal and its live reviews and pack results. This cannot be undone.",
      okLabel: "Delete",
      danger: true,
    });
    if (!ok) return;
    setDeleting(id);
    try {
      await api.deleteSignal(id);
      toast(`${symbol} deleted.`);
    } catch (err) {
      toast(`Could not delete: ${(err as Error).message}`);
    } finally {
      setDeleting(null);
    }
    await refresh();
  }

  const openPnl = (signals ?? []).reduce((sum, s) => sum + (s.paper?.live?.pnl ?? 0), 0);
  const closedPnl = (signals ?? []).reduce((sum, s) => sum + (s.paper?.closed?.pnl ?? 0), 0);

  let table: React.ReactNode;
  if (error)
    table = (
      <Alert severity="warning" sx={{ m: 2 }}>
        Signals unavailable: {error}
      </Alert>
    );
  else if (!signals)
    table = (
      <Box sx={{ p: 2 }}>
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} height={40} />
        ))}
      </Box>
    );
  else if (!signals.length)
    table = (
      <EmptyState
        text={
          tab === "neutral"
            ? "No Neutral holds yet. A full analysis that finishes Neutral saves one here."
            : "No archived signals yet. A full analysis with a Buy or Sell bias saves one here."
        }
        icon={<TrackChanges />}
      />
    );
  else
    table = (
      <SignalsTable
        signals={signals}
        onOpen={(s) => openDetail(s)}
        onCheck={(id) => void check(id)}
        onDelete={(id, symbol) => void remove(id, symbol)}
        checking={checking}
        deleting={deleting}
      />
    );

  if (detailId) {
    return (
      <SignalDetailPage
        signalId={detailId}
        onBack={() => {
          window.location.hash = "#/signals";
          setDetailId(null);
        }}
        onChanged={() => void refresh()}
      />
    );
  }

  return (
    <Stack spacing={2}>
      <PageHeader
        title="Signals"
        subtitle="Every Buy or Sell from a full analysis, as a paper futures trade checked against later candles. Click a row for its chart, analysis and chat."
        actions={
          <>
            <ActionButton icon={<Tune />} disabled={!settings} onClick={() => setEditing(true)}>
              Paper defaults
            </ActionButton>
            <ActionButton icon={<Refresh />} onClick={() => void refresh()}>
              Refresh
            </ActionButton>
            <ActionButton
              icon={<RateReviewOutlined />}
              busy={reviewingOpen}
              busyLabel="Reviewing…"
              disabled={!running}
              onClick={() => void reviewOpen()}
            >
              Live review open
            </ActionButton>
            <ActionButton icon={<DoneAll />} primary busy={verifying} busyLabel="Verifying…" onClick={() => void verifyAll()}>
              Verify open signals
            </ActionButton>
          </>
        }
      />
      <KpiStrip
        tiles={[
          {
            label: "Hit rate",
            value: isNum(stats.hit_rate) ? `${String(Math.round(stats.hit_rate * 100))}%` : <Na reason="No decided signals yet" />,
            note: "Target before stop",
          },
          { label: "Wins / losses", value: `${String(stats.wins ?? 0)} / ${String(stats.losses ?? 0)}`, note: `${String(stats.expired ?? 0)} expired` },
          {
            label: "Open",
            value: String(stats.open ?? 0),
            note: running ? `Now ${fmtSigned(openPnl, 2) ?? ""} USDT` : "Neither level hit yet",
          },
          {
            label: "Paper result",
            value: <V value={signals?.some((s) => s.paper?.closed) ? `${fmtSigned(closedPnl, 2) ?? ""} USDT` : null} reason="No closed signals" />,
            note: settings ? `${usd(settings.margin) ?? ""} · ${String(settings.leverage)}x · ${settings.margin_mode}` : `${String(stats.total ?? 0)} archived`,
          },
        ]}
      />
      {priceError ? <Alert severity="info">Live prices unavailable, so running trades show their levels only: {priceError}</Alert> : null}
      <Card>
        <Tabs value={tab} onChange={(_e, v: Tab) => setTab(v)} variant="scrollable" allowScrollButtonsMobile sx={{ px: 1, borderBottom: 1, borderColor: "divider" }}>
          <Tab value="signals" label="Trades" />
          <Tab value="neutral" label="Neutral" />
          <Tab value="watch" label="On watch" />
          <Tab value="all" label="All" />
          <Tab value="analyses" label="Analysis log" />
        </Tabs>
        {tab === "signals" || tab === "neutral" ? table : null}
        {tab === "watch" ? <AnalysesTable kind="watch" active={active} onOpen={(id) => setOpen({ signal: null, analysisId: id })} /> : null}
        {tab === "all" ? <AllCalls active={active} signals={signals ?? []} onOpen={(signal, analysisId) => setOpen({ signal, analysisId })} /> : null}
        {tab === "analyses" ? <AnalysesTable active={active} onOpen={(id) => setOpen({ signal: null, analysisId: id })} /> : null}
      </Card>
      {open ? (
        <SignalDetailDialog
          signal={open.signal}
          analysisId={open.analysisId}
          onClose={() => setOpen(null)}
          onChanged={(s) => setSignals((list) => list?.map((x) => (x.id === s.id ? s : x)) ?? null)}
        />
      ) : null}
      {editing && settings ? <PaperSettingsDialog value={settings} onClose={() => setEditing(false)} onSaved={setSettings} /> : null}
    </Stack>
  );
}
