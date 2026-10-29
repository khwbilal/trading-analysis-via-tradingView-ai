import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import FormControlLabel from "@mui/material/FormControlLabel";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import AccountBalanceWalletOutlined from "@mui/icons-material/AccountBalanceWalletOutlined";
import Add from "@mui/icons-material/Add";
import { useCallback, useEffect, useState } from "react";
import { api, type Position, type Wallet, type WalletCharts, type WalletDetail, type WalletEntry } from "../api";
import { WalletBalanceChart, WalletHistoryCharts } from "../components/WalletCharts";
import { BookTradeDialog, CloseTradeDialog, EntryDialog, KIND_LABEL, Money, NewWalletDialog } from "../components/WalletDialogs";
import { useFeedback } from "../components/feedback";
import { ActionButton, DataTable, EmptyState, KpiStrip, Na, Num, PageHeader, Pill, SectionCard, StatusPill, V } from "../components/ui";
import { GLYPH, STYLE_LABEL, biasClass, fmtFixed, fmtPx, fmtRate, fmtWhen } from "../lib/format";
import { readPref, writePref } from "../lib/storage";

const STATUS_TIP: Record<Position["status"], string> = {
  open: "Still open",
  win: "Closed with a profit",
  loss: "Closed with a loss",
  liquidated: "Liquidated: the margin is lost",
  closed: "Closed",
};

const HISTORY_LABEL = { start: "Starting balance", deposit: "Deposit", withdrawal: "Withdrawal", trade: "Trade closed" } as const;
// WL-150: what closed in a paper wallet
const SOURCE_LABEL = { wallet: "Trade closed", paper: "Paper position closed", signal: "Signal closed" } as const;
const KIND_LONG = { futures: "USD-M futures", spot: "Spot", paper: "Paper (simulated)" } as const;

function TradeStatus({ p }: Readonly<{ p: Position }>) {
  if (p.archived_at) return <Pill glyph="⊘" label="archived" tone="neutral" title={`Archived ${fmtWhen(p.archived_at) ?? ""}: not counted`} />;
  if (p.status === "liquidated") return <Pill glyph="✕" label="liquidated" tone="sell" title={STATUS_TIP[p.status]} />;
  return <StatusPill status={p.status} title={STATUS_TIP[p.status]} />;
}

/** One wallet as a card in the side-by-side row; click to open it below. */
function WalletCard({ w, selected, onSelect }: Readonly<{ w: Wallet; selected: boolean; onSelect: () => void }>) {
  const s = w.summary;
  return (
    <Card variant="outlined" sx={{ borderColor: selected ? "primary.main" : "divider", borderWidth: selected ? 2 : 1, opacity: w.archived_at ? 0.6 : 1 }}>
      <CardActionArea onClick={onSelect} sx={{ p: 2, height: "100%" }} aria-pressed={selected}>
        <Stack spacing={1}>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <Typography variant="h3" component="h3" noWrap sx={{ flex: 1, minWidth: 0 }}>
              {w.name}
            </Typography>
            <Pill glyph={w.kind === "paper" ? "◇" : "●"} label={KIND_LABEL[w.kind].toLowerCase()} tone={w.kind === "paper" ? "info" : "neutral"} />
            {w.archived_at ? <Pill glyph="⊘" label="archived" tone="neutral" /> : null}
          </Stack>
          <Box>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              Balance
            </Typography>
            <Num sx={{ display: "block", fontSize: "1.4rem", fontWeight: 700 }}>
              {s ? `${fmtFixed(s.balance, 2) ?? ""} ${w.currency}` : <Na />}
            </Num>
          </Box>
          <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap", rowGap: 0.5 }}>
            <Typography variant="body2" component="div">
              Realized <Money pnl={s?.realized_pnl} reason="No closed trades yet" />
            </Typography>
            <Typography variant="body2" component="div">
              Open <Money pnl={s?.unrealized_pnl} reason={s?.open ? "Live price unavailable" : "No open trades"} />
            </Typography>
          </Stack>
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            {s ? `${String(s.open)} open · ${String(s.won)} won · ${String(s.lost)} lost · win rate ${fmtRate(s.win_rate) ?? "none yet"}` : ""}
          </Typography>
        </Stack>
      </CardActionArea>
    </Card>
  );
}

