import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import ListSubheader from "@mui/material/ListSubheader";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import DashboardOutlined from "@mui/icons-material/DashboardOutlined";
import EmojiEventsOutlined from "@mui/icons-material/EmojiEventsOutlined";
import PersonOutline from "@mui/icons-material/PersonOutlined";
import StarOutline from "@mui/icons-material/StarBorderOutlined";
import { type ReactElement, useMemo } from "react";
import type { AgentPick, AgentPickStyle, AgentPicksAgent, AgentPicksResponse } from "../api";
import { GLYPH, GROUP_LABEL, STYLE_LABEL, biasClass, fmtCompact, fmtFixed, fmtPx, fmtR, fmtRate, humanize } from "../lib/format";
import { TOPBAR_HEIGHT } from "../theme";
import { RValue, StancePill } from "./ArenaCharts";
import { type FilterColumn, useTableFilters } from "./TableFilters";
import { DataTable, EmptyState, KpiStrip, Na, Num, Pill, SectionCard, V, monoSx } from "./ui";

/** WL-128: the picks page sections: the winners dashboard, the house list, or one Arena agent (`agent:<id>`). */
export type PicksSection = "dashboard" | "house" | `agent:${string}`;

export const AGENT_PICK_STYLES: AgentPickStyle[] = ["scalp", "day", "swing", "position"];
export const WINNERS = 5; // agents on the dashboard

const pct = (v: number | null | undefined) => (v === null || v === undefined ? null : v * 100);

/** Agents best first by Arena total R on this style; agents without trades there last. */
export function rankAgents(agents: readonly AgentPicksAgent[], style: AgentPickStyle): AgentPicksAgent[] {
  return [...agents].sort((a, b) => (b.standing[style]?.total_r ?? -Infinity) - (a.standing[style]?.total_r ?? -Infinity));
}

/** The Arena agents that made money on this style, best first (WL-128 dashboard). */
export function winnersOf(agents: readonly AgentPicksAgent[], style: AgentPickStyle): AgentPicksAgent[] {
  return rankAgents(agents, style)
    .filter((a) => (a.standing[style]?.total_r ?? 0) > 0)
    .slice(0, WINNERS);
}

function Pair({ symbol, market, onOpen }: Readonly<{ symbol: string; market: string; onOpen: (symbol: string, market: string) => void }>) {
  return (
    <Tooltip title={`Open ${symbol} on the desk`}>
      <Typography
        component="button"
        onClick={() => onOpen(symbol, market)}
        sx={{ all: "unset", cursor: "pointer", fontWeight: 700, fontFamily: (t) => t.typography.fontFamilyMono, "&:hover": { color: "primary.main" }, "&:focus-visible": { outline: 2, outlineColor: "primary.main" } }}
      >
        {symbol}
      </Typography>
    </Tooltip>
  );
}

function SidePill({ side }: Readonly<{ side: string }>) {
  const cls = biasClass(side);
  return <Pill glyph={GLYPH[cls]} label={side} tone={cls === "buy" ? "buy" : "sell"} />;
}

function Exit({ p }: Readonly<{ p: AgentPick }>) {
  if (p.target !== null && p.target !== undefined) return <V value={fmtPx(p.target)} />;
  if (p.trail) {
    return (
      <Tooltip title={`No fixed target: out on a close beyond the ${String(p.trail)}-bar extreme`}>
        <Typography variant="body2" component="span" sx={{ color: "text.secondary" }}>
          Trail {p.trail} bars
        </Typography>
      </Tooltip>
    );
  }
  return <Na reason="Exits at the horizon" />;
}

const freshness = (ago: number) => (ago === 0 ? "Last bar" : `${String(ago)} bar${ago === 1 ? "" : "s"} ago`);

