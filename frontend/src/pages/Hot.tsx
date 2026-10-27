import Autocomplete from "@mui/material/Autocomplete";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import LinearProgress from "@mui/material/LinearProgress";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import LocalFireDepartmentOutlined from "@mui/icons-material/LocalFireDepartmentOutlined";
import { useEffect, useState } from "react";
import { api, type HotCategory, type HotScanResponse } from "../api";
import { ActionButton, DataTable, EmptyState, KpiStrip, Na, Num, PageHeader, V } from "../components/ui";
import { fmtSigned } from "../lib/format";

const HOT_TFS = ["15m", "1h", "4h"] as const;
const TOP_NS = [5, 10, 20] as const;

function changeTone(pct: number | null | undefined): "success.main" | "error.main" | "text.secondary" {
  if (pct == null || Number.isNaN(pct)) return "text.secondary";
  if (pct > 0) return "success.main";
  if (pct < 0) return "error.main";
  return "text.secondary";
}

export default function Hot({
  onOpen,
}: Readonly<{ onOpen: (symbol: string) => void }>) {
  const [category, setCategory] = useState<HotCategory>("majors");
  const [topN, setTopN] = useState<number>(10);
  const [timeframe, setTimeframe] = useState<string>("1h");
  const [withAi, setWithAi] = useState(true);
  const [symbols, setSymbols] = useState<string[]>([]);
  const [coinQuery, setCoinQuery] = useState("");
  const [coinOptions, setCoinOptions] = useState<string[]>([]);
  const [coinSearching, setCoinSearching] = useState(false);
  const [data, setData] = useState<HotScanResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ask, setAsk] = useState("");
  const [askBusy, setAskBusy] = useState(false);
  const [askReply, setAskReply] = useState<string | null>(null);
  const [askError, setAskError] = useState<string | null>(null);

  useEffect(() => {
    const q = coinQuery.trim();
    if (q.length < 1) {
      setCoinOptions([]);
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
            .map((r) => r.symbol.replace("/", "").replace(".P", "").toUpperCase())
            .filter((s, i, a) => Boolean(s) && a.indexOf(s) === i);
          setCoinOptions(opts.length ? opts : [q.toUpperCase().replace("/", "")]);
        })
        .catch(() => {
          if (!cancelled) setCoinOptions([q.toUpperCase().replace("/", "")]);
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

  async function scan() {
    setBusy(true);
    setError(null);
    setAskReply(null);
    try {
      const res = await api.hotScan({
        category,
        top_n: topN,
        timeframe,
        symbols: symbols.length ? symbols : undefined,
        with_ai_brief: withAi,
      });
      setData(res);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function askAi() {
    if (!ask.trim()) return;
    setAskBusy(true);
    setAskError(null);
    try {
      const res = await api.hotAsk(ask.trim(), data);
      setAskReply(res.reply);
    } catch (err) {
      setAskError((err as Error).message);
    } finally {
      setAskBusy(false);
    }
  }

  const rows = data?.rows ?? [];
  const notScanned = <Na reason="Not scanned yet" />;

  let table: React.ReactNode;
  if (busy)
    table = (
      <Box sx={{ p: 2 }}>
        <Alert severity="info" variant="outlined" sx={{ mb: 2 }}>
          Scanning volatility. This can take a short while.
        </Alert>
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} height={40} />
        ))}
      </Box>
    );
  else if (error)
    table = (
      <Alert severity="warning" sx={{ m: 2 }}>
        Scan failed: {error}
      </Alert>
    );
  else if (!data)
    table = (
      <EmptyState
        text="Pick a category and scan for elevated volatility. Open winners on Desk for full analysis."
        icon={<LocalFireDepartmentOutlined />}
      />
    );
  else if (!rows.length) table = <EmptyState text="No hot pairs in this run." />;
  else
    table = (
      <DataTable minWidth={1240}>
        <TableHead>
          <TableRow>
            <TableCell>Pair</TableCell>
            <TableCell align="right">Hot</TableCell>
            <TableCell align="right">ATR%</TableCell>
            <TableCell align="right">BB width</TableCell>
            <TableCell align="right">24h range</TableCell>
            <TableCell align="right">Vol surge</TableCell>
            <TableCell align="right">24h chg</TableCell>
            <TableCell sx={{ minWidth: 220, maxWidth: 320 }}>AI note</TableCell>
            <TableCell align="right" sx={{ width: 88 }} />
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((r) => (
            <TableRow key={r.symbol} hover>
              <TableCell sx={{ whiteSpace: "nowrap" }}>
                <Num sx={{ fontWeight: 700 }}>{r.symbol}</Num>
              </TableCell>
              <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                {r.hot_score == null ? (
                  <Na reason={r.error ?? "No score"} />
                ) : (
                  <Stack direction="row" spacing={1} sx={{ alignItems: "center", justifyContent: "flex-end" }}>
                    <LinearProgress
                      variant="determinate"
                      value={Math.max(0, Math.min(100, r.hot_score))}
                      sx={{ width: 56, height: 6, borderRadius: 3 }}
                    />
                    <Num>{r.hot_score}</Num>
                  </Stack>
                )}
              </TableCell>
              <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                <V value={r.atr_pct == null ? null : `${r.atr_pct.toFixed(2)}%`} />
              </TableCell>
              <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                <V value={r.bandwidth == null ? null : r.bandwidth.toFixed(4)} />
              </TableCell>
              <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                <V value={r.range_24h_pct == null ? null : `${r.range_24h_pct.toFixed(2)}%`} />
              </TableCell>
              <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                <V value={r.vol_surge == null ? null : `${r.vol_surge.toFixed(2)}x`} />
              </TableCell>
              <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                {r.change_24h_pct == null ? (
                  <Na reason="No 24h change" />
                ) : (
                  <Num sx={{ color: changeTone(r.change_24h_pct) }}>{fmtSigned(r.change_24h_pct)}%</Num>
                )}
              </TableCell>
              <TableCell sx={{ minWidth: 220, maxWidth: 320, whiteSpace: "normal" }}>
                {r.ai_note ? (
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    title={r.ai_note}
                    sx={{ overflowWrap: "anywhere", display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}
                  >
                    {r.ai_note}
                  </Typography>
                ) : (
                  <Na reason={data.provider ? "No note" : "AI brief off or offline"} />
                )}
              </TableCell>
              <TableCell align="right" sx={{ width: 88, whiteSpace: "nowrap", verticalAlign: "middle" }}>
                <Button
                  size="small"
                  variant="outlined"
                  color="inherit"
                  sx={{ borderColor: "divider" }}
                  onClick={() => onOpen(r.symbol)}
                >
                  Open
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </DataTable>
    );

  return (
    <Stack spacing={2}>
      <PageHeader
        title="Hot"
        subtitle="Find elevated or expanding volatility, then open pairs on Desk for deep analysis."
        actions={
          <ActionButton primary busy={busy} busyLabel="Scanning…" onClick={() => void scan()}>
            Scan
          </ActionButton>
        }
      />

      <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ alignItems: { md: "center" }, flexWrap: "wrap" }}>
        <ToggleButtonGroup
          exclusive
          size="small"
          value={category}
          onChange={(_, v: HotCategory | null) => {
            if (v) setCategory(v);
          }}
        >
          <ToggleButton value="majors">Majors</ToggleButton>
          <ToggleButton value="mid">Mid</ToggleButton>
          <ToggleButton value="alts">Alts</ToggleButton>
          <ToggleButton value="all">All</ToggleButton>
        </ToggleButtonGroup>
        <Select size="small" value={topN} onChange={(e) => setTopN(Number(e.target.value))} sx={{ minWidth: 100 }}>
          {TOP_NS.map((n) => (
            <MenuItem key={n} value={n}>
              Top {n}
            </MenuItem>
          ))}
        </Select>
        <Select
          size="small"
          value={timeframe}
          onChange={(e) => setTimeframe(String(e.target.value))}
          sx={{ minWidth: 100 }}
        >
          {HOT_TFS.map((tf) => (
            <MenuItem key={tf} value={tf}>
              {tf}
            </MenuItem>
          ))}
        </Select>
        <FormControlLabel
          control={<Checkbox checked={withAi} onChange={(e) => setWithAi(e.target.checked)} size="small" />}
          label="With AI brief"
        />
      </Stack>

      <Autocomplete
        multiple
        freeSolo
        options={coinOptions}
        value={symbols}
        loading={coinSearching}
        onChange={(_, v) =>
          setSymbols(
            v
              .map((s) => String(s).toUpperCase().replace("/", "").replace(".P", ""))
              .filter(Boolean),
          )
        }
        onInputChange={(_, v) => setCoinQuery(v)}
        renderInput={(params) => (
          <TextField
            {...params}
            size="small"
            label="Custom symbols (optional)"
            placeholder="Search to override universe"
          />
        )}
      />

      <KpiStrip
        tiles={[
          {
            label: "Scanned",
            value: data ? String(data.scanned) : notScanned,
            note: data ? `Category ${data.category}` : "Pairs in the universe",
          },
          {
            label: "Hottest",
            value: data?.hottest ?? notScanned,
            note: data ? `Top of ${String(data.top_n)}` : "Highest hot score",
          },
          {
            label: "Median ATR%",
            value: data?.median_atr_pct == null ? notScanned : `${data.median_atr_pct.toFixed(2)}%`,
            note: data ? `On ${data.timeframe}` : "Among ranked rows",
          },
          {
            label: "AI",
            value: data ? (data.provider ?? "local only") : notScanned,
            note: withAi ? "Brief on top N" : "Brief off",
          },
        ]}
      />

      <Box sx={{ border: 1, borderColor: "divider", borderRadius: 1, overflow: "hidden" }}>{table}</Box>

      <Stack spacing={1} sx={{ border: 1, borderColor: "divider", borderRadius: 1, p: 2 }}>
        <Typography variant="subtitle2">Ask AI</Typography>
        <Typography variant="body2" color="text.secondary">
          Question about the latest scan table (no full Desk snapshot per coin).
        </Typography>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
          <TextField
            size="small"
            fullWidth
            value={ask}
            onChange={(e) => setAsk(e.target.value)}
            placeholder="Which of these deserve a desk look first?"
            disabled={askBusy}
          />
          <Button variant="outlined" onClick={() => void askAi()} disabled={askBusy || !ask.trim()}>
            {askBusy ? "Asking…" : "Ask"}
          </Button>
        </Stack>
        {askError ? (
          <Alert severity="warning">{askError}</Alert>
        ) : null}
        {askReply ? (
          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
            {askReply}
          </Typography>
        ) : null}
      </Stack>
    </Stack>
  );
}
