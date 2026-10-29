import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import Slider from "@mui/material/Slider";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import Close from "@mui/icons-material/Close";
import { useState } from "react";
import { api, type MarginMode, type Pick, type Wallet } from "../api";
import { fmtFixed, fmtPx, fmtSigned } from "../lib/format";
import { oneOf, usePref } from "../lib/storage";
import {
  type Outcome,
  type PositionInput,
  type Side,
  cleanDecimal,
  liquidatedBeforeStop,
  liquidation,
  marginForRisk,
  maxSafeLeverage,
  notional,
  outcomeAt,
  quantity,
  toDecimalText,
} from "../lib/position";
import { BookTradeDialog, PaperWalletPicker } from "./WalletDialogs";
import { useFeedback } from "./feedback";
import { ActionButton, DataTable, Num, V } from "./ui";

const num = (s: string) => {
  const n = Number(s.replace(",", "."));
  return Number.isFinite(n) ? n : Number.NaN;
};

function usdt(n: number): string | null {
  return Number.isFinite(n) ? `${fmtFixed(n, 2) ?? ""} USDT` : null;
}

/** Profit green with ▲, loss red with ▼: colour plus glyph (ruleset 9). */
function Pnl({ o }: Readonly<{ o: Outcome }>) {
  const up = o.pnl >= 0;
  return (
    <Num sx={{ color: up ? "success.main" : "error.main", fontWeight: 700 }}>
      {up ? "▲ " : "▼ "}
      {fmtSigned(o.pnl, 2)} USDT ({fmtSigned(o.roe, 1)}%)
    </Num>
  );
}

function reasonFor(label: string): string {
  if (label === "Your exit") return "Enter an exit price";
  if (label === "Liquidation") return "The cross balance covers any price";
  return `No ${label.toLowerCase()} set`;
}

function Field({
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
      sx={{ flex: 1, minWidth: 140 }}
    />
  );
}

/** Try a futures position on a pick: margin, leverage, fees, liquidation and the result at each price (WL-060).
 * A simulation only: nothing is sent to Binance. */
