import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import TravelExploreOutlined from "@mui/icons-material/TravelExploreOutlined";
import { useEffect, useState, type ReactNode } from "react";
import { api, type DeepDive, type SourceState, type Wall, type WallChange } from "../api";
import { fmtCompact, fmtFixed, fmtPct, fmtPx, fmtWhen } from "../lib/format";
import { Pill, SectionCard, V, monoSx } from "./ui";

const CHANGE_GLYPH: Record<WallChange["change"], string> = { new: "+", gone: "✕", grown: "▲", shrunk: "▼" };

function WallTable({ side, walls }: Readonly<{ side: "sell" | "buy"; walls: Wall[] }>) {
  const title = side === "sell" ? "Sell walls (above the price)" : "Buy walls (below the price)";
  return (
    <Box sx={{ minWidth: 0 }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", mb: 0.5 }}>
        <Pill glyph={side === "sell" ? "▼" : "▲"} label={side === "sell" ? "Sell" : "Buy"} tone={side} />
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {title}
        </Typography>
      </Stack>
      {walls.length ? (
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Price</TableCell>
              <TableCell align="right">Distance</TableCell>
              <TableCell align="right">Size</TableCell>
              <TableCell align="right">× median</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {walls.map((w) => (
              <TableRow key={w.price}>
                <TableCell sx={monoSx}>{fmtPx(w.price)}</TableCell>
                <TableCell align="right">
                  <V value={fmtPct(w.distance_pct, 2)} />
                </TableCell>
                <TableCell align="right">
                  <V value={fmtCompact(w.usd, "$")} />
                </TableCell>
                <TableCell align="right">
                  <V value={fmtFixed(w.x_median, 1)} reason="No median" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          No wall in the window: the book is even on this side.
        </Typography>
      )}
    </Box>
  );
}

function Fact({ label, value, reason }: Readonly<{ label: string; value: string | null; reason?: string }>) {
  return (
    <Box>
      <Typography variant="caption" sx={{ color: "text.secondary" }}>
        {label}
      </Typography>
      <Typography variant="body2" component="div">
        <V value={value} reason={reason} />
      </Typography>
    </Box>
  );
}

function source(name: string, s: SourceState) {
  return (
    <Pill key={name} glyph={s.available ? "✓" : "✕"} label={name} tone={s.available ? "neutral" : "warn"} title={s.available ? `${name}: ok` : `${name}: ${s.error ?? "unavailable"}`} />
  );
}

function Body({ d }: Readonly<{ d: DeepDive }>) {
  const t = d.token ?? { available: false };
  const why = t.available ? "Not published by CoinGecko" : `CoinGecko: ${t.error ?? "unavailable"}`;
  const dv = d.derivatives ?? { available: false };
  const dwhy = dv.available ? "Not available" : `Binance futures: ${dv.error ?? "unavailable"}`;
  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={0.5} useFlexGap sx={{ flexWrap: "wrap" }}>
        {Object.values(d.venues ?? {}).map((v) => source(v.label, v))}
        {source("CoinGecko", t)}
        {source("Binance derivatives", dv)}
        {source("Holders", d.holders)}
        {source("Unlocks", d.unlocks)}
      </Stack>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "minmax(0, 1fr)", md: "repeat(2, minmax(0, 1fr))" } }}>
        <WallTable side="sell" walls={d.walls?.sell ?? []} />
        <WallTable side="buy" walls={d.walls?.buy ?? []} />
      </Box>
      {d.previous_at ? (
        <Box>
          <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
            Since the last look ({fmtWhen(d.previous_at) ?? "earlier"})
          </Typography>
          {d.changes?.length ? (
            <Stack direction="row" spacing={0.5} useFlexGap sx={{ flexWrap: "wrap" }}>
              {(d.changes ?? []).map((c) => (
                <Pill
                  key={`${c.side}-${String(c.price)}-${c.change}`}
                  glyph={CHANGE_GLYPH[c.change]}
                  tone={c.side}
                  label={`${c.side} ${fmtPx(c.price) ?? ""} ${c.change}`}
                  title={[c.usd_before === undefined ? null : `before ${fmtCompact(c.usd_before, "$") ?? ""}`, c.usd === undefined ? null : `now ${fmtCompact(c.usd, "$") ?? ""}`].filter(Boolean).join(", ")}
                />
              ))}
            </Stack>
          ) : (
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              The same walls, none grew or shrank by 25% or more.
            </Typography>
          )}
        </Box>
      ) : null}
      <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "repeat(2, minmax(0, 1fr))", md: "repeat(4, minmax(0, 1fr))" } }}>
        <Fact label="Market cap" value={fmtCompact(t.market_cap, "$")} reason={why} />
        <Fact label="Fully diluted" value={fmtCompact(t.fdv, "$")} reason={why} />
        <Fact label="Volume 24 h" value={fmtCompact(t.volume_24h, "$")} reason={why} />
        <Fact label="Rank" value={t.rank ? `#${String(t.rank)}` : null} reason={why} />
        <Fact label="Circulating" value={fmtCompact(t.circulating_supply)} reason={why} />
        <Fact label="Max supply" value={fmtCompact(t.max_supply)} reason={t.available ? "No max supply" : why} />
        <Fact label="7 d / 30 d" value={t.change_7d_pct == null ? null : `${fmtPct(t.change_7d_pct) ?? ""} / ${fmtPct(t.change_30d_pct) ?? "n/a"}`} reason={why} />
        <Fact label="From ATH" value={fmtPct(t.ath_change_pct)} reason={why} />
        <Fact label="Funding" value={fmtPct(dv.funding_pct, 4)} reason={dwhy} />
        <Fact label="Open interest" value={fmtCompact(dv.open_interest_usd, "$")} reason={dwhy} />
        <Fact label="Top traders long/short" value={fmtFixed(dv.top_long_short, 2)} reason={dwhy} />
        <Fact label="Sentiment up" value={t.sentiment_up_pct == null ? null : `${fmtFixed(t.sentiment_up_pct, 0) ?? ""}%`} reason={why} />
      </Box>
      {t.categories?.length ? (
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          {t.name ?? d.base}: {t.categories.join(", ")}
        </Typography>
      ) : null}
    </Stack>
  );
}