/** The section sidebar, like the Arena's (WL-093): dashboard, house list, then every agent best first. */
export function PicksNav({
  section,
  onSection,
  data,
  style,
  houseCount,
}: Readonly<{ section: PicksSection; onSection: (s: PicksSection) => void; data: AgentPicksResponse | null; style: AgentPickStyle; houseCount: number | null }>) {
  const ranked = rankAgents(data?.agents ?? [], style);
  const item = (key: PicksSection, icon: ReactElement, primary: string, secondary: string, count?: ReactElement | null) => (
    <ListItemButton
      key={key}
      selected={section === key}
      aria-current={section === key ? "page" : undefined}
      onClick={() => onSection(key)}
      sx={{
        mx: 1,
        my: 0.25,
        borderRadius: 1,
        minHeight: 40,
        "&.Mui-selected": { color: "primary.main", bgcolor: "surface.action" },
        "&.Mui-selected .MuiListItemIcon-root": { color: "primary.main" },
      }}
    >
      <ListItemIcon sx={{ minWidth: 0, mr: 1.5, "& svg": { fontSize: 20 } }}>{icon}</ListItemIcon>
      <ListItemText
        primary={primary}
        secondary={secondary}
        slotProps={{ primary: { variant: "body2", sx: { fontWeight: 600 }, noWrap: true }, secondary: { variant: "caption", noWrap: true } }}
      />
      {count}
    </ListItemButton>
  );
  return (
    <Card
      component="nav"
      aria-label="Picks sections"
      sx={{ width: 248, flexShrink: 0, alignSelf: "flex-start", position: "sticky", top: TOPBAR_HEIGHT + 24, py: 1, maxHeight: `calc(100vh - ${String(TOPBAR_HEIGHT + 48)}px)`, overflowY: "auto" }}
    >
      <Box sx={{ px: 2, pt: 0.5, pb: 1 }}>
        <Typography variant="body2" sx={{ fontWeight: 700 }}>
          Top 10 picks
        </Typography>
        <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
          {data?.day ? `Agent lists for ${data.day}` : "The house list and every Arena agent's own"}
        </Typography>
      </Box>
      <List dense disablePadding>
        {item("dashboard", <DashboardOutlined />, "Dashboard", "The Arena winners' picks")}
        {item(
          "house",
          <StarOutline />,
          "House Top 10",
          "Deterministic score",
          houseCount === null ? null : <Chip size="small" label={houseCount} sx={[monoSx, { height: 20, ml: 1 }]} />,
        )}
      </List>
      <Divider sx={{ my: 1 }} />
      <List
        dense
        disablePadding
        subheader={
          <ListSubheader disableSticky sx={{ bgcolor: "transparent", lineHeight: "28px" }}>
            Arena agents, best {STYLE_LABEL[style]} first
          </ListSubheader>
        }
      >
        {ranked.map((a) => {
          const st = a.standing[style];
          const n = a.picks[style]?.length ?? 0;
          const trades = a.styles.includes(style);
          return item(
            `agent:${a.id}`,
            <PersonOutline />,
            a.name,
            !trades ? `No ${STYLE_LABEL[style]} trades` : st ? `${fmtR(st.total_r, 1) ?? ""} in the Arena` : "No Arena trades yet",
            trades ? <Chip size="small" label={n} sx={[monoSx, { height: 20, ml: 1 }]} /> : null,
          );
        })}
      </List>
    </Card>
  );
}

const AGENT_PICK_FILTERS: FilterColumn<AgentPick>[] = [
  { key: "rank", label: "#", kind: "range", get: (p) => p.rank },
  { key: "pair", label: "Pair", kind: "text", get: (p) => p.symbol },
  { key: "group", label: "Group", kind: "choice", get: (p) => p.coin_group, labelOf: (v) => GROUP_LABEL[v] ?? v },
  { key: "market", label: "Market", kind: "choice", get: (p) => (p.market === "usdm" ? "Perp" : "Spot") },
  { key: "side", label: "Side", kind: "choice", get: (p) => p.side },
  { key: "entry", label: "Entry", kind: "range", get: (p) => p.entry },
  { key: "stop", label: "Stop", kind: "range", get: (p) => p.stop },
  { key: "target", label: "Target", kind: "range", get: (p) => p.target },
  { key: "exit", label: "Exit", kind: "choice", get: (p) => (p.target !== null && p.target !== undefined ? "Target" : p.trail ? "Trailing" : "Horizon") },
  { key: "rr", label: "R:R", kind: "range", get: (p) => p.rr },
  { key: "risk", label: "Stop distance %", kind: "range", get: (p) => (Math.abs(p.entry - p.stop) / p.entry) * 100 },
  { key: "strategy", label: "Rule", kind: "choice", get: (p) => p.strategy, labelOf: humanize },
  { key: "fresh", label: "Signal age (bars)", kind: "range", get: (p) => p.bars_ago },
  { key: "avg_r", label: "Arena avg R here", kind: "range", get: (p) => p.agent_avg_r },
  { key: "win", label: "Arena win rate %", kind: "range", get: (p) => pct(p.agent_win_rate) },
  { key: "trades", label: "Arena trades here", kind: "range", get: (p) => p.agent_trades },
  { key: "volume", label: "24h volume ($M)", kind: "range", get: (p) => (p.volume_usd === null || p.volume_usd === undefined ? null : p.volume_usd / 1e6) },
];
const agentPickText = (p: AgentPick) => `${p.symbol} ${GROUP_LABEL[p.coin_group] ?? p.coin_group} ${p.side} ${humanize(p.strategy)} ${p.note ?? ""}`;
const NO_PICKS: AgentPick[] = [];

