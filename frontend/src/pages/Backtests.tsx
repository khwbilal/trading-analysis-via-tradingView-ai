import Alert from "@mui/material/Alert";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import Close from "@mui/icons-material/Close";
import HistoryOutlined from "@mui/icons-material/HistoryOutlined";
import Tune from "@mui/icons-material/Tune";
import ScienceOutlined from "@mui/icons-material/ScienceOutlined";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  api,
  type ArenaAgent,
  type BacktestOptions,
  type BacktestResponse,
  type BacktestResult,
  type BacktestRunState,
  type BacktestTrade,
  type Strategy,
} from "../api";
import BacktestSearch from "../components/BacktestSearch";
import BacktestWizard from "../components/BacktestWizard";
import { useFeedback } from "../components/feedback";
import { RunProgress, StatePill, StateTabs, countStates, type RunFilter } from "../components/RunStatus";
import { ActionButton, DataTable, EmptyState, KpiStrip, Na, Num, PageHeader, Pill, SectionCard, StatusPill, V } from "../components/ui";
import { GLYPH, GROUP_LABEL, STYLE_LABEL, biasClass, fmtFixed, fmtPx, fmtR, fmtRate, fmtWhen } from "../lib/format";
import { useTaskData } from "../lib/useTask";
import { usePref } from "../lib/storage";

const GROUP_ORDER = ["major", "large", "mid", "meme", "lowcap", "stock", "commodity"];

/** One line for what a run replayed (WL-055); runs before the wizard show as the daily quick run. */
function describeOptions(o: BacktestOptions | null | undefined): string {
  if (!o) return "Quick, fixed coins";
  const parts = [o.depth === "deep" ? `Deep, ${(o.bars ?? 0).toLocaleString()} candles` : "Quick"];
  parts.push(o.coins === "random" ? `random coins (${String(o.random_count ?? "")} per tier, seed ${String(o.seed ?? "")})` : "fixed coins");
  if (o.strategies?.length) parts.push(`${String(o.strategies.length)} strategies`);
  if (o.styles && o.styles.length < 3) parts.push(o.styles.map((s) => STYLE_LABEL[s]).join(", "));
  if (o.any_style) parts.push("every style");
  return parts.join(", ");
}