/** Walls on several exchanges and token data for the pair on the desk, on request only (WL-083). */
export default function DeepDiveCard({ symbol, active }: Readonly<{ symbol: string; active: boolean }>) {
  const [dive, setDive] = useState<DeepDive | null>(null);
  const [count, setCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState("");

  useEffect(() => {
    if (!active || loaded === symbol) return;
    setLoaded(symbol);
    setDive(null);
    setError(null);
    api
      .deepDive(symbol)
      .then((h) => {
        setDive(h.latest);
        setCount(h.history.length);
      })
      .catch((err: unknown) => setError((err as Error).message));
  }, [active, symbol, loaded]);

  const run = () => {
    setBusy(true);
    setError(null);
    api
      .runDeepDive(symbol)
      .then((d) => {
        setDive(d);
        setCount((c) => c + 1);
      })
      .catch((err: unknown) => setError((err as Error).message))
      .finally(() => setBusy(false));
  };

  let body: ReactNode;
  if (dive) body = <Body d={dive} />;
  else
    body = (
      <Typography variant="body2" sx={{ color: "text.secondary" }}>
        No deep dive for {symbol} yet. It reads the order books of Binance, Bybit, OKX and KuCoin, CoinGecko and Binance futures, and keeps every look so walls can be compared.
      </Typography>
    );

  return (
    <SectionCard
      title="Deep dive: walls and token data"
      icon={<TravelExploreOutlined />}
      right={
        <Button size="small" variant="outlined" onClick={run} disabled={busy}>
          {busy ? "Looking…" : "Run deep dive"}
        </Button>
      }
    >
      {error ? (
        <Alert severity="warning" sx={{ mb: 1.5 }}>
          Deep dive failed: {error}
        </Alert>
      ) : null}
      {body}
      {dive ? (
        <Typography variant="caption" component="p" sx={{ color: "text.secondary", mt: 1.5, mb: 0 }}>
          Looked {fmtWhen(dive.created_at) ?? "at an unknown time"}, {count} stored for {dive.symbol}. A wall is a {dive.settings?.bin_pct ?? "—"}% price band at least {dive.settings?.wall_x ?? "—"}× the median band of its side, within {dive.settings?.window_pct ?? "—"}% of the price; sizes in USD, all venues together.
        </Typography>
      ) : null}
    </SectionCard>
  );
}
