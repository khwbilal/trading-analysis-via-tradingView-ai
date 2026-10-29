import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import ReceiptLongOutlined from "@mui/icons-material/ReceiptLongOutlined";
import Sync from "@mui/icons-material/Sync";
import { useCallback, useEffect, useState } from "react";
import { api, type PaperResponse, type PaperStats, type PositionsResponse } from "../api";
import PositionsCard from "../components/PositionsCard";
import { useFeedback } from "../components/feedback";
import { ActionButton, DataTable, EmptyState, KpiStrip, Na, Num, PageHeader, Pill, SectionCard, StatusPill, V } from "../components/ui";
import { GLYPH, GROUP_LABEL, STYLE_LABEL, biasClass, fmtDuration, fmtPx, fmtR, fmtRate, fmtWhen } from "../lib/format";

function StatsTable({ title, rows, label }: Readonly<{ title: string; rows: [string, PaperStats][]; label: (k: string) => string }>) {
  return (
    <SectionCard title={title} noPadding>
      {rows.length ? (
        <DataTable minWidth={460} maxHeight="none">
          <TableHead>
            <TableRow>
              <TableCell>{title.split(" ").pop()}</TableCell>
              <TableCell align="right">Open</TableCell>
              <TableCell align="right">Won</TableCell>
              <TableCell align="right">Lost</TableCell>
              <TableCell align="right">Expired</TableCell>
              <TableCell align="right">Win rate</TableCell>
              <TableCell align="right">Total R</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map(([k, s]) => (
              <TableRow key={k}>
                <TableCell sx={{ fontWeight: 600 }}>{label(k)}</TableCell>
                <TableCell align="right">
                  <Num>{s.open}</Num>
                </TableCell>
                <TableCell align="right">
                  <Num>{s.won}</Num>
                </TableCell>
                <TableCell align="right">
                  <Num>{s.lost}</Num>
                </TableCell>
                <TableCell align="right">
                  <Num>{s.expired}</Num>
                </TableCell>
                <TableCell align="right">
                  <V value={fmtRate(s.win_rate)} reason="No closed trades yet" />
                </TableCell>
                <TableCell align="right">
                  <V value={fmtR(s.total_r, 1)} reason="No closed trades yet" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </DataTable>
      ) : (
        <EmptyState text="No trades yet." />
      )}
    </SectionCard>
  );
}

/** Paper trades opened from the daily picks and closed by the 4-hourly check (WL-038). */
export default function Paper({ active }: Readonly<{ active: boolean }>) {
  const { toast } = useFeedback();
  const [data, setData] = useState<PaperResponse | null>(null);
  const [positions, setPositions] = useState<PositionsResponse | null>(null);
  const [names, setNames] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [paper, pos] = await Promise.all([api.paper(), api.positions().catch(() => null)]);
      setData(paper);
      setPositions(pos);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    if (!active) return;
    load().catch(() => undefined);
    if (!Object.keys(names).length) {
      api
        .strategies()
        .then((r) => setNames(Object.fromEntries(r.strategies.map((s) => [s.id, s.name]))))
        .catch(() => undefined);
    }
  }, [active, load, names]);

  async function check() {
    setBusy(true);
    try {
      const res = await api.checkPaper();
      const pos = res.positions ? ` Positions: checked ${String(res.positions.checked)}, closed ${String(res.positions.closed)}.` : "";
      toast(`Checked ${String(res.checked)} open trades, closed ${String(res.closed)}.${pos}`);
      await load();
    } catch (err) {
      toast(`Check failed: ${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  const s = data?.stats;
  return (
    <Stack spacing={2}>
      <PageHeader
        title="Paper trades"
        subtitle="Simulated trades from the daily Top 10 at 16:00 PKT and leveraged positions from the calculator; no order reaches Binance. A check every 4 hours closes them at stop, target, liquidation or the style's horizon."
        actions={
          <ActionButton icon={<Sync />} primary busy={busy} busyLabel="Checking…" onClick={() => void check()}>
            Check now
          </ActionButton>
        }
      />
      {error ? <Alert severity="warning">Paper trades unavailable: {error}</Alert> : null}
      <KpiStrip
        tiles={[
          { label: "Open", value: s ? String(s.open) : <Na />, note: s ? `${String(s.total)} trades in all` : "" },
          { label: "Won", tone: "buy", value: s ? String(s.won) : <Na />, note: "Hit the target" },
          { label: "Lost", tone: "sell", value: s ? String(s.lost) : <Na />, note: "Hit the stop" },
          { label: "Expired", value: s ? String(s.expired) : <Na />, note: "Closed at the horizon" },
          { label: "Win rate", value: <V value={fmtRate(s?.win_rate)} reason="No closed trades yet" />, note: "Of closed trades" },
          { label: "Total R", value: <V value={fmtR(s?.total_r, 1)} reason="No closed trades yet" />, note: "Closed trades" },
        ]}
      />
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "minmax(0, 1fr)", lg: "repeat(2, minmax(0, 1fr))" } }}>
        <StatsTable title="By style" rows={Object.entries(data?.by_style ?? {})} label={(k) => STYLE_LABEL[k] ?? k} />
        <StatsTable title="By strategy" rows={Object.entries(data?.by_strategy ?? {})} label={(k) => (k === "none" ? "No strategy" : (names[k] ?? k))} />
      </Box>
      <Card>
        {!data && !error ? <Skeleton height={160} sx={{ mx: 2 }} /> : null}
        {data && !data.trades.length ? <EmptyState icon={<ReceiptLongOutlined />} text="No paper trades yet. They open with the 16:00 picks job." /> : null}
        {data?.trades.length ? (
          <DataTable minWidth={1180}>
            <TableHead>
              <TableRow>
                <TableCell>Started</TableCell>
                <TableCell>Ended</TableCell>
                <TableCell align="right">Duration</TableCell>
                <TableCell>Pair</TableCell>
                <TableCell>Style</TableCell>
                <TableCell>Side</TableCell>
                <TableCell align="right">Entry</TableCell>
                <TableCell align="right">Stop</TableCell>
                <TableCell align="right">Target</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Exit</TableCell>
                <TableCell align="right">R</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.trades.map((t) => {
                const cls = biasClass(t.side);
                const open = t.status === "open";
                const ran = fmtDuration(t.opened_at, open ? new Date().toISOString() : (t.closed_at ?? undefined));
                return (
                  <TableRow key={t.id} hover>
                    <TableCell sx={{ whiteSpace: "nowrap" }}>
                      <V value={fmtWhen(t.opened_at)} />
                    </TableCell>
                    <TableCell sx={{ whiteSpace: "nowrap" }}>
                      <V value={fmtWhen(t.closed_at ?? undefined)} reason="Still open" />
                      {open ? (
                        <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                          Closes by {fmtWhen(t.expires_at) ?? "the expiry"}
                        </Typography>
                      ) : null}
                    </TableCell>
                    <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                      <V value={ran} reason={open ? "Still open" : "No close time recorded"} />
                      {open && ran ? (
                        <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                          so far
                        </Typography>
                      ) : null}
                    </TableCell>
                    <TableCell>
                      <Num sx={{ fontWeight: 700 }}>{t.symbol}</Num>
                      <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                        {GROUP_LABEL[t.coin_group] ?? t.coin_group}
                        {t.strategy_id ? ` · ${names[t.strategy_id] ?? t.strategy_id}` : ""}
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
                      <StatusPill status={t.status} title={t.last_checked ? `Last checked ${fmtWhen(t.last_checked) ?? ""}` : undefined} />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtPx(t.exit)} reason="Still open" />
                    </TableCell>
                    <TableCell align="right">
                      <V value={fmtR(t.r_multiple)} reason="Still open" />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </DataTable>
        ) : null}
      </Card>
      <PositionsCard data={positions} onChanged={() => void load()} />
    </Stack>
  );
}
