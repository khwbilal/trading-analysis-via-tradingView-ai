import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControlLabel from "@mui/material/FormControlLabel";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Tab from "@mui/material/Tab";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Tabs from "@mui/material/Tabs";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import Calculate from "@mui/icons-material/CalculateOutlined";
import Close from "@mui/icons-material/Close";
import History from "@mui/icons-material/History";
import Refresh from "@mui/icons-material/Refresh";
import StarOutline from "@mui/icons-material/StarBorderOutlined";
import { type ReactNode, useCallback, useEffect, useState } from "react";
import { api, type AgentPickStyle, type AgentPicksResponse, type Pick, type PickHistoryRow, type PicksDay, type PicksResponse, type Style } from "../api";
import { AGENT_PICK_STYLES, AgentPickTable, PicksNav, type PicksSection, WinnersDashboard } from "../components/AgentPicks";
import PositionDialog from "../components/PositionDialog";
import { useFeedback } from "../components/feedback";
import { type FilterColumn, useTableFilters } from "../components/TableFilters";
import { ActionButton, DataTable, EmptyState, Na, Num, PageHeader, Pill, StatusPill, V } from "../components/ui";
import { GLYPH, GROUP_LABEL, STYLE_LABEL, biasClass, fmtCompact, fmtFixed, fmtPx, fmtR, fmtRate, fmtSigned, fmtWhen, humanize } from "../lib/format";
import { useTaskData } from "../lib/useTask";
import { oneOf, readPref, usePref, writePref } from "../lib/storage";

const STYLES: Style[] = ["scalp", "day", "swing"];
const RISK: Record<string, string> = { // the picks have no position style (WL-079 added it for backtests)
  scalp: "Highest risk: 15m candles, 1 ATR stop, 1.5R target, closes within 8 hours.",
  day: "Medium risk: 1h candles, 1.5 ATR stop, 2R target, closes within a day.",
  swing: "Days to weeks: 4h candles, 2 ATR stop, 2.5R target, closes within 10 days.",
};

function Corr({ c, b }: Readonly<{ c: number | null | undefined; b: number | null | undefined }>) {
  if (c === null || c === undefined) return <Na reason="Too little overlapping history" />;
  return (
    <Tooltip title={`Correlation ${fmtFixed(c, 2) ?? ""}, beta ${fmtFixed(b, 2) ?? "unknown"}`}>
      <span>
        <Num>{fmtFixed(c, 2)}</Num>
      </span>
    </Tooltip>
  );
}

const NOT_TRADED = "No paper trade: only the crypto Top 10 lists are paper traded";

/** How the paper trade opened from this pick did (WL-059). */
function Result({ status, r, closed }: Readonly<{ status?: string | null; r?: number | null; closed?: string | null }>) {
  if (!status) return <Na reason={NOT_TRADED} />;
  return (
    <Stack direction="row" spacing={0.5} sx={{ alignItems: "center", justifyContent: "flex-end" }}>
      <StatusPill status={status} title={closed ? `Closed ${fmtWhen(closed) ?? ""}` : "Still open"} />
      {r === null || r === undefined ? null : <Num>{fmtR(r)}</Num>}
    </Stack>
  );
}

function dayLabel(d: PicksDay): string {
  if (!d.traded) return `${d.day} · not paper traded`;
  const parts = [`${String(d.won ?? 0)} won`, `${String(d.lost ?? 0)} lost`];
  if (d.expired) parts.push(`${String(d.expired)} expired`);
  if (d.open) parts.push(`${String(d.open)} open`);
  const r = fmtR(d.total_r);
  return `${d.day} · ${parts.join(", ")}${r ? ` · ${r}` : ""}`;
}

