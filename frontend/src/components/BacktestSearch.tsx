import MenuItem from "@mui/material/MenuItem";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import Search from "@mui/icons-material/Search";
import { useEffect, useState } from "react";
import { api, type BacktestTrade } from "../api";
import { GLYPH, GROUP_LABEL, STYLE_LABEL, biasClass, fmtPx, fmtR } from "../lib/format";
import { ActionButton, DataTable, EmptyState, Num, Pill, SectionCard, StatusPill, V } from "./ui";
import { usePref } from "../lib/storage";

const PAGE = 50;

/** WL-077: search every finished run's distinct trades by coin or stock, strategy, style, group, side,
 * result and entry date. */
export default function BacktestSearch({ active, names, version }: Readonly<{ active: boolean; names: Record<string, string>; version: unknown }>) {
  const [symbol, setSymbol] = usePref("cca_bt_symbol", ""); // WL-101: kept per browser
  const [strategy, setStrategy] = usePref("cca_bt_strategy", "");
  const [style, setStyle] = usePref("cca_bt_style", "");
  const [group, setGroup] = usePref("cca_bt_group", "");
  const [outcome, setOutcome] = usePref("cca_bt_outcome", "");
  const [from, setFrom] = usePref("cca_bt_from", "");
  const [to, setTo] = usePref("cca_bt_to", "");
  const [offset, setOffset] = usePref("cca_bt_offset", 0);
  const [found, setFound] = useState<{ trades: BacktestTrade[]; total: number } | null>(null);

  useEffect(() => {
    if (!active) return;
    const id = setTimeout(() => {
      api
        .backtestSearch({ symbol, strategy, style, group, outcome, date_from: from, date_to: to }, PAGE, offset)
        .then((r) => setFound({ trades: r.trades, total: r.total }))
        .catch(() => setFound({ trades: [], total: 0 }));
    }, 300);
    return () => clearTimeout(id);
  }, [active, symbol, strategy, style, group, outcome, from, to, offset, version]);

  function on<T>(set: (v: T) => void): (v: T) => void {
    return (v: T) => {
      setOffset(0);
      set(v);
    };
  }

  return (
    <SectionCard
      title="Search trades (all runs combined)"
      icon={<Search />}
      right={
        found ? (
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            {found.total.toLocaleString()} found
          </Typography>
        ) : null
      }
      noPadding
    >
      <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ p: 2, flexWrap: "wrap", rowGap: 1.5 }}>
        <TextField label="Coin or stock" size="small" value={symbol} onChange={(e) => on(setSymbol)(e.target.value)} placeholder="SOL, TSLA" />
        <TextField label="Strategy" size="small" value={strategy} onChange={(e) => on(setStrategy)(e.target.value)} placeholder="ema, gujjar" />
        <TextField select label="Style" size="small" value={style} onChange={(e) => on(setStyle)(e.target.value)} sx={{ minWidth: 130 }}>
          <MenuItem value="">All styles</MenuItem>
          {Object.entries(STYLE_LABEL).map(([k, label]) => (
            <MenuItem key={k} value={k}>
              {label}
            </MenuItem>
          ))}
        </TextField>
        <TextField select label="Group" size="small" value={group} onChange={(e) => on(setGroup)(e.target.value)} sx={{ minWidth: 140 }}>
          {Object.entries(GROUP_LABEL).map(([k, label]) => (
            <MenuItem key={k} value={k === "all" ? "" : k}>
              {label}
            </MenuItem>
          ))}
        </TextField>
        <TextField select label="Result" size="small" value={outcome} onChange={(e) => on(setOutcome)(e.target.value)} sx={{ minWidth: 120 }}>
          <MenuItem value="">All</MenuItem>
          <MenuItem value="win">▲ Win</MenuItem>
          <MenuItem value="loss">▼ Loss</MenuItem>
          <MenuItem value="expired">● Expired</MenuItem>
        </TextField>
        <TextField label="From" type="date" size="small" value={from} onChange={(e) => on(setFrom)(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
        <TextField label="To" type="date" size="small" value={to} onChange={(e) => on(setTo)(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
      </Stack>
      {found === null ? <Skeleton height={120} sx={{ mx: 2 }} /> : null}
      {found && !found.trades.length ? <EmptyState text="No trades match." /> : null}
      {found?.trades.length ? (
        <DataTable minWidth={1040} maxHeight={520}>
          <TableHead>
            <TableRow>
              <TableCell>Entry</TableCell>
              <TableCell>Strategy</TableCell>
              <TableCell>Pair</TableCell>
              <TableCell>Style</TableCell>
              <TableCell>Side</TableCell>
              <TableCell align="right">Entry price</TableCell>
              <TableCell align="right">Stop</TableCell>
              <TableCell align="right">Target</TableCell>
              <TableCell>Result</TableCell>
              <TableCell align="right">R</TableCell>
              <TableCell>Why it lost</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {found.trades.map((t) => {
              const cls = biasClass(t.side);
              return (
                <TableRow key={t.id} hover>
                  <TableCell sx={{ whiteSpace: "nowrap" }}>
                    <Num>{new Date(t.entry_time).toISOString().slice(0, 16).replace("T", " ")}</Num>
                  </TableCell>
                  <TableCell>{names[t.strategy_id] ?? t.strategy_id}</TableCell>
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
                  <TableCell align="right">
                    <V value={fmtPx(t.entry)} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtPx(t.stop)} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtPx(t.target)} />
                  </TableCell>
                  <TableCell>
                    <StatusPill status={t.outcome} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtR(t.r_multiple)} />
                  </TableCell>
                  <TableCell sx={{ color: "text.secondary" }}>{t.failure_tag ?? ""}</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </DataTable>
      ) : null}
      {found && found.total > PAGE ? (
        <Stack direction="row" spacing={1} sx={{ p: 1.5, justifyContent: "flex-end", alignItems: "center" }}>
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            {String(offset + 1)} to {String(Math.min(offset + PAGE, found.total))} of {found.total.toLocaleString()}
          </Typography>
          <ActionButton compact disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
            Newer
          </ActionButton>
          <ActionButton compact disabled={offset + PAGE >= found.total} onClick={() => setOffset(offset + PAGE)}>
            Older
          </ActionButton>
        </Stack>
      ) : null}
    </SectionCard>
  );
}
