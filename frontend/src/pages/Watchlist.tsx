import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import FormControlLabel from "@mui/material/FormControlLabel";
import IconButton from "@mui/material/IconButton";
import LinearProgress from "@mui/material/LinearProgress";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import Add from "@mui/icons-material/Add";
import Close from "@mui/icons-material/Close";
import DragIndicator from "@mui/icons-material/DragIndicator";
import FormatListBulleted from "@mui/icons-material/FormatListBulleted";
import KeyboardArrowDown from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUp from "@mui/icons-material/KeyboardArrowUp";
import Refresh from "@mui/icons-material/Refresh";
import { useState } from "react";
import { api, type WatchlistList, type WatchlistQuote, type WatchlistResponse } from "../api";
import PairSearch from "../components/PairSearch";
import { ChangeHeads, Changes, DROP_SX, PairName, SortHead, sortLabel, sortedItems, useDragSort, useListActions, useQuotes, useWatchlists } from "../components/Watchlists";
import { useFeedback } from "../components/feedback";
import { ActionButton, BiasPill, DataTable, EmptyState, KpiStrip, Na, Num, PageHeader, Pill, V, useSort } from "../components/ui";
import { fmtPx, fmtSigned, fmtWhen, humanize } from "../lib/format";
import { usePref } from "../lib/storage";

/** One list to manage: add pairs, drag or move them, take them off, rename, show in the panel, delete (archive). */
/** WL-152: drag handle, pair, price, six periods, actions; a narrow card scrolls sideways.
 * WL-153: 84px periods so "▲ 179.43%" stays inside its column under its header. */
const ROW_COLS = "28px minmax(160px, 1fr) 112px repeat(6, 84px) 108px";
const ROW_MIN = 980;