/** Every day one symbol was picked, with its paper result (WL-059). */
function HistoryDialog({ symbol, onClose }: Readonly<{ symbol: string; onClose: () => void }>) {
  const phone = useMediaQuery((t) => t.breakpoints.down("sm"));
  const [rows, setRows] = useState<PickHistoryRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.pickHistory(symbol).then(
      (r) => setRows(r.rows),
      (err: unknown) => setError((err as Error).message),
    );
  }, [symbol]);
  return (
    <Dialog open onClose={onClose} fullScreen={phone} fullWidth maxWidth="md" aria-labelledby="pickHistTitle">
      <DialogTitle id="pickHistTitle" sx={{ display: "flex", alignItems: "center", gap: 1, pr: 1 }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          {symbol} pick history
          <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
            Every day it made a stored list, newest first, with the paper result
          </Typography>
        </Box>
        <IconButton aria-label="Close" onClick={onClose}>
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ p: 0 }}>
        {error ? <Alert severity="warning">History unavailable: {error}</Alert> : null}
        {!rows && !error ? <Skeleton height={120} sx={{ mx: 2 }} /> : null}
        {rows && !rows.length ? <EmptyState icon={<History />} text="No stored picks for this symbol." /> : null}
        {rows?.length ? (
          <DataTable minWidth={720}>
            <TableHead>
              <TableRow>
                <TableCell>Day</TableCell>
                <TableCell>Style</TableCell>
                <TableCell align="right">Rank</TableCell>
                <TableCell>Side</TableCell>
                <TableCell align="right">Entry</TableCell>
                <TableCell align="right">Stop</TableCell>
                <TableCell align="right">Target</TableCell>
                <TableCell align="right">Score</TableCell>
                <TableCell align="right">Result</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((h) => {
                const cls = biasClass(h.side);
                return (
                  <TableRow key={`${h.day}-${h.style}`} hover>
                    <TableCell>
                      <Num>{h.day}</Num>
                    </TableCell>
                    <TableCell>{STYLE_LABEL[h.style]}</TableCell>
                    <TableCell align="right">
                      <Num>{h.rank}</Num>
                    </TableCell>
                    <TableCell>
                      <Pill glyph={GLYPH[cls]} label={h.side} tone={cls === "buy" ? "buy" : "sell"} />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtPx(h.entry)} />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtPx(h.stop)} />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtPx(h.target)} />
                    </TableCell>
                    <TableCell align="right">
                      <Num>{fmtSigned(h.score)}</Num>
                    </TableCell>
                    <TableCell align="right">
                      <Result status={h.paper_status} r={h.paper_r} closed={h.paper_closed_at} />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </DataTable>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}

/** A value or header that explains itself on hover or focus (WL-060). */
function Tip({ title, children }: Readonly<{ title: ReactNode; children: ReactNode }>) {
  return (
    <Tooltip title={title}>
      <Box component="span" tabIndex={0} sx={{ cursor: "help", textDecoration: "underline dotted", textDecorationColor: (t) => t.palette.text.disabled, textUnderlineOffset: 3 }}>
        {children}
      </Box>
    </Tooltip>
  );
}

const HEAD: Record<string, string> = {
  Entry: "Last close when the list was built. The paper trade enters at the live price instead.",
  Stop: "Entry minus (or plus, for a sell) 1, 1.5 or 2 ATR for scalp, day and swing.",
  Target: "1.5R, 2R or 2.5R from the entry, where R is the distance to the stop.",
  "R:R": "Reward to risk: target distance divided by stop distance. 2.0 means a win pays twice what a loss costs.",
  Score:
    "-10 to +10 from trend, momentum, ADX strength, volume and a back-tested strategy firing. The sign is the side, the size the confluence. Hover a score for its parts.",
  Setup: "The chart pattern on the last closed candle, from the setup classifier.",
  "Best strategy": "The back-tested strategy that best fits this setup and style, with its win rate over all stored backtest runs. ● means it fired on the last candles.",
  "Corr BTC": "Correlation of returns with BTC over recent candles, -1 to +1. Near 1 it moves with BTC; beta (on hover) is how far, 1.5 being 50% more.",
  "Corr ETH": "Correlation of returns with ETH, -1 to +1, and beta on hover.",
  "24h volume": "Quote volume traded on Binance in the last 24 hours, in USD.",
  Result: "How the paper trade opened from this pick did: win, loss, expired or open, with its R. Only the crypto Top 10 lists are paper traded.",
};

function Head({ label, align }: Readonly<{ label: string; align?: "right" }>) {
  return <TableCell align={align}>{HEAD[label] ? <Tip title={HEAD[label]}>{label}</Tip> : label}</TableCell>;
}

const PART_LABEL: Record<string, string> = {
  trend: "Trend (EMA 20, 50, 200)",
  momentum: "Momentum (RSI)",
  strength: "Strength (ADX)",
  volume: "Volume above average",
  strategy: "Strategy firing",
};

function ScoreTip({ p }: Readonly<{ p: Pick }>) {
  const d = p.details;
  const parts = Object.entries(d?.parts ?? {});
  if (!parts.length) return <>No breakdown stored for this pick.</>;
  return (
    <Box component="span" sx={{ display: "block" }}>
      {parts.map(([k, v]) => (
        <Box component="span" key={k} sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
          <span>{PART_LABEL[k] ?? humanize(k)}</span>
          <span>{fmtSigned(v, 0)}</span>
        </Box>
      ))}
      <Box component="span" sx={{ display: "block", mt: 0.5 }}>
        Sum scaled by 10/11 = {fmtSigned(p.score)}
        {d?.rsi !== undefined ? ` · RSI ${fmtFixed(d.rsi, 1) ?? ""}` : ""}
        {d?.adx !== undefined ? ` · ADX ${fmtFixed(d.adx, 1) ?? ""}` : ""}
      </Box>
    </Box>
  );
}

function rrTip(p: Pick): string {
  const risk = Math.abs(p.entry - p.stop);
  const reward = Math.abs(p.target - p.entry);
  const pct = (v: number) => `${fmtFixed((v / p.entry) * 100, 2) ?? ""}%`;
  return `Risk ${fmtPx(risk) ?? ""} (${pct(risk)}) to the stop, reward ${fmtPx(reward) ?? ""} (${pct(reward)}) to the target.`;
}

function PickRow({
  p,
  n,
  onOpen,
  onHistory,
  onPosition,
}: Readonly<{ p: Pick; n: number; onOpen: (p: Pick) => void; onHistory: (symbol: string) => void; onPosition: (p: Pick) => void }>) {
  const cls = biasClass(p.side);
  return (
    <TableRow hover>
      <TableCell>
        <Num>{n}</Num>
      </TableCell>
      <TableCell>
        <Tooltip title={`Open ${p.symbol} on the desk`}>
          <Typography
            component="button"
            onClick={() => onOpen(p)}
            sx={{ all: "unset", cursor: "pointer", fontWeight: 700, fontFamily: (t) => t.typography.fontFamilyMono, "&:hover": { color: "primary.main" }, "&:focus-visible": { outline: 2, outlineColor: "primary.main" } }}
          >
            {p.symbol}
          </Typography>
        </Tooltip>
        <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
          {GROUP_LABEL[p.coin_group] ?? p.coin_group}
          {p.market === "usdm" ? " · perp" : ""}
        </Typography>
      </TableCell>
      <TableCell>
        <Pill glyph={GLYPH[cls]} label={p.side} tone={cls === "buy" ? "buy" : "sell"} />
      </TableCell>
      <TableCell align="right">
        <V value={fmtPx(p.entry)} />
      </TableCell>
      <TableCell align="right">
        <V value={fmtPx(p.stop)} />
      </TableCell>
      <TableCell align="right">
        <V value={fmtPx(p.target)} />
      </TableCell>
      <TableCell align="right">
        <Tip title={rrTip(p)}>
          <Num>{fmtFixed(p.rr, 1)}</Num>
        </Tip>
      </TableCell>
      <TableCell align="right">
        <Tip title={<ScoreTip p={p} />}>
          <Num sx={{ fontWeight: 700 }}>{fmtSigned(p.score)}</Num>
        </Tip>
      </TableCell>
      <TableCell>{p.setup ? humanize(p.setup) : <Na />}</TableCell>
      <TableCell sx={{ whiteSpace: "normal", minWidth: 180 }}>
        {p.strategy_name ? (
          <>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {p.strategy_firing ? "● " : ""}
              {p.strategy_name}
            </Typography>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              {p.strategy_firing ? "Fired on the last candles · " : "Fits the setup · "}
              {p.strategy_win_rate === null || p.strategy_win_rate === undefined ? (
                <>
                  win rate <Na reason="too few trades" />
                </>
              ) : (
                <>
                  {fmtRate(p.strategy_win_rate)} wins over {p.strategy_trades} trades
                </>
              )}
            </Typography>
          </>
        ) : (
          <Na reason="No strategy fits" />
        )}
      </TableCell>
      <TableCell align="right">
        <Corr c={p.corr_btc} b={p.beta_btc} />
      </TableCell>
      <TableCell align="right">
        <Corr c={p.corr_eth} b={p.beta_eth} />
      </TableCell>
      <TableCell align="right">
        <V value={fmtCompact(p.volume_usd, "$")} />
      </TableCell>
      <TableCell align="right">
        <Result status={p.paper?.status} r={p.paper?.r_multiple} closed={p.paper?.closed_at} />
      </TableCell>
      <TableCell padding="none" sx={{ whiteSpace: "nowrap", pr: 1 }}>
        <Tooltip title="Try a position: leverage, size, liquidation and profit or loss">
          <IconButton size="small" aria-label={`Try a position on ${p.symbol}`} onClick={() => onPosition(p)}>
            <Calculate fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={`Every day ${p.symbol} was picked`}>
          <IconButton size="small" aria-label={`${p.symbol} pick history`} onClick={() => onHistory(p.symbol)}>
            <History fontSize="small" />
          </IconButton>
        </Tooltip>
      </TableCell>
    </TableRow>
  );
}

/** WL-127: a filter for every column of the house list. */
const HOUSE_FILTERS: FilterColumn<Pick>[] = [
  { key: "rank", label: "#", kind: "range", get: (p) => p.rank },
  { key: "pair", label: "Pair", kind: "text", get: (p) => p.symbol },
  { key: "group", label: "Group", kind: "choice", get: (p) => p.coin_group, labelOf: (v) => GROUP_LABEL[v] ?? v },
  { key: "market", label: "Market", kind: "choice", get: (p) => (p.market === "usdm" ? "Perp" : "Spot") },
  { key: "side", label: "Side", kind: "choice", get: (p) => p.side },
  { key: "entry", label: "Entry", kind: "range", get: (p) => p.entry },
  { key: "stop", label: "Stop", kind: "range", get: (p) => p.stop },
  { key: "target", label: "Target", kind: "range", get: (p) => p.target },
  { key: "rr", label: "R:R", kind: "range", get: (p) => p.rr },
  { key: "score", label: "Score", kind: "range", get: (p) => p.score },
  { key: "setup", label: "Setup", kind: "choice", get: (p) => p.setup, labelOf: humanize },
  { key: "strategy", label: "Best strategy", kind: "choice", get: (p) => p.strategy_name },
  { key: "firing", label: "Strategy fired", kind: "choice", get: (p) => (p.strategy_name ? (p.strategy_firing ? "Fired" : "Fits the setup") : null) },
  { key: "win", label: "Strategy win rate %", kind: "range", get: (p) => p.strategy_win_rate },
  { key: "corr_btc", label: "Corr BTC", kind: "range", get: (p) => p.corr_btc },
  { key: "corr_eth", label: "Corr ETH", kind: "range", get: (p) => p.corr_eth },
  { key: "volume", label: "24h volume ($M)", kind: "range", get: (p) => (p.volume_usd === null || p.volume_usd === undefined ? null : p.volume_usd / 1e6) },
  { key: "result", label: "Result", kind: "choice", get: (p) => p.paper?.status ?? "Not traded" },
];
const houseText = (p: Pick) => `${p.symbol} ${GROUP_LABEL[p.coin_group] ?? p.coin_group} ${p.side} ${humanize(p.setup)} ${p.strategy_name ?? ""}`;
const NO_PICKS: Pick[] = [];

/** WL-128: #/picks alone opens the section used last. */
function sectionFromHash(): PicksSection {
  const part = window.location.hash.replace(/^#\/?/, "").split("/").slice(1).join("/") || (readPref("cca_picks_section") ?? "");
  return part === "dashboard" || part === "house" || part.startsWith("agent:") ? (part as PicksSection) : "dashboard";
}

/** The house list: daily Top 10 per trading style (WL-037), with stocks, ETFs and commodities as an option (WL-041, WL-097). */
function HouseList({
  data,
  error,
  style,
  setStyle,
  stocks,
  setStocks,
  day,
  setDay,
  onOpen,
}: Readonly<{
  data: PicksResponse | null;
  error: string | null;
  style: Style;
  setStyle: (s: Style) => void;
  stocks: boolean;
  setStocks: (v: boolean) => void;
  day: string | null;
  setDay: (d: string | null) => void;
  onOpen: (p: Pick) => void;
}>) {
  const [history, setHistory] = useState<string | null>(null);
  const [position, setPosition] = useState<Pick | null>(null);
  const rows = data?.styles[style] ?? NO_PICKS;
  const { shown, bar } = useTableFilters("cca_picks_filters", rows, HOUSE_FILTERS, houseText, "picks");
  return (
    <>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ alignItems: { sm: "center" }, justifyContent: "space-between" }}>
        <Tabs value={style} onChange={(_e, v: Style) => setStyle(v)} variant="scrollable" allowScrollButtonsMobile aria-label="Trading style">
          {STYLES.map((s) => (
            <Tab key={s} value={s} label={STYLE_LABEL[s]} sx={{ minHeight: 48 }} />
          ))}
        </Tabs>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ alignItems: { sm: "center" } }}>
          <TextField
            select
            size="small"
            label="Day"
            value={day ?? data?.days?.[0]?.day ?? ""}
            onChange={(e) => setDay(e.target.value === data?.days?.[0]?.day ? null : e.target.value)}
            disabled={!data?.days?.length}
            sx={{ minWidth: 260 }}
          >
            {(data?.days ?? []).map((d) => (
              <MenuItem key={d.day} value={d.day}>
                {dayLabel(d)}
              </MenuItem>
            ))}
          </TextField>
          <FormControlLabel control={<Switch checked={stocks} onChange={(e) => setStocks(e.target.checked)} />} label="Include stocks, ETFs and commodities" />
        </Stack>
      </Stack>
      <Typography variant="body2" sx={{ color: "text.secondary" }}>
        {RISK[style]}
      </Typography>
      {error ? <Alert severity="warning">Picks unavailable: {error}</Alert> : null}
      <Card>
        {!data && !error ? <Skeleton height={160} sx={{ mx: 2 }} /> : null}
        {data && !rows.length ? (
          <EmptyState icon={<StarOutline />} text={data.day ? "No pick passed the score floor for this style." : "No picks yet. Select Rebuild picks."} />
        ) : null}
        {rows.length ? <Box sx={{ p: 2, pb: 1 }}>{bar}</Box> : null}
        {rows.length && !shown.length ? <EmptyState icon={<StarOutline />} text="No pick matches the search and filters." /> : null}
        {shown.length ? (
          <DataTable minWidth={1320}>
            <TableHead>
              <TableRow>
                <TableCell>#</TableCell>
                <TableCell>Pair</TableCell>
                <TableCell>Side</TableCell>
                {["Entry", "Stop", "Target", "R:R", "Score"].map((h) => (
                  <Head key={h} label={h} align="right" />
                ))}
                <Head label="Setup" />
                <Head label="Best strategy" />
                {["Corr BTC", "Corr ETH", "24h volume", "Result"].map((h) => (
                  <Head key={h} label={h} align="right" />
                ))}
                <TableCell padding="none" aria-label="Actions" />
              </TableRow>
            </TableHead>
            <TableBody>
              {shown.map((p) => (
                <PickRow key={p.symbol} p={p} n={rows.indexOf(p) + 1} onOpen={onOpen} onHistory={setHistory} onPosition={setPosition} />
              ))}
            </TableBody>
          </DataTable>
        ) : null}
      </Card>
      {history ? <HistoryDialog symbol={history} onClose={() => setHistory(null)} /> : null}
      {position ? <PositionDialog pick={position} onClose={() => setPosition(null)} /> : null}
    </>
  );
}

