import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import AutoAwesome from "@mui/icons-material/AutoAwesome";
import BookmarkAddOutlined from "@mui/icons-material/BookmarkAddOutlined";
import ExpandMore from "@mui/icons-material/ExpandMore";
import { useEffect, useRef, useState } from "react";
import { api, type AnalysisPack, type ArenaAgent, type ChatMessage, type GuardMode, type Market, type OptimizeMode, type StrategyPackResult, type TradeLevels } from "../api";
import ChatPanel, { type UiMessage } from "../components/ChatPanel";
import { ConfluenceCard, CorrelationCard, FlowCard, LevelsBoard, LiquidityCard, SetupCard, StrategyFitCard } from "../components/DeskCards";
import DeepDiveCard from "../components/DeepDiveCard";
import ErrorBoundary from "../components/ErrorBoundary";
import FinancialsCard from "../components/FinancialsCard";
import { useFeedback } from "../components/feedback";
import PulseStrip from "../components/PulseStrip";
import TradingViewChart from "../components/TradingViewChart";
import { ActionButton, BiasPill, KpiStrip, Na, PageHeader, V, type KpiTile } from "../components/ui";
import { GLYPH, biasClass, currentPrice, fmtConf, fmtPct, fmtPx, fmtR, fmtSigned, humanize, isNum, rewardRisk } from "../lib/format";
import { TIMEFRAMES } from "../lib/nav";
import { readPref, writePref } from "../lib/storage";

const DEFAULT_AGENT = "chillar_g";
/** Think like Off: plain desk analysis, no Arena agent playbook. */
const THINK_OFF = "off";

const RUN_HINT = "Run a full analysis";
const GREETING =
  "Pick a pair with Ctrl K, then run a full analysis. I'll pull TradingView and Binance context, score it, and give you a plan with entry, stop and target. Ask follow-ups below.";

const DATA_SOURCE: Record<string, string> = { binance_local: "Binance (local TA)", tradingview: "TradingView TA" };

function deskKpis(levels: TradeLevels | null, market: Market | null): KpiTile[] {
  if (!levels || !market) {
    return [
      { label: "Bias", value: <Na reason={RUN_HINT} />, note: RUN_HINT },
      { label: "Confluence", value: <Na reason={RUN_HINT} />, note: "Score −10 to +10" },
      { label: "Setup", value: <Na reason={RUN_HINT} />, note: "Chop filter" },
      { label: "Entry", value: <Na reason={RUN_HINT} />, note: "Stop · Target" },
      { label: "Reward : risk", value: <Na reason={RUN_HINT} />, note: "Confidence" },
      { label: "Price", value: <Na reason={RUN_HINT} />, note: "24h change" },
    ];
  }
  const conf = market.confluence ?? {};
  const setup = market.setup ?? {};
  const rr = rewardRisk(levels.entry, levels.stop_loss, levels.take_profit);
  const cls = biasClass(levels.bias);
  const or = (v: string | null | undefined) => v ?? <Na />;
  return [
    { label: "Bias", tone: cls, value: `${GLYPH[cls]} ${levels.bias || "Neutral"}`, note: <>Trend {or(levels.trend)}</> },
    {
      label: "Confluence",
      tone: biasClass(conf.bias),
      value: <V value={fmtSigned(conf.score)} />,
      unit: "/ 10",
      note: <>Prefers {or(conf.bias)}</>,
    },
    {
      label: "Setup",
      tone: "text",
      value: setup.type ? humanize(setup.type) : <Na />,
      note: setup.trade_allowed === false ? "Blocked by chop filter" : "Trade allowed",
    },
    {
      label: "Entry",
      value: <V value={fmtPx(levels.entry)} />,
      note: (
        <>
          SL {or(fmtPx(levels.stop_loss))} · TP {or(fmtPx(levels.take_profit))}
        </>
      ),
    },
    {
      label: "Reward : risk",
      value: rr === null ? <Na reason="Needs entry, stop and target" /> : rr.toFixed(1),
      unit: rr === null ? undefined : ": 1",
      note: <>Confidence {or(fmtConf(levels.confidence))}</>,
    },
    {
      label: "Price",
      value: <V value={fmtPx(currentPrice(market))} />,
      note: <>24h {or(fmtPct(market.flow?.price_change_24h_pct ?? market.yahoo_price?.change_pct, 2))}</>,
    },
  ];
}

