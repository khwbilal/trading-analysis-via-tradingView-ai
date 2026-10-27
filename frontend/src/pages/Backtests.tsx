import Autocomplete from "@mui/material/Autocomplete";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Checkbox from "@mui/material/Checkbox";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import ListItemText from "@mui/material/ListItemText";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import ScienceOutlined from "@mui/icons-material/ScienceOutlined";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  api,
  type BacktestRankings,
  type BacktestRun,
  type BacktestTrade,
  type StrategyInfo,
} from "../api";
import { ActionButton, EmptyState, KpiStrip, Na, PageHeader, V, type KpiTile } from "../components/ui";
import { fmtFixed, fmtPct, fmtPx, isNum } from "../lib/format";

const COIN_SUGGESTIONS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT"];
const BACKTEST_TFS = ["15m", "30m", "1h", "2h", "4h", "1d"] as const;

const OUTCOME_WHY: Record<string, string> = {
  stop: "Stop hit first on hidden bars",
  same_bar_both: "Stop and target in same bar (counted as loss)",
  horizon: "Neither stop nor target within the holdout window",
  no_hidden: "No hidden bars to score",
};

function outcomeWhy(t: BacktestTrade): string {
  if (t.outcome === "win") return "Target hit first on hidden bars";
  if (t.failure_tag && OUTCOME_WHY[t.failure_tag]) return OUTCOME_WHY[t.failure_tag];
  return t.failure_tag ?? "—";
}

function ChartCard({ title, children }: Readonly<{ title: string; children: React.ReactNode }>) {
  return (
    <Card sx={{ p: 2, minWidth: 0, height: "100%", display: "flex", flexDirection: "column" }}>
      <Typography variant="h3" component="h3" sx={{ mb: 1.5 }}>
        {title}
      </Typography>
      <Box sx={{ flex: 1, minHeight: 240, width: "100%" }}>{children}</Box>
    </Card>
  );
}