function ListCard({
  list,
  quotes,
  maxItems,
  first,
  last,
  dragProps,
  onMove,
  onOpen,
}: Readonly<{
  list: WatchlistList;
  quotes: Record<string, WatchlistQuote>;
  maxItems: number;
  first: boolean;
  last: boolean;
  dragProps: ReturnType<ReturnType<typeof useDragSort>>;
  onMove: (delta: number) => void;
  onOpen: (symbol: string, exchange?: string) => void;
}>) {
  const { run, orderItems } = useWatchlists();
  const { rename, remove } = useListActions(list);
  const ids = list.items.map((i) => i.id);
  const itemDrag = useDragSort(ids, (next) => orderItems(list.id, next));
  // WL-153: a header click sorts the view; your stored order (drag, arrows) comes back on reset.
  const [sort, onSort, unsort] = useSort(`cca_watch_page_sort_${String(list.id)}`);
  const items = sortedItems(list.items, sort, quotes);
  const full = list.items.length >= maxItems;

  const moveItem = (id: number, delta: number) => {
    const i = ids.indexOf(id);
    const next = ids.filter((x) => x !== id);
    next.splice(i + delta, 0, id);
    orderItems(list.id, next);
  };

  return (
    <Card variant="outlined" sx={[DROP_SX, { minWidth: 0, display: "flex", flexDirection: "column" }]} {...dragProps}>
      <Stack direction="row" spacing={0.5} sx={{ alignItems: "center", px: 1.5, pt: 1, cursor: "grab" }}>
        <DragIndicator fontSize="small" sx={{ color: "text.disabled" }} aria-hidden />
        <Typography variant="h3" component="h3" noWrap sx={{ flex: 1, minWidth: 0 }}>
          {list.name}
        </Typography>
        <Tooltip title="Move the list left">
          <span>
            <IconButton size="small" aria-label={`Move ${list.name} left`} disabled={first} onClick={() => onMove(-1)}>
              <KeyboardArrowUp fontSize="small" sx={{ transform: "rotate(-90deg)" }} />
            </IconButton>
          </span>
        </Tooltip>
        <Tooltip title="Move the list right">
          <span>
            <IconButton size="small" aria-label={`Move ${list.name} right`} disabled={last} onClick={() => onMove(1)}>
              <KeyboardArrowDown fontSize="small" sx={{ transform: "rotate(-90deg)" }} />
            </IconButton>
          </span>
        </Tooltip>
      </Stack>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", px: 1.5, flexWrap: "wrap", rowGap: 0.5 }}>
        <Typography variant="caption" sx={{ color: "text.secondary", flex: 1 }}>
          {list.items.length} of {maxItems} pairs
          {sort ? ` · sorted by ${sortLabel(sort)}` : ""}
        </Typography>
        {sort ? (
          <ActionButton compact onClick={unsort}>
            Your order
          </ActionButton>
        ) : null}
        <FormControlLabel
          sx={{ mr: 0 }}
          control={<Switch size="small" checked={list.is_open} onChange={(e) => void run(() => api.updateWatchlist(list.id, { is_open: e.target.checked }))} />}
          label={<Typography variant="caption">In the panel</Typography>}
        />
      </Stack>
      <Box sx={{ px: 1.5, py: 1 }}>
        {full ? (
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            The list is full ({maxItems} pairs). Take one off to add another.
          </Typography>
        ) : (
          <PairSearch
            exchange="BINANCE"
            placeholder="Add a pair"
            onPickPair={(symbol, exchange) => void run(() => api.addWatchItem(list.id, symbol, exchange ?? "BINANCE"))}
          />
        )}
      </Box>
      <Box sx={{ flex: 1, maxHeight: 520, overflow: "auto", borderTop: 1, borderColor: "divider" }}>
        {list.items.length ? (
          <Box sx={{ display: "grid", gridTemplateColumns: ROW_COLS, gap: 0.75, alignItems: "center", px: 0.5, py: 0.25, minWidth: ROW_MIN, position: "sticky", top: 0, zIndex: 1, bgcolor: "background.paper", borderBottom: 1, borderColor: "divider" }}>
            <span />
            <SortHead id="pair" label="Pair" first="asc" sort={sort} onSort={onSort} />
            <SortHead id="last" label="Price" title="Last traded price" right sort={sort} onSort={onSort} />
            <ChangeHeads sort={sort} onSort={onSort} />
            <span />
          </Box>
        ) : null}
        {list.items.length ? (
          items.map((it, i) => (
            <Box
              key={it.id}
              tabIndex={0}
              {...(sort ? null : itemDrag(it.id))}
              title={sort ? "Sorted by a column: Your order brings back dragging" : "Drag to move it, or Alt plus Up or Down"}
              sx={[
                DROP_SX,
                {
                  display: "grid",
                  gridTemplateColumns: ROW_COLS,
                  minWidth: ROW_MIN,
                  fontSize: "0.8125rem",
                  gap: 0.75,
                  alignItems: "center",
                  pl: 0.5,
                  pr: 0.5,
                  minHeight: { xs: 48, sm: 36 },
                  cursor: sort ? "default" : "grab",
                  "& + &": { borderTop: 1, borderColor: "divider" },
                  "&:hover": { bgcolor: "action.hover" },
                  "&:focus-visible": { outline: 2, outlineOffset: -2, outlineColor: "primary.main" },
                },
              ]}
            >
              <DragIndicator fontSize="small" sx={{ color: "text.disabled", visibility: sort ? "hidden" : undefined }} aria-hidden />
              <Box
                component="button"
                type="button"
                onClick={() => onOpen(it.symbol, it.exchange)}
                sx={{ all: "unset", cursor: "pointer", minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", "&:focus-visible": { outline: 2, outlineColor: "primary.main" } }}
                title={`Open ${it.symbol} on the desk`}
              >
                <PairName item={it} />
              </Box>
              <Num sx={{ fontSize: "0.8125rem", textAlign: "right" }}>{quotes[it.symbol] ? fmtPx(quotes[it.symbol].price) : <Na reason="No Binance ticker for this pair" />}</Num>
              <Changes q={quotes[it.symbol]} />
              <Stack direction="row">
                <IconButton size="small" aria-label={`Move ${it.symbol} up`} disabled={!!sort || i === 0} onClick={() => moveItem(it.id, -1)}>
                  <KeyboardArrowUp fontSize="small" />
                </IconButton>
                <IconButton size="small" aria-label={`Move ${it.symbol} down`} disabled={!!sort || i === list.items.length - 1} onClick={() => moveItem(it.id, 1)}>
                  <KeyboardArrowDown fontSize="small" />
                </IconButton>
                <Tooltip title="Take it off the list (kept stored)">
                  <IconButton size="small" aria-label={`Take ${it.symbol} off ${list.name}`} onClick={() => void run(() => api.removeWatchItem(list.id, it.id))}>
                    <Close fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Stack>
            </Box>
          ))
        ) : (
          <Typography variant="body2" sx={{ color: "text.secondary", p: 1.5 }}>
            No pairs yet. Search above to add up to {maxItems}.
          </Typography>
        )}
      </Box>
      <Stack direction="row" spacing={1} sx={{ p: 1, borderTop: 1, borderColor: "divider", justifyContent: "flex-end" }}>
        <ActionButton compact onClick={() => void rename()}>
          Rename
        </ActionButton>
        <ActionButton compact onClick={() => void remove()}>
          Delete
        </ActionButton>
      </Stack>
    </Card>
  );
}

function ScoreTable({ rows, onOpen }: Readonly<{ rows: WatchlistResponse["rows"]; onOpen: (symbol: string) => void }>) {
  return (
    <DataTable minWidth={980}>
      <TableHead>
        <TableRow>
          <TableCell>Pair</TableCell>
          <TableCell>Quality</TableCell>
          <TableCell>Bias</TableCell>
          <TableCell align="right">Confluence</TableCell>
          <TableCell>Setup</TableCell>
          <TableCell>MTF</TableCell>
          <TableCell>Book</TableCell>
          <TableCell>Liquidity</TableCell>
          <TableCell align="right">Price</TableCell>
          <TableCell />
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map((r) => (
          <TableRow key={r.symbol} hover>
            <TableCell>
              <Num sx={{ fontWeight: 700 }}>{r.symbol}</Num>
            </TableCell>
            <TableCell>
              {r.quality === undefined ? (
                <Na reason={r.error ?? "Not scored"} />
              ) : (
                <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                  <LinearProgress variant="determinate" value={Math.max(0, Math.min(100, r.quality))} sx={{ width: 64, height: 6, borderRadius: 3 }} />
                  <Num>{r.quality}</Num>
                </Stack>
              )}
            </TableCell>
            <TableCell>{r.error ? <Na reason={r.error} /> : <BiasPill bias={r.bias} />}</TableCell>
            <TableCell align="right">
              <V value={fmtSigned(r.confluence)} />
            </TableCell>
            <TableCell>
              {r.setup ? (
                <Stack direction="row" spacing={0.5}>
                  <Chip size="small" label={humanize(r.setup)} />
                  {r.trade_allowed === false ? <Pill glyph="!" label="chop" tone="warn" /> : null}
                </Stack>
              ) : (
                <Na />
              )}
            </TableCell>
            <TableCell>{r.mtf_alignment ? humanize(r.mtf_alignment).toLowerCase() : <Na />}</TableCell>
            <TableCell>{r.book_bias ?? <Na reason="Depth unavailable" />}</TableCell>
            <TableCell>{r.liq_bias ?? <Na reason="No futures data" />}</TableCell>
            <TableCell align="right">
              <V value={fmtPx(r.price)} />
            </TableCell>
            <TableCell align="right">
              <Button size="small" variant="outlined" color="inherit" sx={{ borderColor: "divider" }} onClick={() => onOpen(r.symbol)}>
                Open
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </DataTable>
  );
}

/** Watchlists (WL-149): up to 4 lists of 40 pairs, sorted by drag; the chosen list is scored for setup quality. */
export default function Watchlist({
  timeframe,
  onOpen,
}: Readonly<{ timeframe: string; onOpen: (symbol: string, exchange?: string) => void }>) {
  const { data, error: listError, run, orderLists } = useWatchlists();
  const { ask } = useFeedback();
  const [showArchived, setShowArchived] = usePref("cca_watch_archived", false);
  const [archived, setArchived] = useState<WatchlistList[] | null>(null);
  const [scoreId, setScoreId] = usePref<number>("cca_watch_score_list", 0);
  const [scored, setScored] = useState<WatchlistResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lists = data?.watchlists ?? [];
  const maxLists = data?.max_lists ?? 4;
  const maxItems = data?.max_items ?? 40;
  const ids = lists.map((w) => w.id);
  const listDrag = useDragSort(ids, orderLists, false);
  const { quotes } = useQuotes(
    lists.flatMap((w) => w.items.map((i) => i.symbol)),
    lists.length > 0,
  );
  const scoreList = lists.find((w) => w.id === scoreId) ?? lists[0];

  const moveList = (id: number, delta: number) => {
    const i = ids.indexOf(id);
    const next = ids.filter((x) => x !== id);
    next.splice(i + delta, 0, id);
    orderLists(next);
  };

  async function loadArchived(on: boolean) {
    setShowArchived(on);
    if (!on) return;
    try {
      setArchived((await api.watchlists(true)).watchlists.filter((w) => w.archived_at));
    } catch {
      setArchived([]);
    }
  }

  async function create() {
    const name = await ask({ title: "New watchlist", label: "Name", input: true, okLabel: "Create" });
    if (typeof name === "string" && name.trim()) await run(() => api.createWatchlist(name.trim(), true), `${name.trim()} created and shown in the panel.`);
  }

  async function score() {
    if (!scoreList) return;
    setBusy(true);
    setError(null);
    try {
      setScored(await api.scoreWatchlist(timeframe, scoreList.items.map((i) => i.symbol)));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const rows = scored?.rows ?? [];
  const top = rows[0];
  const notScored = <Na reason="Not scored yet" />;
  const seconds = Math.max(20, (scoreList?.items.length ?? 10) * 3);

  let table: React.ReactNode;
  if (busy)
    table = (
      <Box sx={{ p: 2 }}>
        <Alert severity="info" variant="outlined" sx={{ mb: 2 }}>
          Scoring {scoreList?.name}. This takes about {seconds} seconds.
        </Alert>
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} height={40} />
        ))}
      </Box>
    );
  else if (error)
    table = (
      <Alert severity="warning" sx={{ m: 2 }}>
        Scoring failed: {error}
      </Alert>
    );
  else if (!scored) table = <EmptyState text="Pick a list and score it: confluence, chop filter, book and liquidity per pair." icon={<FormatListBulleted />} />;
  else if (!rows.length) table = <EmptyState text="No results." />;
  else table = <ScoreTable rows={rows} onOpen={(s) => onOpen(s)} />;

  return (
    <Stack spacing={2}>
      <PageHeader
        title="Watchlists"
        subtitle={`Up to ${String(maxLists)} lists of ${String(maxItems)} pairs. Drag a list or a pair to sort it (or Alt plus an arrow key); click a column header to sort a list by it. Lists switched to In the panel show in the watchlist panel on the right (the icon at the top right opens it).`}
        actions={
          <>
            <ActionButton icon={<Add />} primary={!lists.length} disabled={lists.length >= maxLists} title={lists.length >= maxLists ? `At most ${String(maxLists)} lists: delete one first` : undefined} onClick={() => void create()}>
              New watchlist
            </ActionButton>
            {lists.length ? (
              <ActionButton icon={<Refresh />} primary busy={busy} busyLabel="Scoring…" disabled={!scoreList?.items.length} onClick={() => void score()}>
                Score {scoreList?.name ?? "list"}
              </ActionButton>
            ) : null}
          </>
        }
      />
      {listError ? <Alert severity="warning">Watchlists unavailable: {listError}</Alert> : null}
      {!data && !listError ? <Skeleton height={200} /> : null}
      {data && !lists.length ? (
        <Card>
          <EmptyState icon={<FormatListBulleted />} text={`No watchlists. Create one and add up to ${String(maxItems)} pairs.`} />
        </Card>
      ) : null}
      {lists.length ? (
        <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 900px), 1fr))", alignItems: "start" }}>
          {lists.map((w, i) => (
            <ListCard
              key={w.id}
              list={w}
              quotes={quotes}
              maxItems={maxItems}
              first={i === 0}
              last={i === lists.length - 1}
              dragProps={listDrag(w.id)}
              onMove={(d) => moveList(w.id, d)}
              onOpen={onOpen}
            />
          ))}
        </Box>
      ) : null}
      <FormControlLabel control={<Switch checked={showArchived} onChange={(e) => void loadArchived(e.target.checked)} />} label="Show deleted watchlists" />
      {showArchived ? (
        <Card variant="outlined">
          {archived?.length ? (
            archived.map((w) => (
              <Stack key={w.id} direction="row" spacing={1} sx={{ alignItems: "center", px: 2, py: 1, "& + &": { borderTop: 1, borderColor: "divider" } }}>
                <Typography sx={{ flex: 1, minWidth: 0 }} noWrap>
                  {w.name}
                  <Typography component="span" variant="caption" sx={{ color: "text.secondary", ml: 1 }}>
                    {w.items.length} pairs · deleted {fmtWhen(w.archived_at ?? undefined) ?? ""}
                  </Typography>
                </Typography>
                <ActionButton
                  compact
                  disabled={lists.length >= maxLists}
                  title={lists.length >= maxLists ? `At most ${String(maxLists)} lists: archive one first` : undefined}
                  onClick={() => void run(() => api.archiveWatchlist(w.id, true), `${w.name} restored.`).then(() => loadArchived(true))}
                >
                  Restore
                </ActionButton>
              </Stack>
            ))
          ) : (
            <Typography variant="body2" sx={{ color: "text.secondary", p: 2 }}>
              {archived ? "No deleted watchlists." : "Loading…"}
            </Typography>
          )}
        </Card>
      ) : null}

      {lists.length ? (
        <>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ alignItems: { sm: "center" }, pt: 1 }}>
            <Typography variant="h2" component="h2" sx={{ flex: 1 }}>
              Setup quality
            </Typography>
            <ToggleButtonGroup
              exclusive
              size="small"
              value={scoreList?.id ?? null}
              onChange={(_e, v: number | null) => {
                if (v === null) return;
                setScoreId(v);
                setScored(null);
              }}
              aria-label="List to score"
              sx={{ flexWrap: "wrap" }}
            >
              {lists.map((w) => (
                <ToggleButton key={w.id} value={w.id}>
                  {w.name}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>
          </Stack>
          <KpiStrip
            tiles={[
              { label: "Scored", value: scored ? String(rows.length) : notScored, note: scored ? `On ${scored.timeframe}` : `${String(scoreList?.items.length ?? 0)} pairs in ${scoreList?.name ?? "the list"}` },
              { label: "Actionable", value: scored ? String(scored.actionable_count) : notScored, note: "Trade allowed, quality 55 or more" },
              {
                label: "Top pick",
                value: top ? top.symbol : notScored,
                note: top ? (
                  <>
                    Quality {top.quality ?? <Na />} · {top.bias ?? <Na />}
                  </>
                ) : (
                  "Highest quality"
                ),
              },
              { label: "Timeframe", value: scored?.timeframe ?? timeframe, note: "From the top bar" },
            ]}
          />
          <Card>{table}</Card>
        </>
      ) : null}
    </Stack>
  );
}
