import Alert from "@mui/material/Alert";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import CalculateOutlined from "@mui/icons-material/CalculateOutlined";
import { useState } from "react";
import { api, type Position, type PositionsResponse } from "../api";
import { GLYPH, biasClass, fmtFixed, fmtPx, fmtRate, fmtSigned, fmtWhen } from "../lib/format";
import { useFeedback } from "./feedback";
import { ActionButton, DataTable, EmptyState, KpiStrip, Na, Num, Pill, SectionCard, StatusPill, V } from "./ui";

/** Profit green with ▲, loss red with ▼ (ruleset 9). */
function Money({ pnl, roe }: Readonly<{ pnl: number | null | undefined; roe?: number | null }>) {
  if (pnl === null || pnl === undefined) return <Na reason="No price yet" />;
  const up = pnl >= 0;
  return (
    <Num sx={{ color: up ? "success.main" : "error.main", fontWeight: 600 }}>
      {up ? "▲ " : "▼ "}
      {fmtSigned(pnl, 2)}
      {roe === null || roe === undefined ? "" : ` (${fmtSigned(roe, 1) ?? ""}%)`}
    </Num>
  );
}

const STATUS_TIP: Record<Position["status"], string> = {
  open: "Still open",
  win: "Reached the target",
  loss: "Reached the stop",
  liquidated: "Liquidated: the margin is lost",
  closed: "Closed by hand",
};

/** Leveraged paper positions opened from the calculator (WL-061), with live unrealized profit or loss. */
export default function PositionsCard({ data, onChanged }: Readonly<{ data: PositionsResponse | null; onChanged: () => void }>) {
  const { toast, ask } = useFeedback();
  const [closing, setClosing] = useState<number | null>(null);
  const s = data?.stats;

  async function close(p: Position) {
    const ok = await ask({
      title: `Close ${p.symbol} ${p.side === "Buy" ? "long" : "short"}?`,
      text: `It closes at the live Binance price${p.live_price ? `, about ${fmtPx(p.live_price) ?? ""}` : ""}, fees included. The position stays in the list.`,
      okLabel: "Close position",
      danger: true,
    });
    if (!ok) return;
    setClosing(p.id);
    try {
      const done = await api.closePosition(p.id);
      toast(`${done.symbol} closed at ${fmtPx(done.exit) ?? ""}: ${fmtSigned(done.pnl, 2) ?? ""} USDT.`);
      onChanged();
    } catch (err) {
      toast(`Not closed: ${(err as Error).message}`);
    } finally {
      setClosing(null);
    }
  }

  return (
    <SectionCard title="Leveraged positions" noPadding>
      <Stack spacing={2} sx={{ p: 2 }}>
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          Opened from the calculator on the Top 10 picks page (Try a position). They open at the live price and close at the stop, the target or
          liquidation, checked with the paper trades every 4 hours, or by hand. Amounts in USDT.
        </Typography>
        {data?.price_error ? <Alert severity="warning">Live prices unavailable: {data.price_error}</Alert> : null}
        <KpiStrip
          tiles={[
            { label: "Open", value: s ? String(s.open) : <Na />, note: s ? `${String(s.total)} positions in all` : "" },
            { label: "Unrealized", value: <Money pnl={s?.unrealized_pnl} />, note: "Open positions at the live price" },
            { label: "Realized", value: <Money pnl={s?.realized_pnl} />, note: "Closed positions, after fees" },
            { label: "Win rate", value: <V value={fmtRate(s?.win_rate)} reason="No closed positions yet" />, note: s ? `${String(s.won)} won, ${String(s.lost)} lost` : "" },
            { label: "Liquidated", value: s ? String(s.liquidated) : <Na />, note: "Margin lost" },
          ]}
        />
      </Stack>
      {data && !data.positions.length ? (
        <EmptyState icon={<CalculateOutlined />} text="No leveraged positions yet. Open one from Try a position on the Top 10 picks page." />
      ) : null}
      {data?.positions.length ? (
        <DataTable minWidth={1240}>
          <TableHead>
            <TableRow>
              <TableCell>Opened</TableCell>
              <TableCell>Pair</TableCell>
              <TableCell>Side</TableCell>
              <TableCell align="right">Margin</TableCell>
              <TableCell align="right">Leverage</TableCell>
              <TableCell align="right">Entry</TableCell>
              <TableCell align="right">Stop</TableCell>
              <TableCell align="right">Target</TableCell>
              <TableCell align="right">Liquidation</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Price or exit</TableCell>
              <TableCell align="right">Profit or loss</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {data.positions.map((p) => {
              const cls = biasClass(p.side);
              const open = p.status === "open";
              return (
                <TableRow key={p.id} hover>
                  <TableCell sx={{ whiteSpace: "nowrap" }}>
                    <V value={fmtWhen(p.opened_at)} />
                    {p.closed_at ? (
                      <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                        Closed {fmtWhen(p.closed_at) ?? ""}
                      </Typography>
                    ) : null}
                  </TableCell>
                  <TableCell>
                    <Num sx={{ fontWeight: 700 }}>{p.symbol}</Num>
                    {p.pick_day ? (
                      <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                        Pick {p.pick_day}
                        {p.style ? ` · ${p.style}` : ""}
                      </Typography>
                    ) : null}
                  </TableCell>
                  <TableCell>
                    <Pill glyph={GLYPH[cls]} label={p.side === "Buy" ? "Long" : "Short"} tone={cls === "buy" ? "buy" : "sell"} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtFixed(p.margin, 2)} />
                  </TableCell>
                  <TableCell align="right">
                    <Num>{p.leverage}x</Num>
                    <Typography
                      variant="caption"
                      component="div"
                      sx={{ color: "text.secondary" }}
                      title={
                        p.margin_mode === "cross"
                          ? `Cross: backed by ${fmtFixed(p.cross_balance, 2) ?? "the"} USDT balance`
                          : "Isolated: the loss is capped at this margin"
                      }
                    >
                      {p.margin_mode ?? "isolated"}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtPx(p.entry)} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtPx(p.stop)} reason="No stop set" />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtPx(p.target)} reason="No target set" />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtPx(p.liquidation)} />
                  </TableCell>
                  <TableCell>
                    {p.status === "liquidated" ? (
                      <Pill glyph="✕" label="liquidated" tone="sell" title={STATUS_TIP[p.status]} />
                    ) : p.status === "closed" ? (
                      <Pill glyph="■" label="closed" tone="neutral" title={STATUS_TIP[p.status]} />
                    ) : (
                      <StatusPill status={p.status} title={STATUS_TIP[p.status]} />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {open ? <V value={fmtPx(p.live_price)} reason="Live price unavailable" /> : <V value={fmtPx(p.exit)} />}
                  </TableCell>
                  <TableCell align="right">{open ? <Money pnl={p.unrealized?.pnl} roe={p.unrealized?.roe} /> : <Money pnl={p.pnl} roe={p.roe} />}</TableCell>
                  <TableCell>
                    {open ? (
                      <ActionButton compact busy={closing === p.id} busyLabel="Closing…" onClick={() => void close(p)}>
                        Close
                      </ActionButton>
                    ) : null}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </DataTable>
      ) : null}
    </SectionCard>
  );
}
