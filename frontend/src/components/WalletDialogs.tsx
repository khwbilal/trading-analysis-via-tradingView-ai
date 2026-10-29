import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Checkbox from "@mui/material/Checkbox";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControlLabel from "@mui/material/FormControlLabel";
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import Close from "@mui/icons-material/Close";
import { useEffect, useState, type ReactNode } from "react";
import { api, type Position, type Wallet, type WalletEntry, type WalletKind } from "../api";
import { fmtFixed, fmtPx, fmtSigned } from "../lib/format";
import { type Side, cleanDecimal, liquidation, toDecimalText } from "../lib/position";
import { useFeedback } from "./feedback";
import { ActionButton, Num, V } from "./ui";

/** Wallet dialogs (WL-063): new wallet, deposit or withdrawal, book a trade, close a trade.
 * Bookkeeping only: nothing is sent to Binance. Numbers take at most 6 decimals (WL-062). */

const num = (s: string) => (s.trim() === "" ? Number.NaN : Number(s));

/** Local time for a datetime-local field, minutes precision. */
export function localNow(d: Date = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${String(d.getFullYear())}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function Shell({ title, sub, onClose, children }: Readonly<{ title: string; sub?: string; onClose: () => void; children: ReactNode }>) {
  const phone = useMediaQuery((t) => t.breakpoints.down("sm"));
  return (
    <Dialog open onClose={onClose} fullScreen={phone} fullWidth maxWidth="sm" aria-labelledby="walletDlg">
      <DialogTitle id="walletDlg" sx={{ display: "flex", alignItems: "center", gap: 1, pr: 1 }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          {title}
          {sub ? (
            <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
              {sub}
            </Typography>
          ) : null}
        </Box>
        <IconButton aria-label="Close" onClick={onClose}>
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>{children}</Stack>
      </DialogContent>
    </Dialog>
  );
}

function Amount({
  label,
  value,
  onChange,
  unit,
  help,
}: Readonly<{ label: string; value: string; onChange: (v: string) => void; unit?: string; help?: string }>) {
  return (
    <TextField
      label={label}
      size="small"
      value={value}
      onChange={(e) => onChange(cleanDecimal(e.target.value))}
      helperText={help}
      slotProps={{ htmlInput: { inputMode: "decimal" }, input: unit ? { endAdornment: <InputAdornment position="end">{unit}</InputAdornment> } : undefined }}
      sx={{ flex: 1, minWidth: 130 }}
    />
  );
}

function When({ label, value, onChange }: Readonly<{ label: string; value: string; onChange: (v: string) => void }>) {
  return (
    <TextField
      label={label}
      type="datetime-local"
      size="small"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      slotProps={{ inputLabel: { shrink: true } }}
      sx={{ flex: 1, minWidth: 200 }}
    />
  );
}

function SideToggle({ side, onChange, spot }: Readonly<{ side: Side; onChange: (s: Side) => void; spot: boolean }>) {
  return (
    <ToggleButtonGroup exclusive value={side} onChange={(_e, v: Side | null) => v && onChange(v)} aria-label="Side" size="small">
      <ToggleButton value="Buy" sx={{ px: 3, "&.Mui-selected": { color: "success.main" } }}>
        ▲ {spot ? "Buy" : "Long"}
      </ToggleButton>
      <ToggleButton value="Sell" disabled={spot} sx={{ px: 3, "&.Mui-selected": { color: "error.main" } }}>
        ▼ Short
      </ToggleButton>
    </ToggleButtonGroup>
  );
}

/** Profit green with ▲, loss red with ▼ (ruleset 9). */
export function Money({ pnl, roe, reason = "No price yet" }: Readonly<{ pnl: number | null | undefined; roe?: number | null; reason?: string }>) {
  if (pnl === null || pnl === undefined) return <V value={null} reason={reason} />;
  const up = pnl >= 0;
  return (
    <Num sx={{ color: up ? "success.main" : "error.main", fontWeight: 600 }}>
      {up ? "▲ " : "▼ "}
      {fmtSigned(pnl, 2)}
      {roe === null || roe === undefined ? "" : ` (${fmtSigned(roe, 1) ?? ""}%)`}
    </Num>
  );
}

function useSave() {
  const { toast } = useFeedback();
  const [busy, setBusy] = useState(false);
  async function save<T>(call: () => Promise<T>, done: (r: T) => string, after: (r: T) => void) {
    setBusy(true);
    try {
      const r = await call();
      toast(done(r));
      after(r);
    } catch (err) {
      toast(`Not saved: ${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  }
  return { busy, save };
}

export function NewWalletDialog({ onClose, onSaved }: Readonly<{ onClose: () => void; onSaved: (w: Wallet) => void }>) {
  const { busy, save } = useSave();
  const [name, setName] = useState("");
  const [kind, setKind] = useState<WalletKind>("futures");
  const [exchange, setExchange] = useState("Binance");
  const [start, setStart] = useState("0");
  const [notes, setNotes] = useState("");
  const ok = name.trim() !== "" && num(start) >= 0;
  return (
    <Shell title="New wallet" sub="A place to book the trades you open on the exchange yourself, or a paper wallet for simulated trades." onClose={onClose}>
      <TextField label="Name" size="small" value={name} onChange={(e) => setName(e.target.value)} slotProps={{ htmlInput: { maxLength: 80 } }} autoFocus />
      <ToggleButtonGroup exclusive value={kind} onChange={(_e, v: WalletKind | null) => v && setKind(v)} aria-label="Kind" size="small">
        <ToggleButton value="futures" sx={{ px: 3 }}>
          USD-M futures
        </ToggleButton>
        <ToggleButton value="spot" sx={{ px: 3 }}>
          Spot
        </ToggleButton>
        <ToggleButton value="paper" sx={{ px: 3 }}>
          Paper
        </ToggleButton>
      </ToggleButtonGroup>
      {kind === "paper" ? (
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          Simulated: pick it when you open a paper position on Picks or for a signal&apos;s paper trade. It takes no hand bookings.
        </Typography>
      ) : null}
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
        <TextField label="Exchange" size="small" value={exchange} onChange={(e) => setExchange(e.target.value)} sx={{ flex: 1 }} />
        <Amount label="Starting balance" value={start} onChange={setStart} unit="USDT" />
      </Stack>
      <TextField label="Notes" size="small" value={notes} onChange={(e) => setNotes(e.target.value)} multiline minRows={2} />
      <Stack direction="row" sx={{ justifyContent: "flex-end" }}>
        <ActionButton
          primary
          busy={busy}
          busyLabel="Saving…"
          disabled={!ok}
          onClick={() =>
            void save(
              () => api.createWallet({ name: name.trim(), kind, exchange: exchange.trim() || "Binance", starting_balance: num(start), notes: notes.trim() || null }),
              (w) => `Wallet ${w.name} created.`,
              (w) => {
                onSaved(w);
                onClose();
              },
            )
          }
        >
          Create wallet
        </ActionButton>
      </Stack>
    </Shell>
  );
}

export function EntryDialog({ wallet, onClose, onSaved }: Readonly<{ wallet: Wallet; onClose: () => void; onSaved: () => void }>) {
  const { busy, save } = useSave();
  const [kind, setKind] = useState<WalletEntry["kind"]>("deposit");
  const [amount, setAmount] = useState("");
  const [at, setAt] = useState(localNow());
  const [notes, setNotes] = useState("");
  const ok = num(amount) > 0;
  return (
    <Shell title={`Deposit or withdrawal: ${wallet.name}`} sub="Money moved in or out of the wallet." onClose={onClose}>
      <ToggleButtonGroup exclusive value={kind} onChange={(_e, v: WalletEntry["kind"] | null) => v && setKind(v)} aria-label="Kind" size="small">
        <ToggleButton value="deposit" sx={{ px: 3 }}>
          ＋ Deposit
        </ToggleButton>
        <ToggleButton value="withdrawal" sx={{ px: 3 }}>
          − Withdrawal
        </ToggleButton>
      </ToggleButtonGroup>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
        <Amount label="Amount" value={amount} onChange={setAmount} unit={wallet.currency} />
        <When label="When" value={at} onChange={setAt} />
      </Stack>
      <TextField label="Notes" size="small" value={notes} onChange={(e) => setNotes(e.target.value)} />
      <Stack direction="row" sx={{ justifyContent: "flex-end" }}>
        <ActionButton
          primary
          busy={busy}
          busyLabel="Saving…"
          disabled={!ok}
          onClick={() =>
            void save(
              () => api.addWalletEntry(wallet.id, { kind, amount: num(amount), at: at || null, notes: notes.trim() || null }),
              (e) => `${e.kind === "deposit" ? "Deposit" : "Withdrawal"} of ${fmtFixed(e.amount, 2) ?? ""} ${wallet.currency} booked.`,
              () => {
                onSaved();
                onClose();
              },
            )
          }
        >
          Book {kind}
        </ActionButton>
      </Stack>
    </Shell>
  );
}

export type TradePrefill = {
  symbol?: string;
  side?: Side;
  entry?: number | null;
  stop?: number | null;
  target?: number | null;
  margin?: number | null;
  leverage?: number;
  pick_day?: string | null;
  style?: string | null;
};

/** Book a trade you opened on the exchange. Pick the wallet here when more than one is open. */
export function BookTradeDialog({
  wallets: all,
  walletId,
  prefill,
  onClose,
  onSaved,
}: Readonly<{ wallets: Wallet[]; walletId?: number; prefill?: TradePrefill; onClose: () => void; onSaved?: (p: Position) => void }>) {
  const { busy, save } = useSave();
  const wallets = all.filter((w) => w.kind !== "paper"); // WL-150: paper wallets take paper trades only
  const [wid, setWid] = useState<number | "">(wallets.some((w) => w.id === walletId) ? (walletId ?? "") : (wallets[0]?.id ?? ""));
  const wallet = wallets.find((w) => w.id === wid);
  const spot = wallet?.kind === "spot";
  const [symbol, setSymbol] = useState(prefill?.symbol ?? "");
  const [side, setSide] = useState<Side>(prefill?.side ?? "Buy");
  const [entry, setEntry] = useState(prefill?.entry ? toDecimalText(prefill.entry) : "");
  const [by, setBy] = useState<"margin" | "qty">("margin");
  const [size, setSize] = useState(prefill?.margin ? toDecimalText(prefill.margin) : "");
  const [leverage, setLeverage] = useState(String(prefill?.leverage ?? 10));
  const [fee, setFee] = useState("");
  const [stop, setStop] = useState(prefill?.stop ? toDecimalText(prefill.stop) : "");
  const [target, setTarget] = useState(prefill?.target ? toDecimalText(prefill.target) : "");
  const [at, setAt] = useState(localNow());
  const [notes, setNotes] = useState("");

  const effSide: Side = spot ? "Buy" : side;
  const e = num(entry);
  const lev = spot ? 1 : Math.round(num(leverage));
  const sz = num(size);
  const s = num(stop);
  const t = num(target);
  const sizeOk = sz > 0;
  const levOk = spot || (lev >= 1 && lev <= 125);
  const margin = sizeOk && e > 0 && levOk ? (by === "margin" ? sz : (sz * e) / lev) : Number.NaN;
  const qty = sizeOk && e > 0 && levOk ? (by === "qty" ? sz : (sz * lev) / e) : Number.NaN;
  const liq = !spot && e > 0 && levOk ? liquidation({ side: effSide, entry: e, margin: 1, leverage: lev, feeRate: 0, mmr: 0.005 }) : Number.NaN;
  const wrongStop = Number.isFinite(s) && e > 0 && (effSide === "Buy" ? s >= e : s <= e);
  const wrongTarget = Number.isFinite(t) && e > 0 && (effSide === "Buy" ? t <= e : t >= e);
  const liqFirst = !spot && Number.isFinite(s) && !wrongStop && Number.isFinite(liq) && (effSide === "Buy" ? liq >= s : liq <= s);
  const ok = !!wallet && symbol.trim().length > 1 && e > 0 && sizeOk && levOk && !(num(fee) < 0) && !wrongStop && !wrongTarget;
  const base = symbol.trim().toUpperCase().replace(/USDT$|USDC$/, "") || "coins";

  return (
    <Shell title="Book a trade" sub="Record a trade you opened on the exchange yourself. Nothing is sent to Binance." onClose={onClose}>
      {wallets.length ? null : <Alert severity="info">Create a wallet first on the Wallets page.</Alert>}
      {wallets.length > 1 || walletId === undefined ? (
        <TextField select label="Wallet" size="small" value={wid} onChange={(ev) => setWid(Number(ev.target.value))}>
          {wallets.map((w) => (
            <MenuItem key={w.id} value={w.id}>
              {w.name} · {KIND_LABEL[w.kind]}
            </MenuItem>
          ))}
        </TextField>
      ) : null}
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ alignItems: { sm: "center" } }}>
        <TextField
          label="Pair"
          size="small"
          value={symbol}
          onChange={(ev) => setSymbol(ev.target.value.toUpperCase().replace(/[^A-Z0-9.]/g, ""))}
          placeholder="SOLUSDT"
          sx={{ flex: 1 }}
        />
        <SideToggle side={effSide} onChange={setSide} spot={spot} />
      </Stack>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
        <Amount label="Entry price" value={entry} onChange={setEntry} />
        {spot ? null : <Amount label="Leverage" value={leverage} onChange={(v) => setLeverage(v.replace(/\..*/, ""))} unit="x" />}
      </Stack>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ alignItems: { sm: "flex-start" } }}>
        <ToggleButtonGroup exclusive value={by} onChange={(_e, v: "margin" | "qty" | null) => v && setBy(v)} aria-label="Size by" size="small">
          <ToggleButton value="margin">{spot ? "Cost" : "Margin"}</ToggleButton>
          <ToggleButton value="qty">Quantity</ToggleButton>
        </ToggleButtonGroup>
        <Amount label={by === "qty" ? "Quantity" : spot ? "Cost" : "Margin"} value={size} onChange={setSize} unit={by === "qty" ? base : wallet?.currency ?? "USDT"} />
        <Amount label="Fee paid" value={fee} onChange={setFee} unit={wallet?.currency ?? "USDT"} help="At the open, from the exchange" />
      </Stack>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
        <Amount label="Stop (optional)" value={stop} onChange={setStop} />
        <Amount label="Target (optional)" value={target} onChange={setTarget} />
      </Stack>
      <When label="Opened at" value={at} onChange={setAt} />
      <TextField label="Notes" size="small" value={notes} onChange={(ev) => setNotes(ev.target.value)} />
      {!levOk ? <Alert severity="warning">Leverage is 1 to 125.</Alert> : null}
      {wrongStop ? <Alert severity="warning">The stop is on the wrong side of the entry.</Alert> : null}
      {wrongTarget ? <Alert severity="warning">The target is on the wrong side of the entry.</Alert> : null}
      {liqFirst ? <Alert severity="warning">At {lev}x the estimated liquidation {fmtPx(liq) ?? ""} comes before the stop. It is booked anyway.</Alert> : null}
      {Number.isFinite(margin) ? (
        <Stack direction="row" spacing={3} sx={{ flexWrap: "wrap" }}>
          <Typography variant="body2">
            {spot ? "Cost" : "Margin"} <Num sx={{ fontWeight: 700 }}>{fmtFixed(margin, 2)}</Num>
          </Typography>
          <Typography variant="body2">
            Quantity <Num sx={{ fontWeight: 700 }}>{fmtFixed(qty, 6)}</Num>
          </Typography>
          {spot ? null : (
            <Typography variant="body2">
              Liquidation about <V value={fmtPx(liq)} />
            </Typography>
          )}
        </Stack>
      ) : null}
      <Stack direction="row" sx={{ justifyContent: "flex-end" }}>
        <ActionButton
          primary
          busy={busy}
          busyLabel="Booking…"
          disabled={!ok}
          onClick={() =>
            void save(
              () =>
                api.bookTrade(Number(wid), {
                  symbol: symbol.trim(),
                  side: effSide,
                  entry: e,
                  margin: by === "margin" ? sz : null,
                  qty: by === "qty" ? sz : null,
                  leverage: lev,
                  open_fee: num(fee) > 0 ? num(fee) : 0,
                  stop: Number.isFinite(s) ? s : null,
                  target: Number.isFinite(t) ? t : null,
                  opened_at: at || null,
                  pick_day: prefill?.pick_day ?? null,
                  style: prefill?.style ?? null,
                  notes: notes.trim() || null,
                }),
              (p) => `${p.symbol} ${p.side === "Buy" ? "long" : "short"} booked in ${wallet?.name ?? "the wallet"}.`,
              (p) => {
                onSaved?.(p);
                onClose();
              },
            )
          }
        >
          Book trade
        </ActionButton>
      </Stack>
    </Shell>
  );
}

/** Close a booked trade at the exit you got, with the fee paid, or mark it liquidated. */
export function CloseTradeDialog({ wallet, trade, onClose, onSaved }: Readonly<{ wallet: Wallet; trade: Position; onClose: () => void; onSaved: () => void }>) {
  const { busy, save } = useSave();
  const [exit, setExit] = useState(trade.live_price ? toDecimalText(trade.live_price) : "");
  const [fee, setFee] = useState("");
  const [at, setAt] = useState(localNow());
  const [liquidated, setLiquidated] = useState(false);
  const x = liquidated ? (num(exit) > 0 ? num(exit) : trade.liquidation) : num(exit);
  const f = num(fee) > 0 ? num(fee) : 0;
  const dir = trade.side === "Buy" ? 1 : -1;
  const fees = (trade.open_fee ?? 0) + f;
  let gross = x > 0 ? dir * trade.qty * (x - trade.entry) : Number.NaN;
  if (trade.market === "usdm") gross = Math.max(gross, -trade.margin);
  const pnl = liquidated ? -trade.margin - fees : gross - fees;
  const ok = (liquidated || num(exit) > 0) && !(num(fee) < 0);
  return (
    <Shell title={`Close ${trade.symbol} ${trade.side === "Buy" ? "long" : "short"}`} sub={`Entry ${fmtPx(trade.entry) ?? ""}, ${wallet.name}. Enter what the exchange shows.`} onClose={onClose}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
        <Amount label={liquidated ? "Liquidation price (optional)" : "Exit price"} value={exit} onChange={setExit} />
        <Amount label="Fee paid" value={fee} onChange={setFee} unit={wallet.currency} help="At the close" />
      </Stack>
      <When label="Closed at" value={at} onChange={setAt} />
      {trade.market === "usdm" ? (
        <FormControlLabel control={<Checkbox checked={liquidated} onChange={(e) => setLiquidated(e.target.checked)} />} label="It was liquidated: the margin is lost" />
      ) : null}
      {Number.isFinite(pnl) ? (
        <Typography variant="body2">
          Result after {fmtFixed(fees, 2) ?? ""} {wallet.currency} fees: <Money pnl={pnl} roe={(pnl / trade.margin) * 100} />
        </Typography>
      ) : null}
      <Stack direction="row" sx={{ justifyContent: "flex-end" }}>
        <ActionButton
          primary
          busy={busy}
          busyLabel="Closing…"
          disabled={!ok}
          onClick={() =>
            void save(
              () => api.closeWalletTrade(wallet.id, trade.id, { exit: num(exit) > 0 ? num(exit) : null, close_fee: f, closed_at: at || null, liquidated }),
              (p) => `${p.symbol} closed: ${fmtSigned(p.pnl, 2) ?? ""} ${wallet.currency}.`,
              () => {
                onSaved();
                onClose();
              },
            )
          }
        >
          Close trade
        </ActionButton>
      </Stack>
    </Shell>
  );
}

export const KIND_LABEL: Record<WalletKind, string> = { futures: "Futures", spot: "Spot", paper: "Paper" };

/** WL-150: pick the paper wallet a paper trade counts in, or none. Loads the open paper wallets itself. */
export function PaperWalletPicker({
  value,
  onChange,
  label = "Paper wallet",
  disabled = false,
}: Readonly<{ value: number; onChange: (id: number) => void; label?: string; disabled?: boolean }>) {
  const [wallets, setWallets] = useState<Wallet[] | null>(null);
  useEffect(() => {
    let cancelled = false;
    api
      .wallets()
      .then((r) => !cancelled && setWallets(r.wallets.filter((w) => w.kind === "paper")))
      .catch(() => !cancelled && setWallets([]));
    return () => {
      cancelled = true;
    };
  }, []);
  const known = !wallets || !value || wallets.some((w) => w.id === value);
  return (
    <TextField
      select
      label={label}
      size="small"
      value={wallets ? (known ? value : 0) : ""}
      disabled={disabled || !wallets}
      onChange={(e) => onChange(Number(e.target.value))}
      helperText={wallets && !wallets.length ? "No paper wallet yet: create one on the Wallets page." : undefined}
      sx={{ minWidth: 200 }}
    >
      <MenuItem value={0}>No wallet</MenuItem>
      {(wallets ?? []).map((w) => (
        <MenuItem key={w.id} value={w.id}>
          {w.name}
        </MenuItem>
      ))}
    </TextField>
  );
}