/** One agent's own Top 10 for the style, with search and a filter per column (WL-127, WL-128). */
export function AgentPickTable({
  agent,
  style,
  onOpen,
}: Readonly<{ agent: AgentPicksAgent; style: AgentPickStyle; onOpen: (symbol: string, market: string) => void }>) {
  const rows = agent.picks[style] ?? NO_PICKS;
  const { shown, bar } = useTableFilters(`cca_picks_agent_filters`, rows, AGENT_PICK_FILTERS, agentPickText, "picks");
  const st = agent.standing[style];
  const trades = agent.styles.includes(style);
  return (
    <Stack spacing={2}>
      <Card sx={{ p: 2 }}>
        <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ justifyContent: "space-between" }}>
          <Box sx={{ minWidth: 0 }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", mb: 0.5 }}>
              <Typography variant="h3" component="h2">
                {agent.name}
              </Typography>
              <StancePill a={agent} />
            </Stack>
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              {agent.summary}
            </Typography>
            <Box component="ul" sx={{ m: 0, mt: 1, pl: 2.5, color: "text.secondary", typography: "caption" }}>
              {agent.rules.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </Box>
          </Box>
          <Stack spacing={0.5} sx={{ minWidth: 200, flexShrink: 0 }}>
            <Typography variant="overline" sx={{ color: "text.secondary" }}>
              Arena, {STYLE_LABEL[style]}
            </Typography>
            {st ? (
              <>
                <RValue r={st.total_r} digits={1} />
                <Typography variant="caption" sx={{ color: "text.secondary" }}>
                  {st.trades.toLocaleString()} trades, {fmtFixed(st.avg_r, 3) ?? ""}R a trade, {fmtRate(pct(st.win_rate)) ?? ""} won, {st.points.toLocaleString()} points
                </Typography>
              </>
            ) : (
              <Na reason="No Arena trades on this style yet" />
            )}
          </Stack>
        </Stack>
      </Card>
      <Card>
        {!trades ? <EmptyState icon={<PersonOutline />} text={`${agent.name} does not trade ${STYLE_LABEL[style]}.`} /> : null}
        {trades && !rows.length ? <EmptyState icon={<StarOutline />} text="No plan from this agent on the newest candles for this style." /> : null}
        {rows.length ? <Box sx={{ p: 2, pb: 1 }}>{bar}</Box> : null}
        {rows.length && !shown.length ? <EmptyState icon={<StarOutline />} text="No pick matches the search and filters." /> : null}
        {shown.length ? (
          <DataTable minWidth={1180}>
            <TableHead>
              <TableRow>
                <TableCell>#</TableCell>
                <TableCell>Pair</TableCell>
                <TableCell>Side</TableCell>
                <TableCell align="right">Entry</TableCell>
                <TableCell align="right">Stop</TableCell>
                <TableCell align="right">Target</TableCell>
                <TableCell align="right">R:R</TableCell>
                <TableCell>Rule</TableCell>
                <TableCell>Signal</TableCell>
                <TableCell align="right">
                  <Tooltip title="This agent's Arena result on this style and coin bucket: average R a trade, win rate and trades">
                    <span>Arena here</span>
                  </Tooltip>
                </TableCell>
                <TableCell align="right">24h volume</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {shown.map((p) => (
                <TableRow key={p.symbol} hover>
                  <TableCell>
                    <Num>{p.rank}</Num>
                  </TableCell>
                  <TableCell>
                    <Pair symbol={p.symbol} market={p.market} onOpen={onOpen} />
                    <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                      {GROUP_LABEL[p.coin_group] ?? p.coin_group}
                      {p.market === "usdm" ? " · perp" : ""}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <SidePill side={p.side} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtPx(p.entry)} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtPx(p.stop)} />
                  </TableCell>
                  <TableCell align="right">
                    <Exit p={p} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtFixed(p.rr, 1)} reason="No fixed target" />
                  </TableCell>
                  <TableCell sx={{ whiteSpace: "normal", minWidth: 160 }}>
                    <Typography variant="body2">{p.strategy ? humanize(p.strategy) : <Na reason="The agent's own rule" />}</Typography>
                    {p.note && p.note !== p.strategy ? (
                      <Typography variant="caption" sx={{ color: "text.secondary" }}>
                        {p.note}
                      </Typography>
                    ) : null}
                  </TableCell>
                  <TableCell>{freshness(p.bars_ago)}</TableCell>
                  <TableCell align="right">
                    <RValue r={p.agent_avg_r} digits={3} reason="No Arena trades in this bucket" />
                    <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                      {p.agent_trades ? `${fmtRate(pct(p.agent_win_rate)) ?? ""} of ${p.agent_trades.toLocaleString()}` : ""}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtCompact(p.volume_usd, "$")} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </DataTable>
        ) : null}
      </Card>
    </Stack>
  );
}