/** Top 10 picks (WL-037, WL-128): a section sidebar with the Arena winners' dashboard, the house list and every agent's own list. */
export default function Picks({
  active,
  onOpenPair,
}: Readonly<{ active: boolean; onOpenPair: (symbol: string, exchange: string, tv: string) => void }>) {
  const { toast } = useFeedback();
  const wide = useMediaQuery((t) => t.breakpoints.up("md"));
  const [section, setSection] = useState<PicksSection>(sectionFromHash);
  const [style, setStyle] = usePref<Style>("cca_picks_style", "day"); // WL-101: kept per browser
  const [agentStyle, setAgentStyle] = usePref<AgentPickStyle>("cca_picks_agent_style", "swing", oneOf(...AGENT_PICK_STYLES));
  const [stocks, setStocks] = usePref("cca_picks_stocks", false);
  const [day, setDay] = usePref<string | null>("cca_picks_day", null, (v) => v === null || typeof v === "string"); // null: the newest day
  const load = useCallback(() => api.picks(stocks, day), [stocks, day]);
  const taskOf = useCallback((d: PicksResponse) => d.task, []);
  const { data, error, refresh } = useTaskData(load, taskOf, active);
  const running = Boolean(data?.task.running);
  const [agentData, setAgentData] = useState<AgentPicksResponse | null>(null);
  const [agentError, setAgentError] = useState<string | null>(null);
  const built = data?.generated_at ?? null;

  useEffect(() => {
    const onHash = () => setSection(sectionFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  // The agent lists are built with the house list, so they reload when a new build lands.
  useEffect(() => {
    if (!active) return;
    let live = true;
    api.agentPicks(day).then(
      (r) => {
        if (!live) return;
        setAgentData(r);
        setAgentError(null);
      },
      (err: unknown) => live && setAgentError((err as Error).message),
    );
    return () => {
      live = false;
    };
  }, [active, day, built]);

  const go = (s: PicksSection) => {
    writePref("cca_picks_section", s);
    window.location.hash = `#/picks/${s}`;
  };

  async function rebuild() {
    try {
      await api.runPicks();
      toast("Scanning the Binance universe for today's picks and every agent's list, a few minutes.");
      await refresh();
    } catch (err) {
      toast(`Picks: ${(err as Error).message}`);
    }
  }

  const openSymbol = (symbol: string, market: string) => {
    const tv = market === "usdm" ? `BINANCE:${symbol}.P` : `BINANCE:${symbol}`;
    onOpenPair(market === "usdm" ? `${symbol}.P` : symbol, "BINANCE", tv);
  };
  const agent = section.startsWith("agent:") ? agentData?.agents.find((a) => `agent:${a.id}` === section) : undefined;
  const title = section === "dashboard" ? "Dashboard" : section === "house" ? "House Top 10" : (agent?.name ?? "Agent");
  const houseCount = data ? (data.styles[style]?.length ?? 0) : null;

  const agentStyleTabs = (
    <Tabs value={agentStyle} onChange={(_e, v: AgentPickStyle) => setAgentStyle(v)} variant="scrollable" allowScrollButtonsMobile aria-label="Trading style">
      {AGENT_PICK_STYLES.map((s) => (
        <Tab key={s} value={s} label={s === "position" ? "Position and hold (1D)" : STYLE_LABEL[s]} sx={{ minHeight: 48 }} />
      ))}
    </Tabs>
  );

  let body: ReactNode;
  if (section === "house") {
    body = (
      <HouseList
        data={data}
        error={error}
        style={style}
        setStyle={setStyle}
        stocks={stocks}
        setStocks={setStocks}
        day={day}
        setDay={setDay}
        onOpen={(p) => openSymbol(p.symbol, p.market)}
      />
    );
  } else if (!agentData) {
    body = agentError ? <Alert severity="warning">Agent picks unavailable: {agentError}</Alert> : <Skeleton height={200} />;
  } else if (!agentData.day) {
    body = (
      <Card>
        <EmptyState icon={<StarOutline />} text="No agent lists yet. Select Rebuild picks: the next build makes every agent's Top 10 too." />
      </Card>
    );
  } else if (section === "dashboard") {
    body = (
      <>
        {agentStyleTabs}
        <WinnersDashboard data={agentData} style={agentStyle} onAgent={(id) => go(`agent:${id}`)} onOpen={openSymbol} />
      </>
    );
  } else if (agent) {
    body = (
      <>
        {agentStyleTabs}
        <AgentPickTable agent={agent} style={agentStyle} onOpen={openSymbol} />
      </>
    );
  } else {
    body = <Alert severity="info">This agent is not in the Arena any more.</Alert>;
  }

  return (
    <Stack direction="row" spacing={3} sx={{ alignItems: "flex-start" }}>
      {wide ? <PicksNav section={section} onSection={go} data={agentData} style={agentStyle} houseCount={houseCount} /> : null}
      <Stack spacing={2} sx={{ flex: 1, minWidth: 0 }}>
        <PageHeader
          title={`Top 10 picks · ${title}`}
          subtitle={
            data?.day
              ? `Picks for ${data.day}, built ${fmtWhen(data.generated_at ?? undefined) ?? "at an unknown time"}. Deterministic, no AI. At most ${String(data.lowcap_max ?? 3)} low caps per list. The agent lists use each Arena agent's own rules on the newest closed candles.`
              : "Built daily at 16:00 PKT from the liquid Binance universe. Deterministic, no AI."
          }
          actions={
            <ActionButton icon={<Refresh />} primary busy={running} busyLabel="Scanning…" onClick={() => void rebuild()}>
              Rebuild picks
            </ActionButton>
          }
        />
        {data?.task.error ? <Alert severity="warning">Last build failed: {data.task.error}</Alert> : null}
        {wide ? null : (
          <TextField select size="small" label="Section" value={section} onChange={(e) => go(e.target.value as PicksSection)}>
            <MenuItem value="dashboard">Dashboard</MenuItem>
            <MenuItem value="house">House Top 10</MenuItem>
            {(agentData?.agents ?? []).map((a) => (
              <MenuItem key={a.id} value={`agent:${a.id}`}>
                {a.name}
              </MenuItem>
            ))}
          </TextField>
        )}
        {body}
      </Stack>
    </Stack>
  );
}