function TradesDialog({
  cell,
  name,
  runId,
  pooled,
  onClose,
}: Readonly<{ cell: BacktestResult; name: string; runId: number | null; pooled: boolean; onClose: () => void }>) {
  const phone = useMediaQuery((t) => t.breakpoints.down("sm"));
  const [trades, setTrades] = useState<BacktestTrade[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api
      .backtestTrades(cell.strategy_id, cell.style, cell.coin_group, runId, pooled)
      .then((r) => setTrades(r.trades))
      .catch((err: unknown) => setError((err as Error).message));
  }, [cell, runId, pooled]);
  return (
    <Dialog open onClose={onClose} fullScreen={phone} fullWidth maxWidth="lg" aria-labelledby="btTitle">
      <DialogTitle id="btTitle" sx={{ display: "flex", alignItems: "center", gap: 1, pr: 1 }}>
        <Stack sx={{ flex: 1, minWidth: 0 }}>
          {name}
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            {STYLE_LABEL[cell.style]} · {GROUP_LABEL[cell.coin_group] ?? cell.coin_group} · {cell.trades} trades{pooled ? " over all runs" : ""}
            {trades && cell.trades > trades.length ? ` (newest ${String(trades.length)} shown)` : ""}
          </Typography>
        </Stack>
        <IconButton aria-label="Close" onClick={onClose}>
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ p: 0 }}>
        {error ? <Alert severity="warning">Trades unavailable: {error}</Alert> : null}
        {!trades && !error ? <Skeleton height={120} sx={{ mx: 2 }} /> : null}
        {trades ? (
          <DataTable minWidth={860} maxHeight="70vh">
            <TableHead>
              <TableRow>
                <TableCell>Entry time</TableCell>
                <TableCell>Pair</TableCell>
                <TableCell>Side</TableCell>
                <TableCell align="right">Entry</TableCell>
                <TableCell align="right">Exit</TableCell>
                <TableCell>Outcome</TableCell>
                <TableCell align="right">R</TableCell>
                <TableCell>Why it lost</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {trades.map((t) => {
                const cls = biasClass(t.side);
                return (
                  <TableRow key={t.id} hover>
                    <TableCell>
                      <V value={fmtWhen(new Date(t.entry_time).toISOString())} />
                    </TableCell>
                    <TableCell>
                      <Num sx={{ fontWeight: 600 }}>{t.symbol}</Num>
                    </TableCell>
                    <TableCell>
                      <Pill glyph={GLYPH[cls]} label={t.side} tone={cls === "buy" ? "buy" : "sell"} />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtPx(t.entry)} />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtPx(t.exit)} reason="No exit" />
                    </TableCell>
                    <TableCell>
                      <StatusPill status={t.outcome === "win" ? "win" : t.outcome === "loss" ? "loss" : "expired"} />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtR(t.r_multiple)} />
                    </TableCell>
                    <TableCell sx={{ whiteSpace: "normal" }}>
                      {t.failure_tag ? t.failure_tag : <Na reason={t.outcome === "loss" ? "No tag" : "Not a loser"} />}
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

function runDuration(run: BacktestRunState): string | null {
  if (!run.finished_at) return null;
  const s = Math.round((new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()) / 1000);
  if (Number.isNaN(s) || s < 0) return null;
  return s < 60 ? `${String(s)} s` : `${String(Math.floor(s / 60))} m ${String(s % 60)} s`;
}

/** The kept backtest runs with status tabs; a running one shows its progress (WL-053); select a finished one to view it (WL-055). */
function RunsCard({
  runs,
  shownId,
  pooled,
  combined,
  onCombined,
  onSelect,
}: Readonly<{
  runs: BacktestRunState[];
  shownId: number | null;
  pooled: boolean;
  combined: boolean;
  onCombined: () => void;
  onSelect: (id: number) => void;
}>) {
  const [filter, setFilter] = usePref<RunFilter>("cca_bt_runs_tab", "all");
  const counts = countStates(runs, (r) => r.state);
  const shown = filter === "all" ? runs : runs.filter((r) => r.state === filter);
  return (
    <SectionCard
      title="Runs"
      icon={<HistoryOutlined />}
      noPadding
      right={
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          Every run is kept; select one to view it, or all of them combined
        </Typography>
      }
    >
      <StateTabs value={filter} onChange={setFilter} counts={counts} />
      {shown.length ? (
        <DataTable minWidth={720} maxHeight="none">
          <TableHead>
            <TableRow>
              <TableCell>Started</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Setup</TableCell>
              <TableCell align="right">Duration</TableCell>
              <TableCell>Result</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {pooled && filter === "all" ? (
              <TableRow hover selected={combined} onClick={onCombined} sx={{ cursor: "pointer" }}>
                <TableCell sx={{ whiteSpace: "nowrap", fontWeight: 600 }}>All runs combined</TableCell>
                <TableCell>
                  <StatePill state="success" />
                </TableCell>
                <TableCell sx={{ whiteSpace: "normal", minWidth: 200 }}>
                  <Typography variant="body2">Every finished run, each trade once</Typography>
                </TableCell>
                <TableCell align="right">
                  <Na reason="Not one run" />
                </TableCell>
                <TableCell sx={{ minWidth: 260 }}>
                  <Typography variant="body2" sx={{ color: "text.secondary" }}>
                    What the picks and the strategy advice read
                  </Typography>
                </TableCell>
              </TableRow>
            ) : null}
            {shown.map((r) => (
              <TableRow
                key={r.id}
                hover={r.state === "success"}
                selected={!combined && r.id === shownId}
                onClick={r.state === "success" ? () => onSelect(r.id) : undefined}
                sx={{ cursor: r.state === "success" ? "pointer" : "default" }}
              >
                <TableCell sx={{ whiteSpace: "nowrap" }}>
                  <V value={fmtWhen(r.started_at)} mono={false} />
                </TableCell>
                <TableCell>
                  <StatePill state={r.state} />
                </TableCell>
                <TableCell sx={{ whiteSpace: "normal", minWidth: 200 }}>
                  <Typography variant="body2">{describeOptions(r.options)}</Typography>
                </TableCell>
                <TableCell align="right">
                  <V value={runDuration(r)} reason={r.state === "running" ? "Still running" : "No end recorded"} />
                </TableCell>
                <TableCell sx={{ minWidth: 260 }}>
                  {r.state === "running" ? (
                    <RunProgress done={r.progress_done} total={r.progress_total} note={r.progress_note} startedAt={r.started_at} />
                  ) : (
                    <Typography variant="body2" sx={{ color: "text.secondary", overflowWrap: "anywhere" }}>
                      {r.message ?? <Na reason="No message recorded" />}
                    </Typography>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </DataTable>
      ) : (
        <EmptyState icon={<HistoryOutlined />} text={runs.length ? "No runs with this status." : "No backtest runs yet."} />
      )}
    </SectionCard>
  );
}

/** Backtest results per strategy, style and coin group, with the trade list per cell (WL-033). */
export default function Backtests({ active }: Readonly<{ active: boolean }>) {
  const { toast } = useFeedback();
  const [group, setGroup] = usePref<string>("cca_bt_group_tab", "all"); // WL-101: kept per browser
  const [library, setLibrary] = useState<Strategy[]>([]);
  const [cell, setCell] = useState<BacktestResult | null>(null);
  const [runId, setRunId] = usePref<number | null>("cca_bt_run", null, (v) => v === null || typeof v === "number");
  const [combined, setCombined] = usePref("cca_bt_combined", false);
  const [wizard, setWizard] = useState(false);
  const load = useCallback(() => api.backtests(runId, combined), [runId, combined]);
  const taskOf = useCallback((d: BacktestResponse) => d.task, []);
  const { data, error, refresh } = useTaskData(load, taskOf, active);
  const names = useMemo(() => Object.fromEntries(library.map((s) => [s.id, s.name])) as Record<string, string>, [library]);

  useEffect(() => {
    if (!active || library.length) return;
    api
      .strategies()
      .then((r) => setLibrary(r.strategies))
      .catch(() => undefined);
  }, [active, library]);

  // WL-074: the wizard can start an Arena run for chosen agents too (G.O.A.T. needs the others, so it is not offered alone).
  const [agentList, setAgentList] = useState<ArenaAgent[]>([]);
  useEffect(() => {
    if (!active || agentList.length) return;
    api
      .agents()
      .then((r) => setAgentList(r.agents))
      .catch(() => undefined);
  }, [active, agentList]);

  const [strategyFilter, setStrategyFilter] = usePref("cca_bt_strategy_filter", ""); // WL-077
  const rows = useMemo(
    () =>
      (data?.results ?? [])
        .filter((r) => r.coin_group === group)
        .filter((r) => {
          const q = strategyFilter.trim().toLowerCase();
          return !q || r.strategy_id.toLowerCase().includes(q) || (names[r.strategy_id] ?? "").toLowerCase().includes(q);
        })
        .sort((a, b) => (b.win_rate ?? -1) - (a.win_rate ?? -1) || (b.avg_r ?? -9) - (a.avg_r ?? -9)),
    [data, group, strategyFilter, names],
  );
  const min = data?.min_trades ?? 20;
  const all = (data?.results ?? []).filter((r) => r.coin_group === "all");
  const totalTrades = all.reduce((n, r) => n + r.trades, 0);
  const best = all.filter((r) => r.trades >= min).sort((a, b) => (b.avg_r ?? -9) - (a.avg_r ?? -9))[0];
  const running = Boolean(data?.task.running);

  async function start(options: BacktestOptions) {
    try {
      // WL-074: chosen Arena agents run on the same coins, styles and depth.
      if (options.agents?.length) {
        await api.runArena({ ...options, strategies: [] });
        toast(`Arena run started for ${String(options.agents.length)} agent${options.agents.length === 1 ? "" : "s"}; see the Arena page.`);
      }
      await api.runBacktest({ ...options, agents: [] });
      toast("Backtest started. It fetches candles, then replays the chosen strategies.");
      setRunId(null);
      await refresh();
    } catch (err) {
      toast(`Backtest: ${(err as Error).message}`);
    }
  }

  const groups = data?.run?.params?.groups ?? {};
  // Combined: every group any run used, from the pooled results.
  const groupSet = combined ? new Set((data?.results ?? []).map((r) => r.coin_group)) : new Set(Object.keys(groups));
  const groupChips = ["all", ...GROUP_ORDER.filter((g) => groupSet.has(g))];
  const pooled = combined ? data?.pooled : null;
  const shownId = data?.run?.id ?? null;
  const latestId = data?.runs.find((r) => r.state === "success")?.id ?? null;

  return (
    <Stack spacing={2}>
      <PageHeader
        title="Backtests"
        subtitle="Bhalu trades: the strategies replayed on Binance candles with fees and slippage. Quick daily, or deep and random-coin runs set up in the wizard."
        actions={
          <ActionButton icon={<Tune />} primary busy={running} busyLabel="Running…" disabled={!data} onClick={() => setWizard(true)}>
            New backtest
          </ActionButton>
        }
      />
      {pooled ? (
        <Alert
          severity="info"
          action={
            <ActionButton compact onClick={() => setCombined(false)}>
              Show newest
            </ActionButton>
          }
        >
          All runs combined: {pooled.runs} runs, {pooled.trades.toLocaleString()} distinct trades. A trade two runs share counts once.
        </Alert>
      ) : null}
      {!combined && data?.run && shownId !== latestId ? (
        <Alert
          severity="info"
          action={
            <ActionButton compact onClick={() => setRunId(null)}>
              Show newest
            </ActionButton>
          }
        >
          Showing an older run: {describeOptions(data.run.params?.options)}.
        </Alert>
      ) : null}
      {data?.task.error ? <Alert severity="warning">Last run failed: {data.task.error}</Alert> : null}
      {running && data ? (
        <Card sx={{ p: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
            Backtest running
          </Typography>
          <RunProgress
            done={data.task.progress_done}
            total={data.task.progress_total}
            note={data.task.progress_note}
            startedAt={data.task.started_at}
          />
        </Card>
      ) : null}
      <KpiStrip
        tiles={[
          pooled
            ? { label: "Runs combined", value: String(pooled.runs), note: "Every finished run" }
            : {
                label: "Last run",
                value: data?.run ? <V value={fmtWhen(data.run.finished_at ?? data.run.started_at)} mono={false} /> : <Na reason="No backtest yet" />,
                note: data?.run ? `${describeOptions(data.run.params?.options)} · ${data.run.message ?? ""}` : "Runs daily at 15:45 PKT",
              },
          { label: "Trades", value: data?.run ? String(totalTrades) : <Na reason="No backtest yet" />, note: "All styles and groups" },
          {
            label: "Best average R",
            value: best ? <V value={fmtR(best.avg_r)} /> : <Na reason={`Needs ${String(min)} trades`} />,
            note: best ? `${names[best.strategy_id] ?? best.strategy_id} · ${STYLE_LABEL[best.style]}` : "Per strategy and style",
          },
          {
            label: "Costs",
            value: data?.run?.params?.fee_per_side !== undefined ? `${fmtFixed((data.run.params.fee_per_side ?? 0) * 100, 2) ?? ""}%` : <Na />,
            note: `fee per side, slippage ${fmtFixed((data?.run?.params?.slippage_per_side ?? 0) * 100, 2) ?? ""}%`,
          },
        ]}
      />
      <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", alignItems: "center" }} role="group" aria-label="Coin group">
        <TextField
          size="small"
          label="Strategy"
          value={strategyFilter}
          onChange={(e) => setStrategyFilter(e.target.value)}
          placeholder="Filter the table"
          sx={{ minWidth: 200 }}
        />
        {groupChips.map((g) => (
          <Chip
            key={g}
            label={GROUP_LABEL[g]}
            title={combined ? undefined : groups[g]?.join(", ")}
            color={group === g ? "primary" : "default"}
            variant={group === g ? "filled" : "outlined"}
            aria-pressed={group === g}
            onClick={() => setGroup(g)}
            sx={{ minHeight: { xs: 40, sm: 32 } }}
          />
        ))}
      </Stack>
      {error ? <Alert severity="warning">Backtests unavailable: {error}</Alert> : null}
      <Card>
        {!data && !error ? <Skeleton height={160} sx={{ mx: 2 }} /> : null}
        {data && !rows.length ? (
          <EmptyState icon={<ScienceOutlined />} text={data.run ? "No trades in this group." : "No backtest yet. Select New backtest."} />
        ) : null}
        {rows.length ? (
          <DataTable minWidth={880}>
            <TableHead>
              <TableRow>
                <TableCell>Strategy</TableCell>
                <TableCell>Style</TableCell>
                <TableCell align="right">Trades</TableCell>
                <TableCell align="right">Win rate</TableCell>
                <TableCell align="right">W / L / exp.</TableCell>
                <TableCell align="right">Avg R</TableCell>
                <TableCell align="right">Profit factor</TableCell>
                <TableCell align="right">Max DD</TableCell>
                <TableCell align="right">Total R</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={`${r.strategy_id}-${r.style}`} hover onClick={() => setCell(r)} sx={{ cursor: "pointer" }}>
                  <TableCell sx={{ fontWeight: 600 }}>{names[r.strategy_id] ?? r.strategy_id}</TableCell>
                  <TableCell>{STYLE_LABEL[r.style]}</TableCell>
                  <TableCell align="right">
                    <Num>{r.trades}</Num>
                  </TableCell>
                  <TableCell align="right">
                    {r.trades < min ? <Na reason={`too few trades (under ${String(min)})`} /> : <V value={fmtRate(r.win_rate)} />}
                  </TableCell>
                  <TableCell align="right">
                    <Num>
                      {r.wins} / {r.losses} / {r.expired}
                    </Num>
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtR(r.avg_r)} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtFixed(r.profit_factor)} reason="No losing trades" />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtR(r.max_drawdown_r ? -r.max_drawdown_r : r.max_drawdown_r, 1)} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtR(r.total_r, 1)} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </DataTable>
        ) : null}
      </Card>
      {data ? (
        <BacktestSearch active={active} names={names} version={data?.run?.id} />
      ) : null}
      {data ? (
        <RunsCard
          runs={data.runs}
          shownId={shownId}
          pooled={latestId !== null}
          combined={combined}
          onCombined={() => {
            setGroup("all");
            setCombined(true);
          }}
          onSelect={(id) => {
            setCombined(false);
            setRunId(id === latestId ? null : id);
          }}
        />
      ) : null}
      <Typography variant="caption" sx={{ color: "text.secondary" }}>
        Entry at the next candle's open after a signal; stop and target from ATR; a candle that touches both counts as a loss. Scalping
        uses 15m candles, day trading 1h, swing 4h. Win rate is the share of all trades that reached the target. Select a row for its
        trades and why the losers failed.
      </Typography>
      {cell ? <TradesDialog cell={cell} name={names[cell.strategy_id] ?? cell.strategy_id} runId={shownId} pooled={combined} onClose={() => setCell(null)} /> : null}
      {wizard && data ? (
        <BacktestWizard choices={data.choices} strategies={library} agents={agentList} onClose={() => setWizard(false)} onStart={start} />
      ) : null}
    </Stack>
  );
}