export default function PositionDialog({ pick, onClose }: Readonly<{ pick: Pick; onClose: () => void }>) {
  const phone = useMediaQuery((t) => t.breakpoints.down("sm"));
  const { toast, ask } = useFeedback();
  const [opening, setOpening] = useState(false);
  const [side, setSide] = useState<Side>(pick.side);
  const [entry, setEntry] = useState(toDecimalText(pick.entry));
  const [stop, setStop] = useState(toDecimalText(pick.stop));
  const [target, setTarget] = useState(toDecimalText(pick.target));
  const [exit, setExit] = useState(toDecimalText(pick.target));
  const [margin, setMargin] = useState("100");
  const [leverage, setLeverage] = useState(10);
  const [fee, setFee] = useState("0.05");
  const [mmr, setMmr] = useState("0.5");
  const [risk, setRisk] = useState("10");
  const [wallets, setWallets] = useState<Wallet[] | null>(null);
  // WL-110: margin mode as on Binance; cross puts the cross balance behind the position.
  const [mode, setMode] = usePref<MarginMode>("cca_position_mode", "isolated", oneOf("isolated", "cross"));
  const [crossBalance, setCrossBalance] = usePref("cca_position_cross_balance", "1000");
  const cross = mode === "cross";
  const [paperWallet, setPaperWallet] = usePref("cca_position_wallet", 0); // WL-150: 0 for no wallet

  /** Book what you opened on Binance into a wallet (WL-063), prefilled from this calculator. */
  async function bookInWallet() {
    try {
      setWallets((await api.wallets()).wallets);
    } catch (err) {
      toast(`Wallets unavailable: ${(err as Error).message}`);
    }
  }

  const p: PositionInput = {
    side,
    entry: num(entry),
    margin: num(margin),
    leverage,
    feeRate: num(fee) / 100,
    mmr: num(mmr) / 100,
    mode,
    crossBalance: cross ? num(crossBalance) : undefined,
  };
  const crossShort = cross && !(num(crossBalance) >= num(margin));
  const s = num(stop);
  const t = num(target);
  const x = num(exit);
  // Stop and target are optional (WL-061): an empty field means none.
  const hasStop = stop !== "" && s > 0;
  const hasTarget = target !== "" && t > 0;
  const valid = [p.entry, p.margin, p.feeRate, p.mmr].every((v) => Number.isFinite(v) && v >= 0) && p.entry > 0 && p.margin > 0;
  const wrongStop = valid && hasStop && (side === "Buy" ? s >= p.entry : s <= p.entry);
  const wrongTarget = valid && hasTarget && (side === "Buy" ? t <= p.entry : t >= p.entry);
  const liq = valid ? liquidation(p) : Number.NaN;
  const liqFirst = valid && hasStop && !wrongStop && liquidatedBeforeStop(p, s);
  const safe = valid && hasStop ? maxSafeLeverage(side, p.entry, s, p.mmr) : null;
  const riskMargin = valid && hasStop ? marginForRisk(side, p.entry, s, num(risk), leverage, p.feeRate) : null;
  const rows: [string, Outcome | null][] = valid
    ? [
        ["Target", hasTarget ? outcomeAt(p, t) : null],
        ["Stop", hasStop ? outcomeAt(p, s) : null],
        ["Your exit", Number.isFinite(x) && x > 0 ? outcomeAt(p, x) : null],
        ["Liquidation", Number.isNaN(liq) ? null : outcomeAt(p, liq)],
      ]
    : [];

  /** Store it as a leveraged paper position at the live price (WL-061); the paper job then tracks it. */
  async function openPaper() {
    const ok = await ask({
      title: `Open a paper ${side === "Buy" ? "long" : "short"} on ${pick.symbol}?`,
      text: `${fmtFixed(p.margin, 2) ?? ""} USDT margin at ${String(leverage)}x, ${cross ? `cross on ${crossBalance} USDT` : "isolated"}, stop ${stop || "none"}, target ${target || "none"}. It opens at the live price, not the entry field, and is closed at the stop, target or liquidation by the paper check every 4 hours.`,
      okLabel: "Open paper position",
    });
    if (!ok) return;
    setOpening(true);
    try {
      const pos = await api.openPosition({
        symbol: pick.symbol,
        market: pick.market,
        side,
        stop: stop ? s : null,
        target: target ? t : null,
        margin: p.margin,
        leverage,
        fee_rate: p.feeRate,
        mmr: p.mmr,
        pick_day: pick.day,
        style: pick.style,
        margin_mode: mode,
        cross_balance: cross ? num(crossBalance) : null,
        wallet_id: paperWallet || null,
      });
      toast(`Paper ${side === "Buy" ? "long" : "short"} ${pos.symbol} opened at ${fmtPx(pos.entry) ?? ""}, liquidation ${fmtPx(pos.liquidation) ?? ""}. See Paper trades.`);
      onClose();
    } catch (err) {
      toast(`Not opened: ${(err as Error).message}`);
    } finally {
      setOpening(false);
    }
  }

  return (
    <Dialog open onClose={onClose} fullScreen={phone} fullWidth maxWidth="md" aria-labelledby="posTitle">
      <DialogTitle id="posTitle" sx={{ display: "flex", alignItems: "center", gap: 1, pr: 1 }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          Try a position: {pick.symbol}
          <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
            USD-M futures, {cross ? "cross" : "isolated"} margin. Paper only: nothing is sent to Binance.
          </Typography>
        </Box>
        <IconButton aria-label="Close" onClick={onClose}>
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5}>
          <ToggleButtonGroup exclusive value={side} onChange={(_e, v: Side | null) => v && setSide(v)} aria-label="Side" size="small">
            <ToggleButton value="Buy" sx={{ px: 3, "&.Mui-selected": { color: "success.main" } }}>
              ▲ Long
            </ToggleButton>
            <ToggleButton value="Sell" sx={{ px: 3, "&.Mui-selected": { color: "error.main" } }}>
              ▼ Short
            </ToggleButton>
          </ToggleButtonGroup>

          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ alignItems: { sm: "center" } }}>
            <ToggleButtonGroup exclusive value={mode} onChange={(_e, v: MarginMode | null) => v && setMode(v)} aria-label="Margin mode" size="small">
              <ToggleButton value="isolated" sx={{ px: 2 }}>
                Isolated
              </ToggleButton>
              <ToggleButton value="cross" sx={{ px: 2 }}>
                Cross
              </ToggleButton>
            </ToggleButtonGroup>
            {cross ? (
              <Field label="Cross balance" value={crossBalance} onChange={setCrossBalance} unit="USDT" help="The wallet balance behind every cross position" />
            ) : null}
            <Typography variant="caption" sx={{ color: "text.secondary", flex: 2 }}>
              {cross
                ? "Cross: the whole balance backs the position, so liquidation is further away but a loss can exceed the margin. Other open cross paper positions are counted when it opens."
                : "Isolated: only the margin is at risk; liquidation comes sooner."}
            </Typography>
          </Stack>

          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
            <Field label="Entry" value={entry} onChange={setEntry} />
            <Field label="Stop" value={stop} onChange={setStop} />
            <Field label="Target" value={target} onChange={setTarget} />
            <Field label="Your exit" value={exit} onChange={setExit} help="Any price: see what happens" />
          </Stack>

          <Stack direction={{ xs: "column", sm: "row" }} spacing={3} sx={{ alignItems: { sm: "flex-start" } }}>
            <Field label="Margin" value={margin} onChange={setMargin} unit="USDT" help="What you put up" />
            <Box sx={{ flex: 2, px: 1 }}>
              <Typography variant="body2" gutterBottom>
                Leverage: <Num sx={{ fontWeight: 700 }}>{leverage}x</Num>
                {safe ? (
                  <Typography component="span" variant="caption" sx={{ color: "text.secondary" }}>
                    {" "}
                    · up to {safe}x keeps liquidation beyond the stop
                  </Typography>
                ) : null}
              </Typography>
              <Slider
                value={leverage}
                min={1}
                max={125}
                step={1}
                marks={[1, 5, 10, 20, 50, 75, 100, 125].map((v) => ({ value: v, label: `${String(v)}x` }))}
                onChange={(_e, v) => setLeverage(v as number)}
                aria-label="Leverage"
              />
            </Box>
          </Stack>

          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
            <Field label="Fee per side" value={fee} onChange={setFee} unit="%" help="Binance taker 0.05%, maker 0.02%" />
            <Field label="Maintenance margin" value={mmr} onChange={setMmr} unit="%" help="Tier 1: about 0.4% to 1% by coin" />
          </Stack>

          {!valid ? <Alert severity="warning">Enter positive numbers for entry, margin, fee and maintenance margin. Stop and target may be left empty.</Alert> : null}
          {crossShort ? <Alert severity="warning">The cross balance must be at least the margin.</Alert> : null}
          {wrongStop ? <Alert severity="warning">The stop is on the wrong side of the entry for a {side === "Buy" ? "long" : "short"}.</Alert> : null}
          {wrongTarget ? <Alert severity="warning">The target is on the wrong side of the entry for a {side === "Buy" ? "long" : "short"}.</Alert> : null}
          {liqFirst ? (
            <Alert severity="error">
              At {leverage}x you are liquidated at {fmtPx(liq)} before the stop at {fmtPx(s)} is reached.
              {safe ? ` Use ${String(safe)}x or less.` : ""}
            </Alert>
          ) : null}

          {valid ? (
            <Stack direction={{ xs: "column", sm: "row" }} spacing={3} sx={{ flexWrap: "wrap" }}>
              <Box>
                <Typography variant="caption" sx={{ color: "text.secondary" }}>
                  Position size
                </Typography>
                <Typography>
                  <V value={usdt(notional(p))} />
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ color: "text.secondary" }}>
                  Quantity
                </Typography>
                <Typography>
                  <Num>
                    {fmtFixed(quantity(p), 6)} {pick.symbol.replace(/USDT$|USDC$/, "")}
                  </Num>
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ color: "text.secondary" }}>
                  Liquidation price
                </Typography>
                <Typography>
                  <V value={fmtPx(liq)} reason="The cross balance covers any price" />
                </Typography>
              </Box>
            </Stack>
          ) : null}

          {rows.length ? (
            <DataTable minWidth={560}>
              <TableHead>
                <TableRow>
                  <TableCell>Close at</TableCell>
                  <TableCell align="right">Price</TableCell>
                  <TableCell align="right">Move</TableCell>
                  <TableCell align="right">Fees</TableCell>
                  <TableCell align="right">Profit or loss</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map(([label, o]) => (
                  <TableRow key={label}>
                    <TableCell>{label}</TableCell>
                    <TableCell align="right">{o ? <V value={fmtPx(o.price)} /> : <V value={null} reason={reasonFor(label)} />}</TableCell>
                    <TableCell align="right">{o ? <Num>{fmtSigned(o.move, 2)}%</Num> : null}</TableCell>
                    <TableCell align="right">{o ? <V value={usdt(o.fees)} /> : null}</TableCell>
                    <TableCell align="right">{o ? <Pnl o={o} /> : null}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </DataTable>
          ) : null}

          {valid && hasStop && !wrongStop ? (
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ alignItems: { sm: "center" } }}>
              <Field label="Risk per trade" value={risk} onChange={setRisk} unit="USDT" help="What you accept to lose at the stop" />
              <Typography variant="body2" sx={{ flex: 2 }}>
                {riskMargin === null ? (
                  "Enter a risk amount above zero."
                ) : (
                  <>
                    To lose {fmtFixed(num(risk), 2)} USDT at the stop with {leverage}x, put up <Num sx={{ fontWeight: 700 }}>{fmtFixed(riskMargin, 2)} USDT</Num> margin
                    (position {fmtFixed(riskMargin * leverage, 2)} USDT).
                  </>
                )}
              </Typography>
              <Button variant="outlined" disabled={riskMargin === null} onClick={() => riskMargin !== null && setMargin(riskMargin.toFixed(2))}>
                Use this margin
              </Button>
            </Stack>
          ) : null}

          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            Estimate: Binance also charges funding every 8 hours and raises the maintenance margin for large positions, so its liquidation price can differ slightly.
            Numbers take at most 6 decimals.
          </Typography>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ justifyContent: "flex-end", alignItems: { sm: "center" } }}>
            <Box sx={{ flex: 1 }}>
              <PaperWalletPicker value={paperWallet} onChange={setPaperWallet} label="Paper position counts in" />
            </Box>
            <ActionButton disabled={!valid} title="You opened it on Binance yourself: book it in a wallet" onClick={() => void bookInWallet()}>
              Book in a wallet
            </ActionButton>
            <ActionButton primary busy={opening} busyLabel="Opening…" disabled={!valid || wrongStop || wrongTarget || liqFirst || crossShort} onClick={() => void openPaper()}>
              Open paper position
            </ActionButton>
          </Stack>
        </Stack>
      </DialogContent>
      {wallets ? (
        <BookTradeDialog
          wallets={wallets}
          prefill={{
            symbol: pick.symbol,
            side,
            entry: p.entry,
            stop: hasStop ? s : null,
            target: hasTarget ? t : null,
            margin: p.margin,
            leverage,
            pick_day: pick.day,
            style: pick.style,
          }}
          onClose={() => setWallets(null)}
        />
      ) : null}
    </Dialog>
  );
}
