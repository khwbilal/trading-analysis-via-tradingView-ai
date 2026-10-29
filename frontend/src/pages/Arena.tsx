import Alert from "@mui/material/Alert";
import Autocomplete from "@mui/material/Autocomplete";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import FormControlLabel from "@mui/material/FormControlLabel";
import IconButton from "@mui/material/IconButton";
import LinearProgress from "@mui/material/LinearProgress";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import MenuItem from "@mui/material/MenuItem";
import Radio from "@mui/material/Radio";
import RadioGroup from "@mui/material/RadioGroup";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Tab from "@mui/material/Tab";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Tabs from "@mui/material/Tabs";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import AccountTreeOutlined from "@mui/icons-material/AccountTreeOutlined";
import CalendarViewMonthOutlined from "@mui/icons-material/CalendarViewMonthOutlined";
import EmojiEventsOutlined from "@mui/icons-material/EmojiEventsOutlined";
import InsightsOutlined from "@mui/icons-material/InsightsOutlined";
import KeyboardArrowDown from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowRight from "@mui/icons-material/KeyboardArrowRight";
import PlayArrow from "@mui/icons-material/PlayArrow";
import SchoolOutlined from "@mui/icons-material/SchoolOutlined";
import Search from "@mui/icons-material/Search";
import { Fragment, useCallback, useEffect, useRef, useState, type ReactElement } from "react";
import {
  api,
  type ArenaAgent,
  type ArenaCharts,
  type ArenaFigures,
  type ArenaSized,
  type ArenaStanding,
  type ArenaFilters,
  type ArenaOverview,
  type ArenaReview,
  type ArenaStyle,
  type ArenaTrade,
} from "../api";
import AgentMap from "../components/AgentMap";
import { ChartSkeleton, CompareChart, RValue, StancePill, StandingsChart, StyleGrid, type ChartHover } from "../components/ArenaCharts";
import { LessonsCard, ProReportsCard } from "../components/ArenaExtras";
import { RunProgress } from "../components/RunStatus";
import { useFeedback } from "../components/feedback";
import { ActionButton, DataTable, EmptyState, KpiStrip, Na, Num, PageHeader, Pill, SectionCard, SortCell, V, monoSx, sortRows, useSort } from "../components/ui";
import { GLYPH, GROUP_LABEL, STYLE_LABEL, biasClass, fmtFixed, fmtPx, fmtR, fmtRate, fmtWhen } from "../lib/format";
import { oneOf, readPref, usePref, writePref } from "../lib/storage";
import { TOPBAR_HEIGHT } from "../theme";

const STYLES: ArenaStyle[] = ["all", "scalp", "day", "swing", "position", "hold"];
/** WL-100: compact (the default, one screen) or expanded (bigger charts and rows). */
type Layout = "compact" | "expanded";
const PAGE = 50;
const EXIT_LABEL: Record<ArenaTrade["exit_reason"], string> = {
  target: "Target",
  stop: "Stop",
  trail: "Trailing exit",
  expired: "Horizon",
  ladder: "Partials, then stop",
  signal: "Exit signal",
  liquidated: "Liquidated (wick)",
};

/** WL-093: the Arena's own sections, kept in the hash as #/arena/<section>. */
type Section = "standings" | "graphs" | "map" | "trades" | "days" | "learning";
const SECTIONS: { key: Section; label: string; icon: ReactElement; note: string }[] = [
  { key: "standings", label: "Standings", icon: <EmojiEventsOutlined />, note: "Places, points and groups" },
  { key: "graphs", label: "Graphs", icon: <InsightsOutlined />, note: "Compare agents over time" },
  { key: "map", label: "Agent map", icon: <AccountTreeOutlined />, note: "Agents and their strategies" },
  { key: "trades", label: "Trades", icon: <Search />, note: "Search every trade" },
  { key: "days", label: "Day by day", icon: <CalendarViewMonthOutlined />, note: "Each day's winner" },
  { key: "learning", label: "Lessons and reports", icon: <SchoolOutlined />, note: "What the agents learned" },
];

