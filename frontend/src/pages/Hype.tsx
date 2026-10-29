import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import Refresh from "@mui/icons-material/Refresh";
import WhatshotOutlined from "@mui/icons-material/WhatshotOutlined";
import { useCallback } from "react";
import { api, type HypeEntry, type HypeResponse } from "../api";
import { useFeedback } from "../components/feedback";
import { type FilterColumn, useTableFilters } from "../components/TableFilters";
import { ActionButton, DataTable, EmptyState, Na, Num, PageHeader, Pill, V } from "../components/ui";
import { GLYPH, GROUP_LABEL, biasClass, fmtCompact, fmtPct, fmtSigned, fmtWhen } from "../lib/format";
import { useTaskData } from "../lib/useTask";

const SOURCE_LABEL: Record<string, string> = {
  coingecko_trending: "CoinGecko trending",
  geckoterminal: "DEX trending",
  reddit: "Reddit",
  binance_volume: "Volume jump",
  binance_oi: "Open interest",
};

function moveOf(e: HypeEntry): string {
  if (e.rank_yesterday === null || e.rank_yesterday === undefined) return "New";
  const move = e.rank_yesterday - e.rank;
  return move > 0 ? "Up" : move < 0 ? "Down" : "Same";
}

/** WL-127: a filter for every column; the volume in millions so the numbers stay short. */
const HYPE_FILTERS: FilterColumn<HypeEntry>[] = [
  { key: "rank", label: "#", kind: "range", get: (e) => e.rank },
  { key: "coin", label: "Coin or name", kind: "text", get: (e) => `${e.base} ${e.symbol} ${e.name ?? ""}` },
  { key: "listed", label: "On Binance spot", kind: "choice", get: (e) => (e.on_binance ? "Listed" : "Not listed") },
  { key: "hype", label: "Hype", kind: "range", get: (e) => e.hype_score },
  { key: "move", label: "Vs yesterday", kind: "choice", get: moveOf },
  { key: "sources", label: "Where it shows up", kind: "choice", get: (e) => e.sources.map((s) => s.source), labelOf: (v) => SOURCE_LABEL[v] ?? v },
  { key: "volume", label: "24h volume ($M)", kind: "range", get: (e) => (e.volume_usd === null || e.volume_usd === undefined ? null : e.volume_usd / 1e6) },
  { key: "vol_change", label: "Volume vs yesterday %", kind: "range", get: (e) => e.volume_change_pct },
  { key: "oi", label: "OI 1d %", kind: "range", get: (e) => e.oi_change_pct },
  { key: "price", label: "24h price %", kind: "range", get: (e) => e.price_change_pct },
  { key: "group", label: "Group", kind: "choice", get: (e) => e.coin_group, labelOf: (v) => GROUP_LABEL[v] ?? v },
  { key: "confluence", label: "Confluence 1h", kind: "range", get: (e) => e.confluence },
  { key: "side", label: "Confluence side", kind: "choice", get: (e) => e.side },
];
const hypeText = (e: HypeEntry) => `${e.base} ${e.symbol} ${e.name ?? ""} ${e.sources.map((s) => `${SOURCE_LABEL[s.source] ?? s.source} ${s.detail ?? ""}`).join(" ")}`;
const NO_ENTRIES: HypeEntry[] = [];

function RankMove({ e }: Readonly<{ e: HypeEntry }>) {
  if (e.rank_yesterday === null || e.rank_yesterday === undefined) {
    return (
      <Typography variant="caption" sx={{ color: "text.secondary" }}>
        new
      </Typography>
    );
  }
  const move = e.rank_yesterday - e.rank;
  return (
    <Typography variant="caption" sx={{ color: "text.secondary" }}>
      {move > 0 ? `↑ ${String(move)}` : move < 0 ? `↓ ${String(-move)}` : "="} vs yesterday
    </Typography>
  );
}

function Confluence({ e }: Readonly<{ e: HypeEntry }>) {
  if (!e.on_binance) return <Na reason="Not listed on Binance spot" />;
  if (e.confluence === null || e.confluence === undefined) return <Na reason="Not enough 1h candles" />;
  const cls = biasClass(e.side);
  return (
    <Pill
      glyph={GLYPH[cls]}
      label={fmtSigned(e.confluence) ?? ""}
      tone={cls === "buy" ? "buy" : cls === "sell" ? "sell" : "neutral"}
      title={`1h score ${fmtSigned(e.confluence) ?? ""} / 10, prefers ${e.side ?? "neither side"}`}
    />
  );
}