type Consensus = { symbol: string; market: string; side: "Buy" | "Sell"; coin_group: string; agents: AgentPicksAgent[]; weight: number; best: number | null; entry: number };

/** The winners dashboard (WL-128): the Arena's best agents on the style, their own lists, and where they agree. */
export function WinnersDashboard({
  data,
  style,
  onAgent,
  onOpen,
}: Readonly<{ data: AgentPicksResponse; style: AgentPickStyle; onAgent: (id: string) => void; onOpen: (symbol: string, market: string) => void }>) {
  const winners = useMemo(() => winnersOf(data.agents, style), [data, style]);
  const consensus = useMemo(() => {
    const by = new Map<string, Consensus>();
    winners.forEach((a, place) => {
      for (const p of a.picks[style] ?? []) {
        const key = `${p.symbol}|${p.side}`;
        const cur = by.get(key) ?? { symbol: p.symbol, market: p.market, side: p.side, coin_group: p.coin_group, agents: [], weight: 0, best: null, entry: p.entry };
        cur.agents.push(a);
        cur.weight += (WINNERS - place) * (11 - p.rank); // a higher place and a higher rank count more
        if (p.agent_avg_r !== null && p.agent_avg_r !== undefined) cur.best = Math.max(cur.best ?? -Infinity, p.agent_avg_r);
        by.set(key, cur);
      }
    });
    return [...by.values()].sort((a, b) => b.agents.length - a.agents.length || b.weight - a.weight).slice(0, 10);
  }, [winners, style]);
  const withPicks = data.agents.filter((a) => (a.picks[style]?.length ?? 0) > 0).length;
  const lead = winners[0];

  return (
    <Stack spacing={2}>
      <KpiStrip
        tiles={[
          { label: "Lists for", value: data.day ?? "none", note: "Built with the daily picks" },
          { label: "Arena winners", value: String(winners.length), note: `Agents above 0R on ${STYLE_LABEL[style]}`, tone: winners.length ? "buy" : "text" },
          { label: "Leader", value: lead?.name ?? "none", note: lead ? `${fmtFixed(lead.standing[style]?.total_r, 1) ?? ""}R total` : "No agent made money here" },
          { label: "Agents with picks", value: `${String(withPicks)} of ${String(data.agents.length)}`, note: "A plan on the newest candles" },
          { label: "Shared picks", value: String(consensus.filter((c) => c.agents.length > 1).length), note: "Where two winners or more agree" },
        ]}
      />
      {!winners.length ? (
        <Card>
          <EmptyState icon={<EmojiEventsOutlined />} text={`No Arena agent made money on ${STYLE_LABEL[style]} yet, so there is no winner to follow.`} />
        </Card>
      ) : null}
      {winners.length ? (
        <SectionCard title="Winners' Top 10" icon={<EmojiEventsOutlined />} right={<Typography variant="caption" sx={{ color: "text.secondary" }}>Most winners agreeing first</Typography>} noPadding>
          {consensus.length ? (
            <DataTable minWidth={880} maxHeight="none">
              <TableHead>
                <TableRow>
                  <TableCell>#</TableCell>
                  <TableCell>Pair</TableCell>
                  <TableCell>Side</TableCell>
                  <TableCell>Winners with it</TableCell>
                  <TableCell align="right">Best Arena avg R here</TableCell>
                  <TableCell align="right">Entry</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {consensus.map((c, i) => (
                  <TableRow key={`${c.symbol}-${c.side}`} hover>
                    <TableCell>
                      <Num>{i + 1}</Num>
                    </TableCell>
                    <TableCell>
                      <Pair symbol={c.symbol} market={c.market} onOpen={onOpen} />
                      <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                        {GROUP_LABEL[c.coin_group] ?? c.coin_group}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <SidePill side={c.side} />
                    </TableCell>
                    <TableCell sx={{ whiteSpace: "normal" }}>
                      <Stack direction="row" spacing={0.5} useFlexGap sx={{ flexWrap: "wrap" }}>
                        {c.agents.map((a) => (
                          <Chip key={a.id} size="small" variant="outlined" label={a.name} onClick={() => onAgent(a.id)} />
                        ))}
                      </Stack>
                    </TableCell>
                    <TableCell align="right">
                      <RValue r={c.best} digits={3} reason="No Arena trades in this bucket" />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtPx(c.entry)} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </DataTable>
          ) : (
            <EmptyState icon={<StarOutline />} text="The winners have no plan on the newest candles for this style." />
          )}
        </SectionCard>
      ) : null}
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))", xl: "repeat(3, minmax(0, 1fr))" } }}>
        {winners.map((a, place) => {
          const st = a.standing[style];
          const list = a.picks[style] ?? [];
          return (
            <SectionCard
              key={a.id}
              title={
                <Box component="span" sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}>
                  <Num sx={{ color: "text.secondary" }}>{place + 1}</Num>
                  <Box component="button" onClick={() => onAgent(a.id)} sx={{ all: "unset", cursor: "pointer", "&:hover": { color: "primary.main" }, "&:focus-visible": { outline: 2, outlineColor: "primary.main" } }}>
                    {a.name}
                  </Box>
                </Box>
              }
              icon={<PersonOutline />}
              right={<RValue r={st?.total_r} digits={1} />}
              noPadding
            >
              <Typography variant="caption" component="div" sx={{ color: "text.secondary", px: 2, py: 1, borderBottom: 1, borderColor: "divider" }}>
                {st ? `${st.trades.toLocaleString()} Arena trades, ${fmtFixed(st.avg_r, 3) ?? ""}R a trade, ${fmtRate(pct(st.win_rate)) ?? ""} won` : ""}
              </Typography>
              {list.length ? (
                <DataTable minWidth={420} maxHeight="none">
                  <TableBody>
                    {list.map((p) => (
                      <TableRow key={p.symbol} hover>
                        <TableCell sx={{ width: 32 }}>
                          <Num>{p.rank}</Num>
                        </TableCell>
                        <TableCell>
                          <Pair symbol={p.symbol} market={p.market} onOpen={onOpen} />
                        </TableCell>
                        <TableCell>
                          <SidePill side={p.side} />
                        </TableCell>
                        <TableCell align="right">
                          <V value={fmtPx(p.entry)} />
                        </TableCell>
                        <TableCell align="right">
                          <Exit p={p} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </DataTable>
              ) : (
                <EmptyState icon={<StarOutline />} text="No plan on the newest candles." />
              )}
            </SectionCard>
          );
        })}
      </Box>
    </Stack>
  );
}