function subtitle(exchange: string, timeframe: string, market: Market | null): string {
  if (!market) return `${exchange} · ${timeframe} · run a full analysis to score this pair.`;
  const parts = [`${exchange} · ${timeframe}`];
  const conf = market.confluence;
  if (isNum(conf?.score)) parts.push(`confluence ${fmtSigned(conf.score) ?? ""} / 10`);
  if (market.setup?.type) {
    parts.push(`${humanize(market.setup.type)}${market.setup.trade_allowed === false ? " (no trade)" : ""}`);
  }
  return parts.join(" · ");
}

export default function Desk({
  symbol,
  exchange,
  tvSymbol,
  timeframe,
  pairPick,
  dark,
  active,
  onSignalRecorded,
  onJournalChanged,
  onTimeframe,
}: Readonly<{
  symbol: string;
  exchange: string;
  tvSymbol: string;
  timeframe: string;
  pairPick: number;
  dark: boolean;
  active: boolean;
  onSignalRecorded: () => void;
  onJournalChanged: () => void;
  onTimeframe: (tf: string) => void;
}>) {
  const { toast } = useFeedback();
  const [levels, setLevels] = useState<TradeLevels | null>(null);
  const [market, setMarket] = useState<Market | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([{ id: 0, role: "assistant", text: GREETING }]);
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [analysisId, setAnalysisId] = useState<number | null>(null);
  const [packs, setPacks] = useState<AnalysisPack[]>([]);
  const [strategyId, setStrategyId] = useState(() => readPref("cca_strategy") ?? "desk");
  const [optimizeMode, setOptimizeMode] = useState<OptimizeMode>(() => (readPref("cca_optimize") as OptimizeMode) || "local_score");
  const [guardMode, setGuardMode] = useState<GuardMode>(() => (readPref("cca_guard") as GuardMode) || "enforce");
  const [packResults, setPackResults] = useState<StrategyPackResult[] | null>(null);
  const [busy, setBusy] = useState(false);
  const nextId = useRef(1);
  const firstRender = useRef(true);
  const runOnTimeframe = useRef(false); // WL-112: a timeframe button was clicked; run once it is in

  const push = (m: Omit<UiMessage, "id">): number => {
    const id = nextId.current++;
    setMessages((list) => [...list, { ...m, id }]);
    return id;
  };
  const drop = (id: number) => setMessages((list) => list.filter((m) => m.id !== id));

  // A plan belongs to one pair and timeframe; clear it when either changes.
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    setLevels(null);
    setMarket(null);
    setPackResults(null);
    setHistory([]);
    setAnalysisId(null);
    push({ role: "assistant", text: `Switched to ${exchange}:${symbol} · ${timeframe}.`, quiet: true });
    if (runOnTimeframe.current) {
      runOnTimeframe.current = false;
      void analyzeRef.current();
    }
  }, [symbol, exchange, timeframe]);

  // WL-070: optional Arena agent to think like. Off = plain desk (no agent playbook).
  const [agents, setAgents] = useState<ArenaAgent[]>([]);
  const [agent, setAgent] = useState(() => {
    const saved = readPref("cca_agent");
    // Former default was chillar_g meaning "system / no override"; treat as Off.
    if (!saved || saved === DEFAULT_AGENT) return THINK_OFF;
    return saved;
  });
  useEffect(() => {
    api
      .agents()
      .then((r) => setAgents(r.agents ?? []))
      .catch(() => undefined);
  }, []);
  const agentName = agents.find((a) => a.id === agent)?.name;
  const thinkAs = agent !== THINK_OFF && agentName ? agent : null;
  const chooseAgent = (id: string) => {
    writePref("cca_agent", id);
    setAgent(id);
  };
  const thinkValue = agent === THINK_OFF || agents.some((a) => a.id === agent) ? agent : THINK_OFF;

  // WL-112, WL-131: every pick from the search asks the timeframe, also for the same pair, with the
  // Think like agents (top Arena scorer first, as /api/agents sorts them) in the same message.
  const askTimeframe = () =>
    push({
      role: "assistant",
      text: `Which timeframe should I analyse ${symbol} on?`,
      choices: [...TIMEFRAMES],
      current: timeframe,
      agents: [
        { id: THINK_OFF, name: "Off (no agent)", note: "Plain desk analysis" },
        ...agents.map((a) => ({
          id: a.id,
          name: a.id === DEFAULT_AGENT ? `${a.name} (current system)` : a.name,
          note: a.total_r === null || a.total_r === undefined ? "No Arena trades yet" : `${fmtR(a.total_r, 1) ?? ""} in the Arena`,
        })),
      ],
      agent: thinkValue,
    });
  const askRef = useRef(askTimeframe); // the effect below asks with the newest pair, timeframe and agents
  askRef.current = askTimeframe;
  useEffect(() => {
    if (pairPick) askRef.current();
  }, [pairPick]);

  useEffect(() => {
    api
      .packs()
      .then((r) => setPacks(r.packs.filter((p) => p.multi_analyze || p.id === "desk" || p.id === "simple_core")))
      .catch(() => setPacks([]));
  }, []);

  async function runAnalyze() {
    if (busy) return;
    setBusy(true);
    const all = strategyId === "all";
    const label = all ? "All strategies" : packs.find((p) => p.id === strategyId)?.label ?? strategyId;
    push({
      role: "user",
      text: `Full analysis for ${exchange}:${symbol} (${timeframe}) · ${label}${thinkAs ? `, thinking like ${agentName ?? ""}` : ""}`,
    });
    const pending = push({ role: "assistant", text: "Pulling market data and thinking…", thinking: true });
    try {
      const res = await api.analyze({
        symbol,
        exchange,
        timeframe,
        agent: thinkAs,
        strategy_id: strategyId,
        optimize_mode: all ? optimizeMode : undefined,
        guard_mode: guardMode,
      });
      drop(pending);
      setLevels(res.levels);
      setMarket(res.market);
      setAnalysisId(res.analysis_id ?? null);
      setPackResults(res.packs ?? null);
      const winner = res.strategy_label ? ` Winner: ${res.strategy_label}.` : "";
      push({ role: "assistant", text: `${res.analysis}${winner ? `\n\n${winner}` : ""}`, levels: res.levels, provider: res.provider });
      setHistory((h) => [
        ...h,
        { role: "user", content: `Full analysis for ${exchange}:${symbol}` },
        { role: "assistant", content: res.analysis },
      ]);
      if (res.provider === "offline") toast("No AI selected, so this is the deterministic plan only. Restart and pick one.");
      if (res.market.recorded_signal_id) {
        toast(all ? `Signal archived (${res.strategy_label ?? "winner"}). Open Signals for pack results.` : "Signal archived for later verification.");
        onSignalRecorded();
        if (all && res.market.recorded_signal_id) {
          // Deep-link hint; hash route handled on Signals page.
          writePref("cca_last_signal", String(res.market.recorded_signal_id));
        }
      }
    } catch (err) {
      drop(pending);
      push({ role: "assistant", text: `Error: ${(err as Error).message}`, error: true });
    } finally {
      setBusy(false);
    }
  }
  const analyzeRef = useRef(runAnalyze); // the effect above runs the newest one (WL-112)
  analyzeRef.current = runAnalyze;

  async function runChat(message: string) {
    if (busy) return;
    setBusy(true);
    push({ role: "user", text: message });
    const pending = push({ role: "assistant", text: "Thinking…", thinking: true });
    try {
      const res = await api.chat({ symbol, exchange, timeframe, message, history: history.slice(-8), agent: thinkAs, analysis_id: analysisId });
      drop(pending);
      push({ role: "assistant", text: res.reply, provider: res.provider });
      setHistory((h) => [...h, { role: "user", content: message }, { role: "assistant", content: res.reply }]);
    } catch (err) {
      drop(pending);
      push({ role: "assistant", text: `Error: ${(err as Error).message}`, error: true });
    } finally {
      setBusy(false);
    }
  }

  async function logToJournal() {
    if (!levels) return;
    const side = levels.bias === "Sell" ? "Sell" : "Buy";
    try {
      await api.addJournal({
        symbol,
        timeframe,
        side,
        setup: market?.setup?.type ?? null,
        entry: levels.entry,
        stop_loss: levels.stop_loss,
        take_profit: levels.take_profit,
        confluence: market?.confluence?.score ?? null,
        notes: levels.reasoning,
      });
      toast(`Logged ${symbol} ${side} to the journal.`);
      onJournalChanged();
    } catch (err) {
      toast(`Journal error: ${(err as Error).message}`);
    }
  }

  const source = market?.data_source ? (DATA_SOURCE[market.data_source] ?? market.data_source) : "";

  return (
    <Stack spacing={2}>
      <PageHeader
        title={symbol}
        subtitle={subtitle(exchange, timeframe, market)}
        actions={
          <>
            <TextField
              select
              size="small"
              label="Strategy"
              value={strategyId}
              onChange={(e) => {
                writePref("cca_strategy", e.target.value);
                setStrategyId(e.target.value);
              }}
              sx={{ minWidth: 160 }}
            >
              <MenuItem value="all">All strategies</MenuItem>
              {packs.map((p) => (
                <MenuItem key={p.id} value={p.id}>
                  {p.label}
                </MenuItem>
              ))}
            </TextField>
            {strategyId === "all" ? (
              <TextField
                select
                size="small"
                label="Optimization"
                value={optimizeMode}
                onChange={(e) => {
                  const v = e.target.value as OptimizeMode;
                  writePref("cca_optimize", v);
                  setOptimizeMode(v);
                }}
                sx={{ minWidth: 150 }}
              >
                <MenuItem value="local_score">Local score</MenuItem>
                <MenuItem value="majority_vote">Majority vote</MenuItem>
                <MenuItem value="ai_ensemble">AI ensemble</MenuItem>
              </TextField>
            ) : null}
            <TextField
              select
              size="small"
              label="Guards"
              value={guardMode}
              onChange={(e) => {
                const v = e.target.value as GuardMode;
                writePref("cca_guard", v);
                setGuardMode(v);
              }}
              sx={{ minWidth: 120 }}
            >
              <MenuItem value="enforce">On</MenuItem>
              <MenuItem value="ai_only">AI only</MenuItem>
            </TextField>
            {agents.length ? (
              <TextField
                select
                size="small"
                label="Think like"
                value={thinkValue}
                onChange={(e) => chooseAgent(e.target.value)}
                sx={{ minWidth: 180 }}
                helperText={thinkAs ? undefined : "Optional"}
              >
                <MenuItem value={THINK_OFF}>Off</MenuItem>
                {agents.map((a) => (
                  <MenuItem key={a.id} value={a.id}>
                    {a.name}
                    {a.id === DEFAULT_AGENT ? " (current system)" : ""}
                  </MenuItem>
                ))}
              </TextField>
            ) : null}
            <ActionButton icon={<BookmarkAddOutlined />} disabled={!levels} onClick={() => void logToJournal()}>
              Log to journal
            </ActionButton>
            <ActionButton icon={<AutoAwesome />} primary busy={busy} busyLabel="Analysing…" onClick={() => void runAnalyze()}>
              Full analysis
            </ActionButton>
          </>
        }
      />

      <PulseStrip active={active} />

      <KpiStrip tiles={deskKpis(levels, market)} />

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "minmax(0, 1fr)", lg: "minmax(0, 1fr) 380px" }, alignItems: "start" }}>
        <Stack spacing={2} sx={{ minWidth: 0 }}>
          <Card sx={{ minWidth: 0 }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", px: 2, minHeight: 48, borderBottom: 1, borderColor: "divider" }}>
              <Typography variant="h3" component="h3" noWrap sx={{ flex: 1, minWidth: 0, fontFamily: (t) => t.typography.fontFamilyMono }}>
                {tvSymbol}
              </Typography>
              {source ? (
                <Typography variant="caption" noWrap sx={{ color: "text.secondary" }}>
                  Data: {source}
                </Typography>
              ) : null}
            </Stack>
            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "minmax(0, 1fr)", md: "minmax(0, 1fr) 220px" } }}>
              <TradingViewChart tvSymbol={tvSymbol} timeframe={timeframe} dark={dark} />
              <Box sx={{ p: 1.5, borderLeft: { md: 1 }, borderTop: { xs: 1, md: 0 }, borderColor: "divider", minWidth: 0 }}>
                <LevelsBoard levels={levels} market={market} />
              </Box>
            </Box>
          </Card>
          <ErrorBoundary label="Market cards">
            <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "minmax(0, 1fr)", md: "repeat(2, minmax(0, 1fr))" } }}>
              <ConfluenceCard market={market} />
              <SetupCard market={market} />
              <FlowCard market={market} />
              <LiquidityCard market={market} />
            </Box>
          </ErrorBoundary>
          <ErrorBoundary label="Strategy fit">
            <StrategyFitCard market={market} />
          </ErrorBoundary>
          {packResults?.length ? (
            <ErrorBoundary label="Pack results">
              <Card sx={{ p: 2 }}>
                <Typography variant="h3" component="h3" sx={{ mb: 1 }}>
                  Pack results
                </Typography>
                <Stack spacing={0.5}>
                  {[...packResults]
                    .sort((a, b) => (b.pack_score ?? -999) - (a.pack_score ?? -999))
                    .map((p, i) => {
                      const winner = i === 0 && p.bias !== "Neutral";
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
                              {winner ? <Chip size="small" label="Top" color="primary" /> : null}
                              <BiasPill bias={p.bias} />
                              <Typography variant="caption" color="text.secondary">
                                score {p.pack_score ?? "—"} · fit {fmtSigned(p.fit_score) ?? "—"}
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
                                No pack reasoning stored.
                              </Typography>
                            )}
                          </AccordionDetails>
                        </Accordion>
                      );
                    })}
                </Stack>
              </Card>
            </ErrorBoundary>
          ) : null}
          <ErrorBoundary label="Correlation">
            <CorrelationCard market={market} />
          </ErrorBoundary>
          <ErrorBoundary label="Financials">
            <FinancialsCard symbol={symbol.replace(/.P$/, "")} active={active} />
          </ErrorBoundary>
          <ErrorBoundary label="Deep dive">
            <DeepDiveCard symbol={symbol.replace(/.P$/, "")} active={active} />
          </ErrorBoundary>
        </Stack>
        <ErrorBoundary label="Chat">
          <ChatPanel
            symbol={symbol}
            messages={messages}
            busy={busy}
            onSend={(t) => void runChat(t)}
            onChoose={(id, tf, kind) => {
              if (busy) return;
              if (kind === "agent") {
                chooseAgent(tf);
                setMessages((list) => list.map((m) => (m.id === id ? { ...m, agent: tf } : m)));
                return;
              }
              setMessages((list) => list.map((m) => (m.id === id ? { ...m, chosen: tf } : m)));
              if (tf === timeframe) void runAnalyze();
              else {
                runOnTimeframe.current = true;
                onTimeframe(tf);
              }
            }}
            onClear={() => {
              setHistory([]);
              setMessages([{ id: nextId.current++, role: "assistant", text: GREETING }]);
            }}
          />
        </ErrorBoundary>
      </Box>
    </Stack>
  );
}