/** Wallets (WL-063): trades opened on Binance by hand and booked here; several wallets side by side. */
export default function Wallets({ active }: Readonly<{ active: boolean }>) {
  const { toast, ask } = useFeedback();
  const [list, setList] = useState<Wallet[] | null>(null);
  const [priceError, setPriceError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showArchived, setShowArchived] = useState(() => readPref("cca_wallets_archived") === "1");
  const [selected, setSelected] = useState<number | null>(() => Number(readPref("cca_wallet")) || null);
  const [detail, setDetail] = useState<WalletDetail | null>(null);
  const [charts, setCharts] = useState<WalletCharts | null>(null);
  const [dialog, setDialog] = useState<"new" | "entry" | "book" | null>(null);
  const [closing, setClosing] = useState<Position | null>(null);

  const load = useCallback(async () => {
    try {
      const r = await api.wallets(showArchived);
      setList(r.wallets);
      setPriceError(r.price_error ?? null);
      setError(null);
      const id = r.wallets.some((w) => w.id === selected) ? selected : (r.wallets[0]?.id ?? null);
      if (id !== selected) setSelected(id);
      setDetail(id ? await api.wallet(id) : null);
      setCharts(await api.walletCharts(showArchived)); // WL-151
    } catch (err) {
      setError((err as Error).message);
    }
  }, [showArchived, selected]);

  useEffect(() => {
    if (active) load().catch(() => undefined);
  }, [active, load]);

  const pick = (id: number) => {
    writePref("cca_wallet", String(id));
    setSelected(id);
  };

  const w = detail?.wallet;
  const s = w?.summary;
  const usable = (list ?? []).filter((x) => !x.archived_at);
  const bookable = usable.filter((x) => x.kind !== "paper");
  const paper = w?.kind === "paper";
  const series = charts?.wallets.find((x) => x.id === w?.id);

  async function rename() {
    if (!w) return;
    const name = await ask({ title: "Rename wallet", label: "Name", input: true, okLabel: "Rename" });
    if (typeof name !== "string" || !name.trim()) return;
    try {
      await api.updateWallet(w.id, { name: name.trim() });
      toast(`Renamed to ${name.trim()}.`);
      await load();
    } catch (err) {
      toast(`Not renamed: ${(err as Error).message}`);
    }
  }

  async function archive() {
    if (!w) return;
    const restore = !!w.archived_at;
    const ok = await ask({
      title: restore ? `Restore ${w.name}?` : `Archive ${w.name}?`,
      text: restore
        ? "It shows again and takes new bookings."
        : "It is hidden and takes no new bookings. Every trade and entry stays stored; you can restore it from Show archived.",
      okLabel: restore ? "Restore" : "Archive",
      danger: !restore,
    });
    if (!ok) return;
    try {
      await api.archiveWallet(w.id, restore);
      toast(restore ? `${w.name} restored.` : `${w.name} archived.`);
      await load();
    } catch (err) {
      toast(`Not changed: ${(err as Error).message}`);
    }
  }

  async function archiveTrade(p: Position) {
    if (!w) return;
    const ok = await ask({
      title: `Archive the ${p.symbol} booking?`,
      text: "For a booking made by mistake: it stops counting in the balance and results but stays stored and listed.",
      okLabel: "Archive booking",
      danger: true,
    });
    if (!ok) return;
    try {
      await api.archiveWalletTrade(w.id, p.id);
      toast(`${p.symbol} booking archived.`);
      await load();
    } catch (err) {
      toast(`Not archived: ${(err as Error).message}`);
    }
  }

  async function archiveEntry(e: WalletEntry) {
    if (!w) return;
    const ok = await ask({
      title: `Archive this ${e.kind}?`,
      text: "For an entry made by mistake: it stops counting in the balance but stays stored.",
      okLabel: "Archive entry",
      danger: true,
    });
    if (!ok) return;
    try {
      await api.archiveWalletEntry(w.id, e.id);
      toast("Entry archived.");
      await load();
    } catch (err) {
      toast(`Not archived: ${(err as Error).message}`);
    }
  }

  const header = (
    <PageHeader
      title="Wallets"
      subtitle="Trades you open on Binance yourself, booked here for bookkeeping, and paper wallets for simulated trades from Picks and Signals. Nothing is sent to Binance and no key is stored. Live prices only show the open result."
      actions={
        <>
          <ActionButton icon={<Add />} primary={!usable.length} onClick={() => setDialog("new")}>
            New wallet
          </ActionButton>
          {bookable.length ? (
            <ActionButton
              primary
              disabled={!w || !!w.archived_at || paper}
              title={paper ? "A paper wallet fills from Open paper position on Picks and from signal paper trades" : undefined}
              onClick={() => setDialog("book")}
            >
              Book a trade
            </ActionButton>
          ) : null}
        </>
      }
    />
  );

  return (
    <Stack spacing={2}>
      {header}
      {error ? <Alert severity="warning">Wallets unavailable: {error}</Alert> : null}
      {priceError ? <Alert severity="warning">Live prices unavailable: {priceError}</Alert> : null}
      <FormControlLabel
        control={
          <Switch
            checked={showArchived}
            onChange={(e) => {
              writePref("cca_wallets_archived", e.target.checked ? "1" : "0");
              setShowArchived(e.target.checked);
            }}
          />
        }
        label="Show archived wallets"
      />
      {!list && !error ? <Skeleton height={140} /> : null}
      {list && !list.length ? (
        <Card>
          <EmptyState icon={<AccountBalanceWalletOutlined />} text="No wallets yet. Create one, then book the trades you open on Binance." />
        </Card>
      ) : null}
      {list?.length ? (
        <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "minmax(0, 1fr)", sm: "repeat(auto-fill, minmax(280px, 1fr))" } }}>
          {list.map((x) => (
            <WalletCard key={x.id} w={x} selected={x.id === selected} onSelect={() => pick(x.id)} />
          ))}
        </Box>
      ) : null}
      {charts?.days.length ? <WalletBalanceChart charts={charts} /> : null}

      {w && s ? (
        <>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ alignItems: { sm: "center" } }}>
            <Typography variant="h2" component="h2" sx={{ flex: 1, minWidth: 0, overflowWrap: "anywhere" }}>
              {w.name}
              <Typography component="span" variant="body2" sx={{ color: "text.secondary", ml: 1 }}>
                {paper ? "" : `${w.exchange} · `}
                {KIND_LONG[w.kind]} · since {fmtWhen(w.created_at) ?? ""}
              </Typography>
            </Typography>
            <ActionButton compact disabled={!!w.archived_at} onClick={() => setDialog("entry")}>
              Deposit or withdraw
            </ActionButton>
            <ActionButton compact onClick={() => void rename()}>
              Rename
            </ActionButton>
            <ActionButton compact onClick={() => void archive()}>
              {w.archived_at ? "Restore" : "Archive"}
            </ActionButton>
          </Stack>
          <KpiStrip
            tiles={[
              { label: "Balance", value: fmtFixed(s.balance, 2) ?? <Na />, unit: w.currency, note: "Start, deposits, withdrawals and closed trades" },
              {
                label: "Equity",
                value: <V value={fmtFixed(s.equity, 2)} reason={s.open ? "Live price unavailable" : "No open trades"} />,
                unit: s.equity === null || s.equity === undefined ? undefined : w.currency,
                note: "Balance plus open trades at the live price",
              },
              { label: "Realized", value: <Money pnl={s.realized_pnl} reason="No closed trades yet" />, note: "Closed trades, after fees" },
              { label: "Unrealized", value: <Money pnl={s.unrealized_pnl} reason={s.open ? "Live price unavailable" : "No open trades"} />, note: "Open trades, after the open fee" },
              { label: "Win rate", value: <V value={fmtRate(s.win_rate)} reason="No closed trades yet" />, note: `${String(s.won)} won, ${String(s.lost)} lost` },
              { label: "Fees", value: <V value={fmtFixed(s.fees, 2)} reason="No closed trades yet" />, unit: s.fees === null || s.fees === undefined ? undefined : w.currency, note: "Closed trades" },
            ]}
          />

          <SectionCard title="Trades" noPadding>
            {detail.trades.length ? (
              <DataTable minWidth={1240}>
                <TableHead>
                  <TableRow>
                    <TableCell>Opened</TableCell>
                    <TableCell>Pair</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell align="right">{w.kind === "spot" ? "Cost" : "Margin"}</TableCell>
                    <TableCell align="right">Leverage</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell align="right">Entry</TableCell>
                    <TableCell align="right">Stop</TableCell>
                    <TableCell align="right">Target</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Price or exit</TableCell>
                    <TableCell align="right">Fees</TableCell>
                    <TableCell align="right">Profit or loss</TableCell>
                    <TableCell />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {detail.trades.map((p) => {
                    const cls = biasClass(p.side);
                    const booked = p.account === "wallet"; // WL-150: paper positions and signals close by the paper checks
                    const open = p.status === "open" && !p.archived_at;
                    return (
                      <TableRow key={`${p.account}-${String(p.id)}`} hover sx={{ opacity: p.archived_at ? 0.55 : 1 }}>
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
                          {booked ? null : (
                            <Pill glyph="◇" label={p.account === "signal" ? "signal" : "paper"} tone="info" title={p.account === "signal" ? "A signal's paper trade" : "A paper position from Picks"} />
                          )}
                          {p.pick_day || p.notes ? (
                            <Typography variant="caption" component="div" sx={{ color: "text.secondary", maxWidth: 220, overflowWrap: "anywhere" }}>
                              {p.pick_day ? `Pick ${p.pick_day}${p.style ? ` · ${STYLE_LABEL[p.style] ?? p.style}` : ""}` : ""}
                              {p.pick_day && p.notes ? " · " : ""}
                              {p.notes ?? ""}
                            </Typography>
                          ) : null}
                        </TableCell>
                        <TableCell>
                          <Pill glyph={GLYPH[cls]} label={w.kind === "spot" ? "Buy" : p.side === "Buy" ? "Long" : "Short"} tone={cls === "buy" ? "buy" : "sell"} />
                        </TableCell>
                        <TableCell align="right">
                          <V value={fmtFixed(p.margin, 2)} />
                        </TableCell>
                        <TableCell align="right">
                          <Num>{p.leverage}x</Num>
                        </TableCell>
                        <TableCell align="right">
                          <V value={fmtFixed(p.qty, 6)} />
                        </TableCell>
                        <TableCell align="right">
                          <V value={fmtPx(p.entry)} />
                        </TableCell>
                        <TableCell align="right">
                          <V value={fmtPx(p.stop)} reason="No stop booked" />
                        </TableCell>
                        <TableCell align="right">
                          <V value={fmtPx(p.target)} reason="No target booked" />
                        </TableCell>
                        <TableCell>
                          <TradeStatus p={p} />
                        </TableCell>
                        <TableCell align="right">
                          {p.status === "open" ? <V value={fmtPx(p.live_price)} reason={p.archived_at ? "Archived" : "Live price unavailable"} /> : <V value={fmtPx(p.exit)} />}
                        </TableCell>
                        <TableCell align="right">
                          <V value={fmtFixed(p.status === "open" ? p.open_fee : p.fees, 2)} reason="No fee booked" />
                        </TableCell>
                        <TableCell align="right">
                          {p.status === "open" ? (
                            <Money pnl={p.unrealized?.pnl} roe={p.unrealized?.roe} reason={p.archived_at ? "Archived" : "Live price unavailable"} />
                          ) : (
                            <Money pnl={p.pnl} roe={p.roe} />
                          )}
                        </TableCell>
                        <TableCell sx={{ whiteSpace: "nowrap" }}>
                          <Stack direction="row" spacing={1}>
                            {open && booked ? (
                              <ActionButton compact onClick={() => setClosing(p)}>
                                Close
                              </ActionButton>
                            ) : null}
                            {p.archived_at || !booked ? null : (
                              <ActionButton compact onClick={() => void archiveTrade(p)} title="A booking made by mistake: keep it stored, stop counting it">
                                Archive
                              </ActionButton>
                            )}
                          </Stack>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </DataTable>
            ) : (
              <EmptyState
                icon={<AccountBalanceWalletOutlined />}
                text={
                  paper
                    ? "No paper trades in this wallet yet. Pick it in Open paper position on Picks, or in a signal's paper trade."
                    : "No trades booked in this wallet yet. Use Book a trade after you open one on Binance."
                }
              />
            )}
          </SectionCard>

          {charts && series ? <WalletHistoryCharts charts={charts} wallet={series} /> : null}

          <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "minmax(0, 1fr)", lg: "repeat(2, minmax(0, 1fr))" } }}>
            <SectionCard title="Balance history" noPadding>
              <DataTable minWidth={460} maxHeight={420}>
                <TableHead>
                  <TableRow>
                    <TableCell>When</TableCell>
                    <TableCell>What</TableCell>
                    <TableCell align="right">Change</TableCell>
                    <TableCell align="right">Balance</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {[...detail.history].reverse().map((h, i) => (
                    <TableRow key={`${h.kind}-${h.source ?? ""}-${String(h.ref ?? i)}`}>
                      <TableCell sx={{ whiteSpace: "nowrap" }}>
                        <V value={fmtWhen(h.at)} />
                      </TableCell>
                      <TableCell>
                        {h.kind === "trade" && h.source ? SOURCE_LABEL[h.source] : HISTORY_LABEL[h.kind]}
                        {h.symbol ? ` · ${h.symbol}` : ""}
                      </TableCell>
                      <TableCell align="right">
                        {h.kind === "trade" ? <Money pnl={h.amount} /> : <V value={h.kind === "start" ? fmtFixed(h.amount, 2) : `${(h.amount ?? 0) >= 0 ? "+" : ""}${fmtFixed(h.amount, 2) ?? ""}`} />}
                      </TableCell>
                      <TableCell align="right">
                        <Num sx={{ fontWeight: 600 }}>{fmtFixed(h.balance, 2)}</Num>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </DataTable>
            </SectionCard>
            <SectionCard title="Deposits and withdrawals" noPadding>
              {detail.entries.length ? (
                <DataTable minWidth={460} maxHeight={420}>
                  <TableHead>
                    <TableRow>
                      <TableCell>When</TableCell>
                      <TableCell>Kind</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell>Notes</TableCell>
                      <TableCell />
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {detail.entries.map((e) => (
                      <TableRow key={e.id} sx={{ opacity: e.archived_at ? 0.55 : 1 }}>
                        <TableCell sx={{ whiteSpace: "nowrap" }}>
                          <V value={fmtWhen(e.at)} />
                        </TableCell>
                        <TableCell>
                          {e.archived_at ? (
                            <Pill glyph="⊘" label="archived" tone="neutral" title="Not counted" />
                          ) : (
                            <Pill glyph={e.kind === "deposit" ? "＋" : "−"} label={e.kind} tone="neutral" />
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <Num>
                            {fmtFixed(e.amount, 2)} {w.currency}
                          </Num>
                        </TableCell>
                        <TableCell sx={{ color: "text.secondary", overflowWrap: "anywhere" }}>{e.notes ?? ""}</TableCell>
                        <TableCell>
                          {e.archived_at ? null : (
                            <ActionButton compact onClick={() => void archiveEntry(e)}>
                              Archive
                            </ActionButton>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </DataTable>
              ) : (
                <EmptyState text="No deposits or withdrawals yet." />
              )}
            </SectionCard>
          </Box>
        </>
      ) : null}

      {dialog === "new" ? (
        <NewWalletDialog
          onClose={() => setDialog(null)}
          onSaved={(nw) => {
            pick(nw.id);
            void load();
          }}
        />
      ) : null}
      {dialog === "entry" && w ? <EntryDialog wallet={w} onClose={() => setDialog(null)} onSaved={() => void load()} /> : null}
      {dialog === "book" ? <BookTradeDialog wallets={bookable} walletId={w?.id} onClose={() => setDialog(null)} onSaved={() => void load()} /> : null}
      {closing && w ? <CloseTradeDialog wallet={w} trade={closing} onClose={() => setClosing(null)} onSaved={() => void load()} /> : null}
    </Stack>
  );
}