export default function Backtests({
  active,
  onOpenRun,
}: Readonly<{ active: boolean; onOpenRun?: (id: string) => void }>) {
  const theme = useTheme();
  const [rankings, setRankings] = useState<BacktestRankings | null>(null);
  const [runs, setRuns] = useState<BacktestRun[]>([]);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [symbols, setSymbols] = useState<string[]>(["BTCUSDT", "ETHUSDT"]);
  const [coinQuery, setCoinQuery] = useState("");
  const [coinOptions, setCoinOptions] = useState<string[]>([...COIN_SUGGESTIONS]);
  const [coinSearching, setCoinSearching] = useState(false);
  const [strategyIds, setStrategyIds] = useState<string[]>(["all"]);
  const [bars, setBars] = useState(220);
  const [step, setStep] = useState(12);
  const [timeframe, setTimeframe] = useState<string>("1h");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<BacktestRun | null>(null);
  const [trades, setTrades] = useState<BacktestTrade[]>([]);
  const [tradeFilterStrategy, setTradeFilterStrategy] = useState("");
  const [tradeFilterSymbol, setTradeFilterSymbol] = useState("");
  const [tradeFilterOutcome, setTradeFilterOutcome] = useState("");

  const primary = theme.palette.primary.main;
  const win = theme.palette.success.main;
  const loss = theme.palette.error.main;
  const grid = theme.palette.divider;
  const textSec = theme.palette.text.secondary;

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [r, list, cats] = await Promise.all([
        api.backtestRankings("custom"),
        api.backtestRuns(),
        api.strategies(),
      ]);
      setRankings(r);
      setRuns(list.runs);
      setStrategies(cats.strategies);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!active) return;
    refresh().catch(() => undefined);
  }, [active, refresh]);

  useEffect(() => {
    const q = coinQuery.trim();
    if (q.length < 1) {
      setCoinOptions([...COIN_SUGGESTIONS]);
      setCoinSearching(false);
      return;
    }
    let cancelled = false;
    const timer = window.setTimeout(() => {
      setCoinSearching(true);
      api
        .searchSymbols(q, "BINANCE")
        .then((res) => {
          if (cancelled) return;
          const opts = res.results
            .filter((r) => {
              const t = String(r.type ?? "crypto").toLowerCase();
              return t === "crypto" || /USDT|USDC/i.test(r.symbol);
            })
            .map((r) => r.symbol.replace("/", "").replace(".P", "").toUpperCase())
            .filter((s, i, a) => Boolean(s) && a.indexOf(s) === i);
          setCoinOptions(opts.length ? opts : [q.toUpperCase().replace("/", "").replace(".P", "")]);
        })
        .catch(() => {
          if (!cancelled) setCoinOptions([q.toUpperCase().replace("/", "").replace(".P", "")]);
        })
        .finally(() => {
          if (!cancelled) setCoinSearching(false);
        });
    }, 160);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [coinQuery]);

  const onStrategyChange = (next: string[]) => {
    if (next.includes("all") && !strategyIds.includes("all")) {
      setStrategyIds(["all"]);
      return;
    }
    setStrategyIds(next.filter((id) => id !== "all"));
  };

  const loadTrades = useCallback(
    async (runId: string, filters?: { strategy_id?: string; symbol?: string; outcome?: string }) => {
      const res = await api.backtestRun(runId, {
        trades: true,
        strategy_id: filters?.strategy_id || undefined,
        symbol: filters?.symbol || undefined,
        outcome: filters?.outcome || undefined,
        limit: 500,
      });
      setTrades(res.trades ?? []);
    },
    [],
  );

  const onRun = async () => {
    if (!symbols.length) {
      setError("Pick at least one coin");
      return;
    }
    setRunning(true);
    setError(null);
    try {
      const run = await api.runBacktest({
        mode: "custom",
        symbols,
        strategy_ids: strategyIds.length ? strategyIds : ["all"],
        bars,
        step,
        timeframe,
      });
      setLastRun(run);
      setTradeFilterStrategy("");
      setTradeFilterSymbol("");
      setTradeFilterOutcome("");
      await loadTrades(run.id);
      await refresh();
      onOpenRun?.(run.id);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setRunning(false);
    }
  };

  const applyTradeFilters = async () => {
    if (!lastRun?.id) return;
    try {
      await loadTrades(lastRun.id, {
        strategy_id: tradeFilterStrategy || undefined,
        symbol: tradeFilterSymbol || undefined,
        outcome: tradeFilterOutcome || undefined,
      });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const rows = lastRun?.summary?.by_strategy ?? rankings?.strategies ?? [];
  const byCoin = lastRun?.summary?.by_symbol ?? [];
  const chartData = useMemo(
    () =>
      rows.map((s) => ({
        id: s.strategy_id,
        label: s.strategy_label,
        hit: isNum(s.hit_rate) ? Math.round(s.hit_rate * 1000) / 10 : 0,
        avg_r: isNum(s.avg_r) ? s.avg_r : 0,
        n: s.n,
      })),
    [rows],
  );

  const overall = lastRun?.summary?.overall ?? runs[0]?.summary?.overall;
  const kpis: KpiTile[] = useMemo(() => {
    if (!overall) {
      return [
        { label: "Trades", value: <Na reason="No run yet" />, note: "Walk-forward" },
        { label: "Hit rate", value: <Na reason="No run yet" />, note: "Hidden bars" },
        { label: "Avg R", value: <Na reason="No run yet" />, note: "Hidden bars" },
        { label: "Max DD (R)", value: <Na reason="No run yet" />, note: "Hidden bars" },
      ];
    }
    return [
      {
        label: "Trades",
        value: isNum(overall.n) ? <V value={String(overall.n)} /> : <Na />,
        note: lastRun?.summary?.method === "walk_forward" ? "Walk-forward holdout" : "Latest run",
      },
      {
        label: "Hit rate",
        value: isNum(overall.hit_rate) ? <V value={fmtPct(overall.hit_rate * 100, 1)} /> : <Na reason="No closed trades" />,
        note: "Wins among decided",
      },
      {
        label: "Avg R",
        value: isNum(overall.avg_r) ? <V value={fmtFixed(overall.avg_r, 2)} /> : <Na />,
        note: "Including expired",
      },
      {
        label: "Max DD (R)",
        value: isNum(overall.max_drawdown_r) ? <V value={fmtFixed(overall.max_drawdown_r, 2)} /> : <Na />,
        note: "Equity peak to trough",
      },
    ];
  }, [overall, lastRun]);

  return (
    <Box>
      <PageHeader
        title="Backtests"
        subtitle="Pick coins, strategies and timeframe. The engine sees only past candles on that tape, places a plan, then scores it on the hidden future bars. Every run and trade is stored."
        actions={
          <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", alignItems: "center" }}>
            <ActionButton primary busy={running} onClick={() => void onRun()}>
              Run walk-forward
            </ActionButton>
            <ActionButton onClick={() => void refresh()} disabled={loading || running}>
              Refresh
            </ActionButton>
          </Stack>
        }
      />

      <Card sx={{ p: 2, mb: 2 }}>
        <Stack spacing={2}>
          <Autocomplete
            multiple
            freeSolo
            filterOptions={(x) => x}
            options={coinOptions}
            value={symbols}
            inputValue={coinQuery}
            onInputChange={(_e, v, reason) => {
              if (reason !== "reset") setCoinQuery(v);
            }}
            loading={coinSearching}
            loadingText="Searching catalogue…"
            noOptionsText={coinQuery.trim() ? "No catalogue match. Press Enter to use this ticker." : "Type to search the instrument catalogue"}
            onChange={(_e, v) =>
              setSymbols(
                v
                  .map((x) => String(x).trim().toUpperCase().replace("/", "").replace(".P", ""))
                  .filter(Boolean)
                  .filter((s, i, a) => a.indexOf(s) === i),
              )
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Coins"
                placeholder="Search pairs (same catalogue as Desk)"
                helperText="Searches Binance instruments. Majors show when empty; type LINK, PEPE, ARB, etc."
              />
            )}
          />
          <FormControl fullWidth size="small">
            <InputLabel id="bt-strat-label">Strategies</InputLabel>
            <Select
              labelId="bt-strat-label"
              multiple
              label="Strategies"
              value={strategyIds}
              onChange={(e) => onStrategyChange(typeof e.target.value === "string" ? e.target.value.split(",") : e.target.value)}
              renderValue={(selected) => (selected.includes("all") ? "All strategies" : selected.join(", "))}
            >
              <MenuItem value="all">
                <Checkbox checked={strategyIds.includes("all")} />
                <ListItemText primary="All strategies" />
              </MenuItem>
              {strategies.map((s) => (
                <MenuItem key={s.id} value={s.id} disabled={strategyIds.includes("all")}>
                  <Checkbox checked={strategyIds.includes("all") || strategyIds.includes(s.id)} />
                  <ListItemText primary={s.label} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Stack direction="row" spacing={2} useFlexGap sx={{ flexWrap: "wrap" }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel id="bt-tf-label">Timeframe</InputLabel>
              <Select
                labelId="bt-tf-label"
                label="Timeframe"
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
              >
                {BACKTEST_TFS.map((tf) => (
                  <MenuItem key={tf} value={tf}>
                    {tf}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Bars"
              type="number"
              size="small"
              value={bars}
              onChange={(e) => setBars(Math.max(80, Math.min(1000, Number(e.target.value) || 220)))}
              sx={{ width: 120 }}
              helperText="History length"
            />
            <TextField
              label="Step"
              type="number"
              size="small"
              value={step}
              onChange={(e) => setStep(Math.max(1, Math.min(48, Number(e.target.value) || 12)))}
              sx={{ width: 120 }}
              helperText="Bars between decisions"
            />
          </Stack>
        </Stack>
      </Card>

      {runs.length ? (
        <Card sx={{ p: 2, mb: 2, overflow: "auto" }}>
          <Typography variant="h3" component="h3" sx={{ mb: 1 }}>
            Saved runs
          </Typography>
          <Typography variant="caption" sx={{ color: "text.secondary", display: "block", mb: 1.5 }}>
            Open a run for its full detail page (settings, rankings and trade ledger).
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Run</TableCell>
                <TableCell>When</TableCell>
                <TableCell>TF</TableCell>
                <TableCell>Coins</TableCell>
                <TableCell align="right">Trades</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right" />
              </TableRow>
            </TableHead>
            <TableBody>
              {runs.map((r) => {
                const p = r.params as { timeframe?: string; symbols?: string[] } | null | undefined;
                const tf = r.summary?.timeframe ?? p?.timeframe ?? "—";
                const coins = (r.summary?.symbols ?? p?.symbols ?? []).slice(0, 4).join(", ") || "—";
                return (
                  <TableRow key={r.id} hover sx={{ cursor: onOpenRun ? "pointer" : undefined }} onClick={() => onOpenRun?.(r.id)}>
                    <TableCell>{r.id}</TableCell>
                    <TableCell>{r.created_at ? new Date(r.created_at).toLocaleString() : "—"}</TableCell>
                    <TableCell>{tf}</TableCell>
                    <TableCell>{coins}</TableCell>
                    <TableCell align="right">{r.summary?.n_trades ?? "—"}</TableCell>
                    <TableCell>{r.status}</TableCell>
                    <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                      <ActionButton compact onClick={() => onOpenRun?.(r.id)}>
                        Open
                      </ActionButton>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Card>
      ) : null}

      {error ? (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      ) : null}

      <Box sx={{ mb: 2 }}>
        <KpiStrip tiles={kpis} />
      </Box>

      {loading && !rankings && !lastRun ? (
        <Skeleton variant="rounded" height={320} />
      ) : !rows.length ? (
        <EmptyState
          text="No walk-forward results yet. Pick coins and strategies, then run. Future bars stay hidden from the signal engine."
          icon={<ScienceOutlined />}
        />
      ) : (
        <Box
          sx={{
            display: "grid",
            gap: 2,
            gridTemplateColumns: { xs: "1fr", lg: "1.2fr 1fr" },
            alignItems: "stretch",
          }}
        >
          <Stack spacing={2}>
            <Card sx={{ p: 2, overflow: "auto" }}>
              <Typography variant="h3" component="h3" sx={{ mb: 1.5 }}>
                By strategy
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Strategy</TableCell>
                    <TableCell align="right">N</TableCell>
                    <TableCell align="right">Hit rate</TableCell>
                    <TableCell align="right">Avg R</TableCell>
                    <TableCell align="right">PF</TableCell>
                    <TableCell align="right">Max DD</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((s) => (
                    <TableRow key={s.strategy_id}>
                      <TableCell>{s.strategy_label}</TableCell>
                      <TableCell align="right">{s.n}</TableCell>
                      <TableCell align="right">
                        {isNum(s.hit_rate) ? fmtPct(s.hit_rate * 100, 1) : <Na reason="No closed" />}
                      </TableCell>
                      <TableCell align="right">{isNum(s.avg_r) ? fmtFixed(s.avg_r, 2) : <Na />}</TableCell>
                      <TableCell align="right">
                        {isNum(s.profit_factor) ? fmtFixed(s.profit_factor, 2) : <Na reason="n/a" />}
                      </TableCell>
                      <TableCell align="right">
                        {isNum(s.max_drawdown_r) ? fmtFixed(s.max_drawdown_r, 2) : <Na />}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
            {byCoin.length ? (
              <Card sx={{ p: 2, overflow: "auto" }}>
                <Typography variant="h3" component="h3" sx={{ mb: 1.5 }}>
                  By coin
                </Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell align="right">N</TableCell>
                      <TableCell align="right">Hit rate</TableCell>
                      <TableCell align="right">Avg R</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {byCoin.map((s) => (
                      <TableRow key={s.symbol}>
                        <TableCell>{s.symbol}</TableCell>
                        <TableCell align="right">{s.n}</TableCell>
                        <TableCell align="right">
                          {isNum(s.hit_rate) ? fmtPct(s.hit_rate * 100, 1) : <Na reason="No closed" />}
                        </TableCell>
                        <TableCell align="right">{isNum(s.avg_r) ? fmtFixed(s.avg_r, 2) : <Na />}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Card>
            ) : null}
          </Stack>

          <Stack spacing={2}>
            <ChartCard title="Hit rate by strategy">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
                  <CartesianGrid stroke={grid} strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fill: textSec, fontSize: 11 }} angle={-25} textAnchor="end" interval={0} height={60} />
                  <YAxis tick={{ fill: textSec, fontSize: 11 }} unit="%" />
                  <Tooltip />
                  <Bar dataKey="hit" name="Hit %">
                    {chartData.map((d) => (
                      <Cell key={d.id} fill={d.hit >= 50 ? win : loss} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
            <ChartCard title="Average R by strategy">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
                  <CartesianGrid stroke={grid} strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fill: textSec, fontSize: 11 }} angle={-25} textAnchor="end" interval={0} height={60} />
                  <YAxis tick={{ fill: textSec, fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="avg_r" name="Avg R" fill={primary} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </Stack>
        </Box>
      )}

      {lastRun?.id ? (
        <Card sx={{ p: 2, mt: 2, overflow: "auto" }}>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 1.5, alignItems: { sm: "center" }, justifyContent: "space-between" }}>
            <Box>
              <Typography variant="h3" component="h3">
                Trade ledger
              </Typography>
              <Typography variant="caption" sx={{ color: "text.secondary" }}>
                Each row is one plan: why the strategy fired, levels, then what the hidden bars did.
              </Typography>
            </Box>
            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
              <FormControl size="small" sx={{ minWidth: 140 }}>
                <InputLabel>Strategy</InputLabel>
                <Select
                  label="Strategy"
                  value={tradeFilterStrategy}
                  onChange={(e) => setTradeFilterStrategy(e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  {(lastRun.summary?.by_strategy ?? []).map((s) => (
                    <MenuItem key={s.strategy_id} value={s.strategy_id}>
                      {s.strategy_label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Coin</InputLabel>
                <Select label="Coin" value={tradeFilterSymbol} onChange={(e) => setTradeFilterSymbol(e.target.value)}>
                  <MenuItem value="">All</MenuItem>
                  {(lastRun.summary?.by_symbol ?? []).map((s) => (
                    <MenuItem key={s.symbol} value={s.symbol}>
                      {s.symbol}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Outcome</InputLabel>
                <Select label="Outcome" value={tradeFilterOutcome} onChange={(e) => setTradeFilterOutcome(e.target.value)}>
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="win">Win</MenuItem>
                  <MenuItem value="loss">Loss</MenuItem>
                  <MenuItem value="expired">Expired</MenuItem>
                </Select>
              </FormControl>
              <ActionButton onClick={() => void applyTradeFilters()}>Filter</ActionButton>
            </Stack>
          </Stack>
          {!trades.length ? (
            <EmptyState text="No trades in this filter. Run a walk-forward or clear filters." icon={<ScienceOutlined />} />
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Coin</TableCell>
                  <TableCell>Strategy</TableCell>
                  <TableCell>Side</TableCell>
                  <TableCell align="right">Entry</TableCell>
                  <TableCell align="right">Stop</TableCell>
                  <TableCell align="right">Target</TableCell>
                  <TableCell>Outcome</TableCell>
                  <TableCell align="right">R</TableCell>
                  <TableCell>Why signal</TableCell>
                  <TableCell>Why result</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {trades.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell>{t.symbol}</TableCell>
                    <TableCell>{t.strategy_id}</TableCell>
                    <TableCell>{t.side}</TableCell>
                    <TableCell align="right">{fmtPx(t.entry) ?? <Na />}</TableCell>
                    <TableCell align="right">{fmtPx(t.stop_loss) ?? <Na />}</TableCell>
                    <TableCell align="right">{fmtPx(t.take_profit) ?? <Na />}</TableCell>
                    <TableCell>{t.outcome ?? <Na />}</TableCell>
                    <TableCell align="right">{isNum(t.r_multiple) ? fmtFixed(t.r_multiple, 2) : <Na />}</TableCell>
                    <TableCell sx={{ maxWidth: 280, whiteSpace: "normal" }}>
                      {t.signal_reason ?? <Na reason="No reason stored (older run)" />}
                    </TableCell>
                    <TableCell sx={{ maxWidth: 220, whiteSpace: "normal" }}>{outcomeWhy(t)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      ) : null}
    </Box>
  );
}