/** WL-101: #/arena alone opens the section used last. */
function sectionFromHash(): Section {
  const part = window.location.hash.replace(/^#\/?/, "").split("/")[1] || (readPref("cca_arena_section") ?? "");
  return SECTIONS.some((s) => s.key === part) ? (part as Section) : "standings";
}

/** The figure cells shared by an agent's main row and its bucket rows. */
function FigureCells({ f }: Readonly<{ f: ArenaFigures }>) {
  return (
    <>
      <TableCell align="right">
        <Num sx={{ fontWeight: 700 }}>{f.points}</Num>
      </TableCell>
      <TableCell align="right">
        <Num>{f.days_won}</Num>
      </TableCell>
      <TableCell align="right">
        <Num>{f.days_traded}</Num>
      </TableCell>
      <TableCell align="right">
        <Num>{f.trades}</Num>
      </TableCell>
      <TableCell align="right">
        <V value={fmtRate(f.win_rate)} reason="No trades" />
      </TableCell>
      <TableCell align="right">
        <RValue r={f.total_r} />
      </TableCell>
      <TableCell align="right">
        <RValue r={f.avg_r} digits={3} />
      </TableCell>
      <TableCell align="right">
        <V value={fmtFixed(f.profit_factor, 2)} reason={f.trades ? "No losing trades" : "No trades"} />
      </TableCell>
    </>
  );
}

/** WL-144: the figure columns, in FigureCells order, for the sortable header. */
const FIGURE_COLUMNS: [keyof ArenaFigures, string][] = [
  ["points", "Points"],
  ["days_won", "Days won"],
  ["days_traded", "Days traded"],
  ["trades", "Trades"],
  ["win_rate", "Win rate"],
  ["total_r", "Total R"],
  ["avg_r", "Avg R"],
  ["profit_factor", "Profit factor"],
];

function figureValue(f: ArenaFigures, key: string): number | null | undefined {
  return FIGURE_COLUMNS.some(([id]) => id === key) ? f[key as keyof ArenaFigures] : null;
}

/** WL-148: the USDT result at 50 USDT margin and one leverage, with the liquidations under it. */
function SizedCell({ s }: Readonly<{ s: ArenaSized | undefined }>) {
  if (!s?.trades) return <Na reason="No trades at this size" />;
  const pnl = s.pnl_usdt ?? 0;
  return (
    <Stack sx={{ alignItems: "flex-end" }}>
      <Num sx={{ color: pnl > 0 ? "success.main" : pnl < 0 ? "error.main" : "text.secondary", fontWeight: 600 }}>
        {pnl > 0 ? "▲ " : pnl < 0 ? "▼ " : ""}
        {fmtFixed(pnl, 2)} USDT
      </Num>
      <Typography variant="caption" sx={{ color: "text.secondary" }}>
        {s.liquidated.toLocaleString()} liquidated
      </Typography>
    </Stack>
  );
}

const SIZED_COLUMNS: [string, number, string][] = [
  ["usdt_10", 10, "50 USDT at 10x"],
  ["usdt_20", 20, "50 USDT at 20x"],
];

function standingValue(r: ArenaStanding, key: string): string | number | null | undefined {
  const sized = SIZED_COLUMNS.find(([id]) => id === key);
  if (sized) return r.sized?.find((s) => s.leverage === sized[1])?.pnl_usdt;
  if (key === "place") return r.place || null;
  if (key === "name") return r.name;
  if (key === "stance") return r.stance;
  return figureValue(r, key);
}

/** Table-shaped placeholders while new figures load (WL-092). */
function TableSkeleton({ rows = 8 }: Readonly<{ rows?: number }>) {
  return (
    <Stack spacing={1} sx={{ p: 2 }} aria-busy="true" aria-label="Loading">
      <Skeleton variant="rounded" height={28} />
      {Array.from({ length: rows }, (_v, i) => (
        <Skeleton key={i} variant="rounded" height={36} sx={{ opacity: 1 - i * 0.08 }} />
      ))}
    </Stack>
  );
}

/** How the chosen agent trades and what its review says (WL-078). */
function AgentCard({ agent, review, onClose }: Readonly<{ agent: ArenaAgent; review: ArenaReview | null; onClose: () => void }>) {
  const [sortBy, onSort] = useSort("cca_arena_sort_failures");
  const tagSort = { sort: sortBy, onSort };
  return (
    <SectionCard
      title={`${agent.name}: how it trades`}
      right={
        <>
          <StancePill a={agent} />
          <ActionButton compact onClick={onClose}>
            Close
          </ActionButton>
        </>
      }
    >
      <Typography variant="body2" sx={{ mb: 1 }}>
        {agent.summary}
      </Typography>
      <Box component="ul" sx={{ m: 0, pl: 2.5, color: "text.secondary" }}>
        {agent.rules.map((rule) => (
          <Typography component="li" variant="body2" key={rule}>
            {rule}
          </Typography>
        ))}
      </Box>
      {review === null ? <Skeleton variant="rounded" height={80} sx={{ mt: 2 }} /> : null}
      {review?.trades ? (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 700, mb: 0.5 }}>
            Review: {review.trades.toLocaleString()} trades, {fmtRate(review.win_rate) ?? ""} won, <RValue r={review.total_r} /> in all
          </Typography>
          <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
            {review.suggestions.map((tip) => (
              <Typography component="li" variant="body2" key={tip}>
                {tip}
              </Typography>
            ))}
          </Box>
          {review.slices.failure_tag?.length ? (
            <DataTable minWidth={420} maxHeight={240}>
              <TableHead>
                <TableRow>
                  <SortCell id="key" first="asc" {...tagSort}>
                    Why the losers lost
                  </SortCell>
                  <SortCell id="losses" align="right" {...tagSort}>
                    Losses
                  </SortCell>
                  <SortCell id="lost_r" align="right" first="asc" {...tagSort}>
                    Lost
                  </SortCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortRows(review.slices.failure_tag, sortBy, (f, k) => (k === "key" ? f.key : k === "losses" ? f.losses : f.lost_r)).map((f) => (
                  <TableRow key={f.key}>
                    <TableCell>{f.key}</TableCell>
                    <TableCell align="right">
                      <Num>{f.losses}</Num>
                    </TableCell>
                    <TableCell align="right">
                      <RValue r={f.lost_r} digits={1} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </DataTable>
          ) : null}
        </Box>
      ) : null}
    </SectionCard>
  );
}

/** The Arena section sidebar (WL-093), like the Unefy project sidebar. */
function SectionNav({
  section,
  onSection,
  data,
  found,
}: Readonly<{ section: Section; onSection: (s: Section) => void; data: ArenaOverview | null; found: number | null }>) {
  const count: Partial<Record<Section, string>> = {
    standings: data ? String(data.agents.length) : undefined,
    days: data?.history.days ? data.history.days.toLocaleString() : undefined,
    trades: found !== null ? found.toLocaleString() : undefined,
  };
  return (
    <Card
      component="nav"
      aria-label="Arena sections"
      sx={{ width: 232, flexShrink: 0, alignSelf: "flex-start", position: "sticky", top: TOPBAR_HEIGHT + 24, py: 1 }}
    >
      <Box sx={{ px: 2, pt: 0.5, pb: 1 }}>
        <Typography variant="body2" sx={{ fontWeight: 700 }}>
          Arena
        </Typography>
        <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
          {data?.history.first ? `History ${data.history.first} to ${data.history.last ?? ""}` : "Agents on the same candles"}
        </Typography>
      </Box>
      <List dense disablePadding>
        {SECTIONS.map((s) => (
          <ListItemButton
            key={s.key}
            selected={section === s.key}
            aria-current={section === s.key ? "page" : undefined}
            onClick={() => onSection(s.key)}
            sx={{
              mx: 1,
              my: 0.25,
              borderRadius: 1,
              minHeight: 40,
              "&.Mui-selected": { color: "primary.main", bgcolor: "surface.action" },
              "&.Mui-selected .MuiListItemIcon-root": { color: "primary.main" },
            }}
          >
            <ListItemIcon sx={{ minWidth: 0, mr: 1.5, "& svg": { fontSize: 20 } }}>{s.icon}</ListItemIcon>
            <ListItemText
              primary={s.label}
              secondary={s.note}
              slotProps={{ primary: { variant: "body2", sx: { fontWeight: 600 } }, secondary: { variant: "caption", noWrap: true } }}
            />
            {count[s.key] ? <Chip size="small" label={count[s.key]} sx={[monoSx, { height: 20, ml: 1 }]} /> : null}
          </ListItemButton>
        ))}
      </List>
    </Card>
  );
}

/** The Arena (WL-069, WL-075 to WL-077, WL-092 to WL-095): the agents on the same candles, scored per day, filtered and searched. */
export default function Arena({ active }: Readonly<{ active: boolean }>) {
  const { toast, ask } = useFeedback();
  const wide = useMediaQuery((t) => t.breakpoints.up("md"));
  const [section, setSection] = useState<Section>(sectionFromHash);
  const [style, setStyle] = useState<ArenaStyle>(() => {
    const saved = readPref("cca_arena_style") ?? "";
    return (STYLES as string[]).includes(saved) ? (saved as ArenaStyle) : "all";
  });
  const [layout, setLayout] = useState<Layout>(() => (readPref("cca_arena_layout") === "expanded" ? "expanded" : "compact"));
  const dense = layout === "compact";
  // WL-101: filters, folds, search and page kept per browser.
  const [agents, setAgents] = usePref<string[]>("cca_arena_agents", []);
  const [from, setFrom] = usePref("cca_arena_from", "");
  const [to, setTo] = usePref("cca_arena_to", "");
  const [view, setView] = useState<{ key: string; data: ArenaOverview } | null>(null);
  const [chartView, setChartView] = useState<{ key: string; data: ArenaCharts } | null>(null);
  const [chartError, setChartError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [folded, setFolded] = usePref<string[]>("cca_arena_folded", []); // expanded by default (WL-076)
  const closed = new Set(folded);
  const [selected, setSelected] = usePref<string | null>("cca_arena_selected", null, (v) => v === null || typeof v === "string");
  // Trade search (WL-077)
  const [symbol, setSymbol] = usePref("cca_arena_symbol", "");
  const [strategy, setStrategy] = usePref("cca_arena_strategy", "");
  const [bucket, setBucket] = usePref("cca_arena_bucket", "");
  // WL-144: column sorts, kept per browser
  const [standSortBy, onStandSort] = useSort("cca_arena_sort_standings");
  const standSort = { sort: standSortBy, onSort: onStandSort };
  const [tradeSortBy, onTradeSort] = useSort("cca_arena_sort_trades");
  const [daySortBy, onDaySort] = useSort("cca_arena_sort_days");
  const daySort = { sort: daySortBy, onSort: onDaySort };
  const [hover, setHover] = useState<ChartHover>(null); // WL-098: the compare cursor, for the standings bars
  const [outcome, setOutcome] = usePref<"" | "win" | "loss">("cca_arena_outcome", "", oneOf("", "win", "loss"));
  const [side, setSide] = usePref<"" | "Buy" | "Sell">("cca_arena_side", "", oneOf("", "Buy", "Sell"));
  const [offset, setOffset] = usePref("cca_arena_offset", 0);
  const [found, setFound] = useState<{ key: string; base: string; trades: ArenaTrade[]; total: number } | null>(null);
  const [review, setReview] = useState<{ key: string; data: ArenaReview } | null>(null);

  useEffect(() => {
    const onHash = () => setSection(sectionFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const go = (s: Section) => {
    writePref("cca_arena_section", s);
    window.location.hash = `#/arena/${s}`;
  };

  const filters: ArenaFilters = { agents, date_from: from || undefined, date_to: to || undefined };
  const filterKey = JSON.stringify(filters);
  const ranged = Boolean(from || to);
  // WL-092: every answer carries the filters it was asked for; an answer for older filters is dropped,
  // and the page shows skeletons until the figures match what is on screen.
  const key = JSON.stringify([style, filterKey]);
  const keyRef = useRef(key);
  keyRef.current = key;

  const load = useCallback(async () => {
    const asked = key;
    try {
      const d = await api.arena(style, ranged ? 3650 : 30, JSON.parse(filterKey) as ArenaFilters);
      if (keyRef.current !== asked) return;
      setView({ key: asked, data: d });
      setError(null);
    } catch (err) {
      if (keyRef.current === asked) setError((err as Error).message);
    }
  }, [key, style, filterKey, ranged]);

  useEffect(() => {
    if (active) load().catch(() => undefined);
  }, [active, load]);

  const data = view?.data ?? null; // the last answer: agent names, history, run state
  const fresh = view?.key === key ? view.data : null; // figures for the filters on screen
  const running = Boolean(data?.task.running);
  useEffect(() => {
    if (!active || !running) return;
    const id = setTimeout(() => void load(), 2500);
    return () => clearTimeout(id);
  }, [active, running, view, load]);

  const runId = data?.latest_run?.id;
  const chartKey = `${key}|${String(runId)}`;
  const needCharts = section === "graphs" || section === "map";
  useEffect(() => {
    if (!active || !needCharts || chartView?.key === chartKey) return;
    const asked = chartKey;
    setChartError(null);
    api
      .arenaCharts(style, JSON.parse(filterKey) as ArenaFilters)
      .then((d) => {
        if (`${keyRef.current}|${String(runId)}` === asked) setChartView({ key: asked, data: d });
      })
      .catch((err: Error) => setChartError(err.message));
  }, [active, needCharts, chartKey, chartView?.key, style, filterKey, runId]);
  const charts = chartView?.key === chartKey ? chartView.data : null;

  const searchBase = JSON.stringify([key, selected, runId]);
  const searchKey = JSON.stringify([searchBase, symbol, strategy, bucket, outcome, side, offset, tradeSortBy]);
  const searchKeyRef = useRef(searchKey);
  searchKeyRef.current = searchKey;
  useEffect(() => {
    if (!active || section !== "trades") return;
    const base = JSON.parse(filterKey) as ArenaFilters;
    const f: ArenaFilters = {
      ...base,
      agents: selected ? [selected] : base.agents,
      style,
      symbol: symbol.trim() || undefined,
      strategy: strategy.trim() || undefined,
      bucket: bucket || undefined,
      outcome,
      side,
    };
    const asked = { key: searchKey, base: searchBase };
    const id = setTimeout(() => {
      api
        .arenaSearch(f, PAGE, offset, tradeSortBy)
        .then((r) => setFound((old) => (asked.key === searchKeyRef.current ? { ...asked, trades: r.trades, total: r.total } : old)))
        .catch(() => setFound({ ...asked, trades: [], total: 0 }));
    }, 300);
    return () => clearTimeout(id);
  }, [active, section, filterKey, style, symbol, strategy, bucket, outcome, side, offset, selected, searchKey, searchBase, tradeSortBy]);
  // WL-078: the chosen agent's review, for the same style and dates.
  const reviewKey = JSON.stringify([key, selected, runId]);
  useEffect(() => {
    if (!active || !selected) return;
    const base = JSON.parse(filterKey) as ArenaFilters;
    const asked = reviewKey;
    api
      .arenaReview(selected, { ...base, style })
      .then((d) => setReview({ key: asked, data: d }))
      .catch(() => setReview({ key: asked, data: { agent: selected, trades: 0, suggestions: [], slices: {} } }));
  }, [active, selected, filterKey, style, reviewKey]);

  async function start(deep: boolean) {
    if (deep) {
      const ok = await ask({
        title: "Run a deep Arena?",
        text: "It pages 5,000 candles per coin from Binance for every style, then replays every agent. It takes a few minutes. No AI is used.",
        okLabel: "Run deep",
      });
      if (!ok) return;
    }
    try {
      await api.runArena(deep ? { depth: "deep", bars: 5000 } : {});
      toast(deep ? "Deep Arena run started." : "Arena run started: candles first, then the agents.");
      await load();
    } catch (err) {
      toast(`Arena: ${(err as Error).message}`);
    }
  }

  const board = fresh?.leaderboard ?? [];
  const byId = Object.fromEntries((data?.agents ?? []).map((a) => [a.id, a]));
  const leader = board.find((r) => r.place === 1);
  const latest = fresh?.daily[0];
  const latestWinner = latest?.winner ? byId[latest.winner] : null;
  const shownAgents = (data?.agents ?? []).filter((a) => !agents.length || agents.includes(a.id));
  const chosen = selected ? byId[selected] : null;
  const toggle = (id: string) =>
    setFolded((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  const pick = (id: string) => {
    setOffset(0);
    setSelected(selected === id ? null : id);
  };
  function resetPage<T>(set: (v: T) => void): (v: T) => void {
    return (v: T) => {
      setOffset(0);
      set(v);
    };
  }
  const agentCard = chosen ? (
    <AgentCard agent={chosen} review={review?.key === reviewKey ? review.data : null} onClose={() => setSelected(null)} />
  ) : null;
  // WL-144: the trades page sorts on the server (it pages), so a new sort starts at the first page.
  const tradeSort = {
    sort: tradeSortBy,
    onSort: (k: string, first?: "asc" | "desc") => {
      setOffset(0);
      onTradeSort(k, first);
    },
  };
  const searchReady = found?.base === searchBase ? found : null;
  const searchStale = Boolean(searchReady && found?.key !== searchKey);

  const filterBar = (
    <Card>
      <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ alignItems: { md: "center" }, p: 2 }}>
        <Autocomplete
          multiple
          size="small"
          options={(data?.agents ?? []).map((a) => a.id)}
          getOptionLabel={(id) => byId[id]?.name ?? id}
          value={agents}
          onChange={(_e, v) => {
            setOffset(0);
            setAgents(v);
          }}
          renderInput={(params) => <TextField {...params} label="Agents" placeholder={agents.length ? "" : "All agents"} />}
          sx={{ flex: 2, minWidth: 240 }}
        />
        <TextField
          label="From"
          type="date"
          size="small"
          value={from}
          onChange={(e) => resetPage(setFrom)(e.target.value)}
          slotProps={{ inputLabel: { shrink: true }, htmlInput: { min: data?.history.first ?? undefined, max: to || undefined } }}
        />
        <TextField
          label="To"
          type="date"
          size="small"
          value={to}
          onChange={(e) => resetPage(setTo)(e.target.value)}
          slotProps={{ inputLabel: { shrink: true }, htmlInput: { min: from || undefined, max: data?.history.last ?? undefined } }}
        />
        <ActionButton
          compact
          disabled={!data?.history.first}
          title={data?.history.first ? `${data.history.first} to ${data.history.last ?? ""}, ${String(data.history.days)} days` : undefined}
          onClick={() => {
            setOffset(0);
            setFrom(data?.history.first ?? "");
            setTo(data?.history.last ?? "");
          }}
        >
          All history
        </ActionButton>
        <ActionButton
          compact
          disabled={!agents.length && !from && !to}
          onClick={() => {
            setOffset(0);
            setAgents([]);
            setFrom("");
            setTo("");
          }}
        >
          Clear
        </ActionButton>
        <RadioGroup
          row
          aria-label="Layout"
          value={layout}
          onChange={(_e, v) => {
            const next: Layout = v === "expanded" ? "expanded" : "compact";
            writePref("cca_arena_layout", next);
            setLayout(next);
          }}
          sx={{ flexWrap: "nowrap", ml: { md: "auto" } }}
        >
          <FormControlLabel value="compact" control={<Radio size="small" />} label="Compact" slotProps={{ typography: { variant: "body2" } }} />
          <FormControlLabel value="expanded" control={<Radio size="small" />} label="Expanded" slotProps={{ typography: { variant: "body2" } }} />
        </RadioGroup>
      </Stack>
      <Tabs
        value={style}
        onChange={(_e, v: ArenaStyle) => {
          writePref("cca_arena_style", v);
          setOffset(0);
          setStyle(v);
        }}
        variant="scrollable"
        allowScrollButtonsMobile
        sx={{ px: 1, borderTop: 1, borderColor: "divider" }}
      >
        {STYLES.map((s) => (
          <Tab key={s} value={s} label={s === "all" ? "All styles" : STYLE_LABEL[s]} />
        ))}
      </Tabs>
      {data && !fresh && !error ? <LinearProgress aria-label="Loading the new figures" /> : null}
    </Card>
  );

  const standings = (
    <>
      <KpiStrip
        tiles={[
          {
            label: "Leader",
            value: fresh ? leader ? (byId[leader.id]?.name ?? leader.id) : <Na reason="No trades yet" /> : <Skeleton width={120} />,
            note: leader ? `${fmtR(leader.total_r, 1) ?? ""} total, ${String(leader.points)} points` : fresh ? "Run the Arena" : "",
          },
          {
            label: "Latest day",
            value: fresh ? latestWinner ? latestWinner.name : <Na reason={latest ? "Every agent lost that day" : "No days yet"} /> : <Skeleton width={120} />,
            note: latest ? `Winner of ${latest.day}` : "",
          },
          {
            label: ranged ? "Days in range" : "Days shown",
            value: fresh ? String(fresh.daily.length) : <Skeleton width={60} />,
            note: data?.history.first ? `History ${data.history.first} to ${data.history.last ?? ""}` : "",
          },
          {
            label: "Last run",
            value: <V value={data?.latest_run ? fmtWhen(data.latest_run.finished_at ?? data.latest_run.started_at) : null} reason="Never run" />,
            note: data?.latest_run?.message ?? "",
          },
        ]}
      />
      <SectionCard
        title="Standings"
        icon={<EmojiEventsOutlined />}
        right={
          <>
            <ActionButton compact disabled={!board.length || board.every((r) => closed.has(r.id))} onClick={() => setFolded(board.map((r) => r.id))}>
              Fold all
            </ActionButton>
            <ActionButton compact disabled={!closed.size} onClick={() => setFolded([])}>
              Unfold all
            </ActionButton>
          </>
        }
        noPadding
      >
        {!fresh && !error ? <TableSkeleton rows={10} /> : null}
        {fresh && !board.some((r) => r.trades) ? <EmptyState icon={<EmojiEventsOutlined />} text="No results for these filters." /> : null}
        {fresh && board.some((r) => r.trades) ? (
          <DataTable minWidth={1360} maxHeight="none" size={dense ? "small" : "medium"}>
            <TableHead>
              <TableRow>
                <SortCell id="place" align="right" first="asc" {...standSort}>
                  Place
                </SortCell>
                <SortCell id="name" first="asc" {...standSort}>
                  Agent
                </SortCell>
                <SortCell id="stance" first="asc" {...standSort}>
                  Stance
                </SortCell>
                {FIGURE_COLUMNS.map(([id, label]) => (
                  <SortCell key={id} id={id} align="right" {...standSort}>
                    {label}
                  </SortCell>
                ))}
                {SIZED_COLUMNS.map(([id, , label]) => (
                  <SortCell key={id} id={id} align="right" {...standSort}>
                    {label}
                  </SortCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {sortRows(board, standSort.sort, standingValue).map((r) => {
                const open = !closed.has(r.id);
                return (
                  <Fragment key={r.id}>
                    <TableRow hover selected={selected === r.id}>
                      <TableCell align="right">
                        <V value={r.place ? String(r.place) : null} reason="No trades" />
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
                          <IconButton size="small" aria-label={open ? `Collapse ${r.name}` : `Expand ${r.name}`} aria-expanded={open} onClick={() => toggle(r.id)}>
                            {open ? <KeyboardArrowDown fontSize="small" /> : <KeyboardArrowRight fontSize="small" />}
                          </IconButton>
                          <Box
                            role="button"
                            tabIndex={0}
                            onClick={() => pick(r.id)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") pick(r.id);
                            }}
                            sx={{ cursor: "pointer" }}
                            title="Show how it trades"
                          >
                            <Typography variant="body2" sx={{ fontWeight: 700 }}>
                              {r.name}
                            </Typography>
                            <Typography variant="caption" sx={{ color: "text.secondary" }}>
                              {r.person} · overall
                            </Typography>
                          </Box>
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <StancePill a={r} />
                      </TableCell>
                      <FigureCells f={r} />
                      {SIZED_COLUMNS.map(([id, lev]) => (
                        <TableCell key={id} align="right">
                          <SizedCell s={r.sized?.find((s) => s.leverage === lev)} />
                        </TableCell>
                      ))}
                    </TableRow>
                    {open
                      ? sortRows(r.groups, standSort.sort, figureValue).map((g) => (
                          <TableRow key={`${r.id}-${g.bucket}`} sx={{ "& td": { borderBottomStyle: "dashed" } }}>
                            <TableCell />
                            <TableCell sx={{ pl: 7, color: "text.secondary" }}>{g.label}</TableCell>
                            <TableCell />
                            <FigureCells f={g} />
                            <TableCell colSpan={SIZED_COLUMNS.length} />
                          </TableRow>
                        ))
                      : null}
                  </Fragment>
                );
              })}
            </TableBody>
          </DataTable>
        ) : null}
      </SectionCard>
      {agentCard}
    </>
  );

  const chartsMissing = chartError ? <Alert severity="warning">Graphs unavailable: {chartError}</Alert> : null;
  const graphs = (
    <>
      {chartsMissing}
      {/* WL-098: compare and the standings side by side, both following the compare cursor; agents by style below. */}
      {/* WL-100: expanded stacks them at full width with the bigger charts and rows. */}
      <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "1fr", lg: dense ? "7fr 5fr" : "1fr" }, alignItems: "stretch" }}>
        <SectionCard title="Compare agents over time" icon={<InsightsOutlined />} noPadding>
          <Box sx={{ p: 1.5, height: "100%" }}>
            {charts && fresh ? (
              <CompareChart
                charts={charts}
                agents={data?.agents ?? []}
                initial={board.filter((r) => r.trades).map((r) => r.id)}
                height={dense ? 150 : 360}
                fill={dense}
                onHover={setHover}
              />
            ) : (
              <ChartSkeleton height={dense ? 170 : 380} />
            )}
          </Box>
        </SectionCard>
        <SectionCard title="Standings chart" icon={<EmojiEventsOutlined />} noPadding>
          <Box sx={{ p: 1.5 }}>
            {fresh ? board.some((r) => r.trades) ? <StandingsChart board={board} selected={selected} onPick={pick} hover={hover} dense={dense} /> : <EmptyState text="No results for these filters." /> : <ChartSkeleton />}
          </Box>
        </SectionCard>
      </Box>
      <SectionCard title="Agents by style" icon={<CalendarViewMonthOutlined />} noPadding>
        <Box sx={{ p: 1.5 }}>
          {charts && fresh ? <StyleGrid charts={charts} board={board} selected={selected} onPick={pick} hover={hover} dense={dense} /> : <ChartSkeleton />}
        </Box>
      </SectionCard>
      {agentCard}
    </>
  );

  const map = (
    <>
      {chartsMissing}
      <SectionCard title="Agent map" icon={<AccountTreeOutlined />}>
        {charts && fresh ? (
          <AgentMap charts={charts} board={board} agents={data?.agents ?? []} selected={selected} onPick={pick} />
        ) : (
          <ChartSkeleton height={520} />
        )}
      </SectionCard>
      {agentCard}
    </>
  );

  const trades = (
    <SectionCard
      title={chosen ? `Trades: ${chosen.name}` : "Trades"}
      icon={<Search />}
      right={
        <>
          {chosen ? (
            <ActionButton compact onClick={() => setSelected(null)}>
              All agents
            </ActionButton>
          ) : null}
          {searchReady ? (
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              {searchReady.total.toLocaleString()} found
            </Typography>
          ) : null}
        </>
      }
      noPadding
    >
      <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ p: 2 }}>
        <TextField label="Coin or stock" size="small" value={symbol} onChange={(e) => resetPage(setSymbol)(e.target.value)} placeholder="SOL, TSLA" />
        <TextField label="Strategy" size="small" value={strategy} onChange={(e) => resetPage(setStrategy)(e.target.value)} placeholder="ema_cross, gujjar" />
        <TextField select label="Group" size="small" value={bucket} onChange={(e) => resetPage(setBucket)(e.target.value)} sx={{ minWidth: 150 }}>
          <MenuItem value="">All groups</MenuItem>
          {Object.entries(data?.buckets ?? {}).map(([k, label]) => (
            <MenuItem key={k} value={k}>
              {label}
            </MenuItem>
          ))}
        </TextField>
        <TextField select label="Side" size="small" value={side} onChange={(e) => resetPage(setSide)(e.target.value as "" | "Buy" | "Sell")} sx={{ minWidth: 120 }}>
          <MenuItem value="">Both</MenuItem>
          <MenuItem value="Buy">▲ Long</MenuItem>
          <MenuItem value="Sell">▼ Short</MenuItem>
        </TextField>
        <TextField select label="Result" size="small" value={outcome} onChange={(e) => resetPage(setOutcome)(e.target.value as "" | "win" | "loss")} sx={{ minWidth: 120 }}>
          <MenuItem value="">All</MenuItem>
          <MenuItem value="win">▲ Won</MenuItem>
          <MenuItem value="loss">▼ Lost</MenuItem>
        </TextField>
      </Stack>
      {searchStale ? <LinearProgress aria-label="Searching" /> : null}
      {searchReady === null ? <TableSkeleton rows={8} /> : null}
      {searchReady && !searchReady.trades.length ? <EmptyState text="No trades match." /> : null}
      {searchReady?.trades.length ? (
        <Box sx={{ opacity: searchStale ? 0.5 : 1, transition: "opacity 120ms" }}>
          <DataTable minWidth={1240} maxHeight={640}>
            <TableHead>
              <TableRow>
                <SortCell id="exit_time" {...tradeSort}>
                  Closed
                </SortCell>
                <SortCell id="agent_id" first="asc" {...tradeSort}>
                  Agent
                </SortCell>
                <SortCell id="symbol" first="asc" {...tradeSort}>
                  Pair
                </SortCell>
                <SortCell id="style" first="asc" {...tradeSort}>
                  Style
                </SortCell>
                <SortCell id="side" first="asc" {...tradeSort}>
                  Side
                </SortCell>
                <SortCell id="strategy" first="asc" {...tradeSort}>
                  Strategy
                </SortCell>
                <SortCell id="entry" align="right" {...tradeSort}>
                  Entry
                </SortCell>
                <SortCell id="stop" align="right" {...tradeSort}>
                  Stop
                </SortCell>
                <SortCell id="exit" align="right" {...tradeSort}>
                  Exit
                </SortCell>
                <SortCell id="exit_reason" first="asc" {...tradeSort}>
                  How it closed
                </SortCell>
                <SortCell id="r_multiple" align="right" {...tradeSort}>
                  R
                </SortCell>
                <SortCell id="pnl_usdt" align="right" {...tradeSort}>
                  USDT at 10x
                </SortCell>
                <TableCell>Why</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {searchReady.trades.map((t) => {
                const cls = biasClass(t.side);
                return (
                  <TableRow key={t.id} hover>
                    <TableCell sx={{ whiteSpace: "nowrap" }}>
                      <Num>{t.exit_day}</Num>
                      <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                        {fmtWhen(new Date(t.exit_time).toISOString()) ?? ""}
                      </Typography>
                    </TableCell>
                    <TableCell>{byId[t.agent_id]?.name ?? t.agent_id}</TableCell>
                    <TableCell>
                      <Num sx={{ fontWeight: 700 }}>{t.symbol}</Num>
                      <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                        {GROUP_LABEL[t.coin_group] ?? t.coin_group}
                      </Typography>
                    </TableCell>
                    <TableCell>{STYLE_LABEL[t.style] ?? t.style}</TableCell>
                    <TableCell>
                      <Pill glyph={GLYPH[cls]} label={t.side} tone={cls === "buy" ? "buy" : "sell"} />
                    </TableCell>
                    <TableCell sx={{ color: "text.secondary" }}>{t.strategy ?? ""}</TableCell>
                    <TableCell align="right">
                      <V value={fmtPx(t.entry)} />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtPx(t.stop)} />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtPx(t.exit)} />
                    </TableCell>
                    <TableCell>{EXIT_LABEL[t.exit_reason]}</TableCell>
                    <TableCell align="right">
                      <RValue r={t.r_multiple} />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtFixed(t.pnl_usdt, 2)} reason="Not sized (before WL-148)" />
                    </TableCell>
                    <TableCell sx={{ color: "text.secondary", maxWidth: 320, overflowWrap: "anywhere" }}>
                      {t.retro ?? t.note ?? ""}
                      {t.score !== null && t.score !== undefined ? ` · A+ ${String(t.score)}/8` : ""}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </DataTable>
        </Box>
      ) : null}
      {searchReady && searchReady.total > PAGE ? (
        <Stack direction="row" spacing={1} sx={{ p: 1.5, justifyContent: "flex-end", alignItems: "center" }}>
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            {String(offset + 1)} to {String(Math.min(offset + PAGE, searchReady.total))} of {searchReady.total.toLocaleString()}
          </Typography>
          <ActionButton compact disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
            Newer
          </ActionButton>
          <ActionButton compact disabled={offset + PAGE >= searchReady.total} onClick={() => setOffset(offset + PAGE)}>
            Older
          </ActionButton>
        </Stack>
      ) : null}
    </SectionCard>
  );

  const days = (
    <SectionCard title={ranged ? "Day by day (the range)" : "Day by day (newest 30)"} icon={<CalendarViewMonthOutlined />} noPadding>
      {!fresh && !error ? <TableSkeleton rows={10} /> : null}
      {fresh?.daily.length ? (
        <DataTable minWidth={1100} maxHeight={720}>
          <TableHead>
            <TableRow>
              <SortCell id="day" {...daySort}>
                Day
              </SortCell>
              <SortCell id="winner" first="asc" {...daySort}>
                Winner
              </SortCell>
              {shownAgents.map((a) => (
                <SortCell key={a.id} id={`r:${a.id}`} align="right" {...daySort}>
                  {a.name}
                </SortCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {sortRows(fresh.daily, daySortBy, (d, k) =>
              k === "day" ? d.day : k === "winner" ? (d.winner ? (byId[d.winner]?.name ?? d.winner) : null) : d.agents[k.slice(2)]?.total_r,
            ).map((d) => (
              <TableRow key={d.day} hover>
                <TableCell sx={{ whiteSpace: "nowrap" }}>
                  <Num>{d.day}</Num>
                </TableCell>
                <TableCell>
                  {d.winner ? <Pill glyph="★" label={byId[d.winner]?.name ?? d.winner} tone="info" /> : <Na reason="Every agent lost that day" />}
                </TableCell>
                {shownAgents.map((a) => {
                  const c = d.agents[a.id];
                  return (
                    <TableCell key={a.id} align="right" sx={{ whiteSpace: "nowrap" }}>
                      {c ? (
                        <>
                          <RValue r={c.total_r} digits={1} />
                          <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                            {fmtRate(c.win_rate) ?? ""} of {c.trades}
                            {c.points ? ` · ${String(c.points)} pts` : ""}
                          </Typography>
                        </>
                      ) : (
                        <Na reason="No trade closed that day" />
                      )}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </DataTable>
      ) : null}
      {fresh && !fresh.daily.length ? <EmptyState text="No days in this range." /> : null}
    </SectionCard>
  );

  const learning = (
    <>
      <LessonsCard active={active && section === "learning"} names={Object.fromEntries((data?.agents ?? []).map((a) => [a.id, a.name]))} version={runId} />
      <ProReportsCard active={active && section === "learning"} running={running} version={runId} />
    </>
  );

  const body: Record<Section, ReactElement> = { standings, graphs, map, trades, days, learning };

  return (
    <Stack direction="row" spacing={3} sx={{ alignItems: "flex-start" }}>
      {wide ? <SectionNav section={section} onSection={go} data={data} found={searchReady?.total ?? null} /> : null}
      <Stack spacing={2} sx={{ flex: 1, minWidth: 0 }}>
        <PageHeader
          title={`Arena · ${SECTIONS.find((s) => s.key === section)?.label ?? ""}`}
          subtitle="The agents on the same Binance candles with fees and slippage. Places follow total R. Each day, the agents above 0R score 16, 14, 12, 10, 8, 6, 5, 4, 3, 2, 1 by rank and the best one wins the day. Every run and trade is kept. No AI is used."
          actions={
            <>
              <ActionButton disabled={!data || running} onClick={() => void start(true)}>
                Run deep
              </ActionButton>
              <ActionButton icon={<PlayArrow />} primary busy={running} busyLabel="Running…" disabled={!data} onClick={() => void start(false)}>
                Run quick
              </ActionButton>
            </>
          }
        />
        {wide ? null : (
          <Tabs value={section} onChange={(_e, v: Section) => go(v)} variant="scrollable" allowScrollButtonsMobile aria-label="Arena sections">
            {SECTIONS.map((s) => (
              <Tab key={s.key} value={s.key} label={s.label} icon={s.icon} iconPosition="start" sx={{ minHeight: 48 }} />
            ))}
          </Tabs>
        )}
        {error ? <Alert severity="warning">Arena unavailable: {error}</Alert> : null}
        {data?.task.error ? <Alert severity="warning">Last run failed: {data.task.error}</Alert> : null}
        {running && data?.latest_run ? (
          <Card sx={{ p: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
              Arena running
            </Typography>
            <RunProgress
              done={data.latest_run.progress_done}
              total={data.latest_run.progress_total}
              note={data.latest_run.progress_note}
              startedAt={data.latest_run.started_at}
            />
          </Card>
        ) : null}
        {section === "learning" ? null : filterBar}
        {body[section]}
      </Stack>
    </Stack>
  );
}