/** Coins people suddenly talk about or trade, refreshed daily at 16:30 PKT (WL-042). A lead, not a signal. */
export default function Hype({
  active,
  onOpenPair,
}: Readonly<{ active: boolean; onOpenPair: (symbol: string, exchange: string, tv: string) => void }>) {
  const { toast } = useFeedback();
  const load = useCallback(() => api.hype(), []);
  const taskOf = useCallback((d: HypeResponse) => d.task, []);
  const { data, error, refresh } = useTaskData(load, taskOf, active);
  const running = Boolean(data?.task.running);
  const { shown, bar } = useTableFilters("cca_hype_filters", data?.entries ?? NO_ENTRIES, HYPE_FILTERS, hypeText, "coins");

  async function rebuild() {
    try {
      await api.runHype();
      toast("Building the hype radar from trending lists, Reddit, volume and open interest.");
      await refresh();
    } catch (err) {
      toast(`Hype radar: ${(err as Error).message}`);
    }
  }

  return (
    <Stack spacing={2}>
      <PageHeader
        title="Hype radar"
        subtitle={
          data?.day
            ? `Radar for ${data.day}. Hype is a lead, not a signal: check the confluence and liquidity before trading.`
            : "Built daily at 16:30 PKT from free sources. Hype is a lead, not a signal."
        }
        actions={
          <ActionButton icon={<Refresh />} primary busy={running} busyLabel="Building…" onClick={() => void rebuild()}>
            Rebuild radar
          </ActionButton>
        }
      />
      {data ? (
        <Stack direction="row" spacing={0.75} useFlexGap sx={{ flexWrap: "wrap" }} aria-label="Sources">
          {data.sources.map((s) => {
            const ok = s.available !== false;
            const title = ok
              ? `${SOURCE_LABEL[s.name] ?? s.name}: ${String(s.items ?? 0)} items, ${fmtWhen(s.fetched_at ?? undefined) ?? "unknown time"}${s.error ? `. ${s.error}` : ""}`
              : `${SOURCE_LABEL[s.name] ?? s.name}: ${s.error ?? "unavailable"}`;
            return <Pill key={s.name} glyph={ok ? "✓" : "✕"} label={SOURCE_LABEL[s.name] ?? s.name} tone={ok ? "neutral" : "warn"} title={title} />;
          })}
        </Stack>
      ) : null}
      {data?.task.error ? <Alert severity="warning">Last build failed: {data.task.error}</Alert> : null}
      {error ? <Alert severity="warning">Hype radar unavailable: {error}</Alert> : null}
      <Card>
        {!data && !error ? <Skeleton height={160} sx={{ mx: 2 }} /> : null}
        {data && !data.entries.length ? <EmptyState icon={<WhatshotOutlined />} text="No radar yet. Select Rebuild radar." /> : null}
        {data?.entries.length ? <Box sx={{ p: 2, pb: 1 }}>{bar}</Box> : null}
        {data?.entries.length && !shown.length ? <EmptyState icon={<WhatshotOutlined />} text="No coin matches the search and filters." /> : null}
        {shown.length ? (
          <DataTable minWidth={1080}>
            <TableHead>
              <TableRow>
                <TableCell>#</TableCell>
                <TableCell>Coin</TableCell>
                <TableCell align="right">Hype</TableCell>
                <TableCell>Where it shows up</TableCell>
                <TableCell align="right">24h volume</TableCell>
                <TableCell align="right">Volume vs yesterday</TableCell>
                <TableCell align="right">OI 1d</TableCell>
                <TableCell align="right">24h price</TableCell>
                <TableCell>Group</TableCell>
                <TableCell>Confluence 1h</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {shown.map((e) => (
                <TableRow key={e.symbol} hover>
                  <TableCell>
                    <Num>{e.rank}</Num>
                  </TableCell>
                  <TableCell>
                    {e.on_binance ? (
                      <Tooltip title={`Open ${e.symbol} on the desk`}>
                        <Typography
                          component="button"
                          onClick={() => onOpenPair(e.symbol, "BINANCE", `BINANCE:${e.symbol}`)}
                          sx={{ all: "unset", cursor: "pointer", fontWeight: 700, fontFamily: (t) => t.typography.fontFamilyMono, "&:hover": { color: "primary.main" }, "&:focus-visible": { outline: 2, outlineColor: "primary.main" } }}
                        >
                          {e.base}
                        </Typography>
                      </Tooltip>
                    ) : (
                      <Num sx={{ fontWeight: 700 }}>{e.base}</Num>
                    )}
                    <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                      {e.name ?? (e.on_binance ? e.symbol : "Not on Binance spot")}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Num sx={{ fontWeight: 700 }}>{e.hype_score.toFixed(1)}</Num>
                    <div>
                      <RankMove e={e} />
                    </div>
                  </TableCell>
                  <TableCell sx={{ whiteSpace: "normal", minWidth: 220 }}>
                    <Stack direction="row" spacing={0.5} useFlexGap sx={{ flexWrap: "wrap" }}>
                      {e.sources.map((s, i) => (
                        <Chip key={`${s.source}-${String(i)}`} size="small" variant="outlined" label={SOURCE_LABEL[s.source] ?? s.source} title={s.detail ?? undefined} />
                      ))}
                    </Stack>
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtCompact(e.volume_usd, "$")} reason="Not on Binance spot" />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtPct(e.volume_change_pct, 0)} reason="No stored volume from yesterday" />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtPct(e.oi_change_pct, 0)} reason="No USD-M futures or not checked" />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtPct(e.price_change_pct, 1)} reason="Not on Binance spot" />
                  </TableCell>
                  <TableCell>{e.coin_group ? (GROUP_LABEL[e.coin_group] ?? e.coin_group) : <Na reason="Not on Binance spot" />}</TableCell>
                  <TableCell>
                    <Confluence e={e} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </DataTable>
        ) : null}
      </Card>
      <Typography variant="caption" sx={{ color: "text.secondary" }}>
        Score: CoinGecko trending up to 4, a trending DEX pool 2, Reddit 1 per post title up to 5, volume jump up to 3, open interest jump up to 2, a
        24h move over 20% 1. X (Twitter) needs a paid API and is not included.
      </Typography>
    </Stack>
  );
}
