import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import ArrowBack from "@mui/icons-material/ArrowBack";
import ScienceOutlined from "@mui/icons-material/ScienceOutlined";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, type BacktestRun, type BacktestTrade } from "../api";
import { ActionButton, EmptyState, KpiStrip, Na, PageHeader, V, type KpiTile } from "../components/ui";
import { fmtFixed, fmtPct, fmtPx, isNum } from "../lib/format";

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

export default function BacktestDetail({
  runId,
  onBack,
}: Readonly<{ runId: string; onBack: () => void }>) {
  const [run, setRun] = useState<BacktestRun | null>(null);
  const [trades, setTrades] = useState<BacktestTrade[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterStrategy, setFilterStrategy] = useState("");
  const [filterSymbol, setFilterSymbol] = useState("");
  const [filterOutcome, setFilterOutcome] = useState("");

  const load = useCallback(
    async (filters?: { strategy_id?: string; symbol?: string; outcome?: string }) => {
      setLoading(true);
      setErr(null);
      try {
        const res = await api.backtestRun(runId, {
          trades: true,
          strategy_id: filters?.strategy_id,
          symbol: filters?.symbol,
          outcome: filters?.outcome,
          limit: 1000,
        });
        setRun(res.run);
        setTrades(res.trades ?? []);
      } catch (e) {
        setRun(null);
        setTrades([]);
        setErr((e as Error).message);
      } finally {
        setLoading(false);
      }
    },
    [runId],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const params = (run?.params ?? {}) as {
    timeframe?: string;
    symbols?: string[];
    strategy_ids?: string[];
    bars?: number;
    step?: number;
    horizon_bars?: number;
    method?: string;
  };
  const summary = run?.summary;
  const overall = summary?.overall;
  const byStrategy = summary?.by_strategy ?? [];
  const byCoin = summary?.by_symbol ?? [];

  const kpis: KpiTile[] = useMemo(() => {
    if (!overall) {
      return [
        { label: "Trades", value: <Na reason="Loading" />, note: "Run" },
        { label: "Hit rate", value: <Na reason="Loading" />, note: "Run" },
        { label: "Avg R", value: <Na reason="Loading" />, note: "Run" },
        { label: "Max DD (R)", value: <Na reason="Loading" />, note: "Run" },
      ];
    }
    return [
      { label: "Trades", value: <V value={String(overall.n)} />, note: summary?.method ?? "walk_forward" },
      {
        label: "Hit rate",
        value: isNum(overall.hit_rate) ? <V value={fmtPct(overall.hit_rate * 100, 1)} /> : <Na reason="No closed" />,
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
  }, [overall, summary?.method]);

  if (err) {
    return (
      <Box>
        <PageHeader
          title="Backtest run"
          subtitle={err}
          actions={<ActionButton icon={<ArrowBack />} onClick={onBack}>Back</ActionButton>}
        />
      </Box>
    );
  }

  return (
    <Box>
      <PageHeader
        title={`Run ${runId}`}
        subtitle={
          loading
            ? "Loading…"
            : [
                summary?.timeframe ?? params.timeframe,
                (summary?.symbols ?? params.symbols ?? []).join(", ") || null,
                run?.created_at ? new Date(run.created_at).toLocaleString() : null,
                run?.status,
              ]
                .filter(Boolean)
                .join(" · ")
        }
        actions={
          <Stack direction="row" spacing={1}>
            <ActionButton icon={<ArrowBack />} onClick={onBack}>
              Back
            </ActionButton>
            <ActionButton
              onClick={() =>
                void load({
                  strategy_id: filterStrategy || undefined,
                  symbol: filterSymbol || undefined,
                  outcome: filterOutcome || undefined,
                })
              }
              disabled={loading}
            >
              Reload
            </ActionButton>
          </Stack>
        }
      />

      <Card sx={{ p: 2, mb: 2 }}>
        <Typography variant="h3" component="h3" sx={{ mb: 1 }}>
          Run settings (stored)
        </Typography>
        <Table size="small">
          <TableBody>
            <TableRow>
              <TableCell>Timeframe</TableCell>
              <TableCell>{summary?.timeframe ?? params.timeframe ?? <Na />}</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Coins</TableCell>
              <TableCell>{(summary?.symbols ?? params.symbols ?? []).join(", ") || <Na />}</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Strategies</TableCell>
              <TableCell>{(summary?.strategy_ids ?? params.strategy_ids ?? []).join(", ") || <Na />}</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Bars / step / holdout</TableCell>
              <TableCell>
                {String(summary?.bars ?? params.bars ?? "—")} / {String(summary?.step ?? params.step ?? "—")} /{" "}
                {String(summary?.horizon_bars ?? params.horizon_bars ?? "—")}
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Method</TableCell>
              <TableCell>{summary?.method ?? params.method ?? "walk_forward"}</TableCell>
            </TableRow>
            {summary?.errors?.length ? (
              <TableRow>
                <TableCell>Errors</TableCell>
                <TableCell>{summary.errors.join("; ")}</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Card>

      <Box sx={{ mb: 2 }}>
        <KpiStrip tiles={kpis} />
      </Box>

      <Box
        sx={{
          display: "grid",
          gap: 2,
          gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
          mb: 2,
        }}
      >
        <Card sx={{ p: 2, overflow: "auto" }}>
          <Typography variant="h3" component="h3" sx={{ mb: 1.5 }}>
            By strategy
          </Typography>
          {!byStrategy.length ? (
            <EmptyState text="No strategy rows." icon={<ScienceOutlined />} />
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Strategy</TableCell>
                  <TableCell align="right">N</TableCell>
                  <TableCell align="right">Hit</TableCell>
                  <TableCell align="right">Avg R</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {byStrategy.map((s) => (
                  <TableRow key={s.strategy_id}>
                    <TableCell>{s.strategy_label}</TableCell>
                    <TableCell align="right">{s.n}</TableCell>
                    <TableCell align="right">
                      {isNum(s.hit_rate) ? fmtPct(s.hit_rate * 100, 1) : <Na />}
                    </TableCell>
                    <TableCell align="right">{isNum(s.avg_r) ? fmtFixed(s.avg_r, 2) : <Na />}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
        <Card sx={{ p: 2, overflow: "auto" }}>
          <Typography variant="h3" component="h3" sx={{ mb: 1.5 }}>
            By coin
          </Typography>
          {!byCoin.length ? (
            <EmptyState text="No coin rows." icon={<ScienceOutlined />} />
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Symbol</TableCell>
                  <TableCell align="right">N</TableCell>
                  <TableCell align="right">Hit</TableCell>
                  <TableCell align="right">Avg R</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {byCoin.map((s) => (
                  <TableRow key={s.symbol}>
                    <TableCell>{s.symbol}</TableCell>
                    <TableCell align="right">{s.n}</TableCell>
                    <TableCell align="right">
                      {isNum(s.hit_rate) ? fmtPct(s.hit_rate * 100, 1) : <Na />}
                    </TableCell>
                    <TableCell align="right">{isNum(s.avg_r) ? fmtFixed(s.avg_r, 2) : <Na />}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      </Box>

      <Card sx={{ p: 2, overflow: "auto" }}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          sx={{ mb: 1.5, alignItems: { sm: "center" }, justifyContent: "space-between" }}
        >
          <Box>
            <Typography variant="h3" component="h3">
              Trade ledger
            </Typography>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              Why each strategy fired and why the hidden bars scored win, loss or expired.
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>Strategy</InputLabel>
              <Select label="Strategy" value={filterStrategy} onChange={(e) => setFilterStrategy(e.target.value)}>
                <MenuItem value="">All</MenuItem>
                {byStrategy.map((s) => (
                  <MenuItem key={s.strategy_id} value={s.strategy_id}>
                    {s.strategy_label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Coin</InputLabel>
              <Select label="Coin" value={filterSymbol} onChange={(e) => setFilterSymbol(e.target.value)}>
                <MenuItem value="">All</MenuItem>
                {byCoin.map((s) => (
                  <MenuItem key={s.symbol} value={s.symbol}>
                    {s.symbol}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Outcome</InputLabel>
              <Select label="Outcome" value={filterOutcome} onChange={(e) => setFilterOutcome(e.target.value)}>
                <MenuItem value="">All</MenuItem>
                <MenuItem value="win">Win</MenuItem>
                <MenuItem value="loss">Loss</MenuItem>
                <MenuItem value="expired">Expired</MenuItem>
              </Select>
            </FormControl>
            <ActionButton
              onClick={() =>
                void load({
                  strategy_id: filterStrategy || undefined,
                  symbol: filterSymbol || undefined,
                  outcome: filterOutcome || undefined,
                })
              }
            >
              Filter
            </ActionButton>
          </Stack>
        </Stack>
        {!trades.length ? (
          <EmptyState text="No trades for this filter." icon={<ScienceOutlined />} />
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Coin</TableCell>
                <TableCell>Strategy</TableCell>
                <TableCell>TF</TableCell>
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
                  <TableCell>{t.timeframe}</TableCell>
                  <TableCell>{t.side}</TableCell>
                  <TableCell align="right">{fmtPx(t.entry) ?? <Na />}</TableCell>
                  <TableCell align="right">{fmtPx(t.stop_loss) ?? <Na />}</TableCell>
                  <TableCell align="right">{fmtPx(t.take_profit) ?? <Na />}</TableCell>
                  <TableCell>{t.outcome ?? <Na />}</TableCell>
                  <TableCell align="right">{isNum(t.r_multiple) ? fmtFixed(t.r_multiple, 2) : <Na />}</TableCell>
                  <TableCell sx={{ maxWidth: 260, whiteSpace: "normal" }}>
                    {t.signal_reason ?? <Na reason="No reason stored" />}
                  </TableCell>
                  <TableCell sx={{ maxWidth: 200, whiteSpace: "normal" }}>{outcomeWhy(t)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </Box>
  );
}
