import Badge from "@mui/material/Badge";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Drawer from "@mui/material/Drawer";
import IconButton from "@mui/material/IconButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TableSortLabel from "@mui/material/TableSortLabel";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import Check from "@mui/icons-material/Check";
import Close from "@mui/icons-material/Close";
import DragIndicator from "@mui/icons-material/DragIndicator";
import MoreVert from "@mui/icons-material/MoreVert";
import UnfoldLess from "@mui/icons-material/UnfoldLess";
import UnfoldMore from "@mui/icons-material/UnfoldMore";
import ViewSidebarOutlined from "@mui/icons-material/ViewSidebarOutlined";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type DragEvent,
  type KeyboardEvent,
  type PointerEvent,
  type ReactNode,
} from "react";
import { api, type WatchlistItem, type WatchlistList, type WatchlistQuote, type WatchlistsResponse, type WatchPeriod } from "../api";
import { fmtFixed, fmtPx } from "../lib/format";
import { oneOf, usePref } from "../lib/storage";
import { Segmented } from "./ArenaCharts";
import { useFeedback } from "./feedback";
import { Na, Num, monoSx, sortRows, useSort, type Sort } from "./ui";

/** Watchlists (WL-149): up to 4 stored lists of 40 pairs. Since WL-152 the open ones show in a panel docked on the right. */

const QUOTE_MS = 15_000;

type Ctx = {
  data: WatchlistsResponse | null;
  error: string | null;
  reload: () => Promise<void>;
  /** Run a change, then show the list as the server returns it; a failure is a toast and a reload. */
  run: (fn: () => Promise<unknown>, done?: string) => Promise<boolean>;
  /** Show a new order at once, then store it. */
  orderLists: (ids: number[]) => void;
  orderItems: (listId: number, ids: number[]) => void;
  /** The panel shows only the list names (kept per browser). */
  folded: boolean;
  setFolded: (f: boolean) => void;
  /** WL-152: the right panel is open, and the period its single change column shows (both per browser). */
  panelOpen: boolean;
  setPanelOpen: (open: boolean) => void;
  period: WatchPeriod;
  setPeriod: (p: WatchPeriod) => void;
};

const WatchCtx = createContext<Ctx | null>(null);

/** The rows in the order of `ids`; a row the order does not name is dropped until the reload. */
function inOrder<T extends { id: number }>(rows: T[], ids: number[]): T[] {
  const byId = new Map(rows.map((r) => [r.id, r]));
  return ids.map((id) => byId.get(id)).filter((r): r is T => !!r);
}

export function useWatchlists(): Ctx {
  const ctx = useContext(WatchCtx);
  if (!ctx) throw new Error("useWatchlists needs a WatchlistsProvider");
  return ctx;
}

export function WatchlistsProvider({ children }: Readonly<{ children: ReactNode }>) {
  const { toast } = useFeedback();
  const [data, setData] = useState<WatchlistsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [folded, setFolded] = usePref("cca_watch_strip_folded", false);
  const [panelOpen, setPanelOpen] = usePref("cca_watch_panel_open", true);
  const [period, setPeriod] = usePref<WatchPeriod>("cca_watch_period", "24h", oneOf("15m", "4h", "24h", "1d", "1w", "1M"));

  const reload = useCallback(async () => {
    try {
      setData(await api.watchlists());
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    reload().catch(() => undefined);
  }, [reload]);

  const run = useCallback(
    async (fn: () => Promise<unknown>, done?: string) => {
      try {
        await fn();
        if (done) toast(done);
        await reload();
        return true;
      } catch (err) {
        toast(`Not saved: ${(err as Error).message}`);
        await reload();
        return false;
      }
    },
    [toast, reload],
  );

  const orderLists = useCallback(
    (ids: number[]) => {
      setData((d) => (d ? { ...d, watchlists: inOrder(d.watchlists, ids) } : d));
      void run(() => api.orderWatchlists(ids));
    },
    [run],
  );

  const orderItems = useCallback(
    (listId: number, ids: number[]) => {
      setData((d) => (d ? { ...d, watchlists: d.watchlists.map((w) => (w.id === listId ? { ...w, items: inOrder(w.items, ids) } : w)) } : d));
      void run(() => api.orderWatchItems(listId, ids));
    },
    [run],
  );

  const value = useMemo(
    () => ({ data, error, reload, run, orderLists, orderItems, folded, setFolded, panelOpen, setPanelOpen, period, setPeriod }),
    [data, error, reload, run, orderLists, orderItems, folded, setFolded, panelOpen, setPanelOpen, period, setPeriod],
  );
  return <WatchCtx.Provider value={value}>{children}</WatchCtx.Provider>;
}

// --- sorting by drag or keyboard ------------------------------------------------------------

function moved(ids: number[], id: number, to: number): number[] {
  const out = ids.filter((x) => x !== id);
  out.splice(Math.max(0, Math.min(out.length, to)), 0, id);
  return out;
}

/** Drag to sort, or Alt plus an arrow key on the focused entry. Each use keeps its own drag, so a pair dragged
 * inside a list never moves the list around it. */
export function useDragSort(ids: number[], onOrder: (ids: number[]) => void, vertical = true) {
  const [dragId, setDragId] = useState<number | null>(null);
  const [overId, setOverId] = useState<number | null>(null);
  const back = vertical ? "ArrowUp" : "ArrowLeft";
  const forward = vertical ? "ArrowDown" : "ArrowRight";

  return (id: number) => ({
    draggable: true,
    "data-over": overId === id && dragId !== null && dragId !== id ? "1" : undefined,
    onDragStart: (e: DragEvent) => {
      e.stopPropagation();
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", String(id));
      setDragId(id);
    },
    onDragOver: (e: DragEvent) => {
      if (dragId === null) return;
      e.preventDefault();
      e.stopPropagation();
      if (overId !== id) setOverId(id);
    },
    onDrop: (e: DragEvent) => {
      if (dragId === null) return;
      e.preventDefault();
      e.stopPropagation();
      if (dragId !== id) onOrder(moved(ids, dragId, ids.indexOf(id)));
      setDragId(null);
      setOverId(null);
    },
    onDragEnd: () => {
      setDragId(null);
      setOverId(null);
    },
    onKeyDown: (e: KeyboardEvent) => {
      if (!e.altKey || (e.key !== back && e.key !== forward)) return;
      e.preventDefault();
      e.stopPropagation();
      const i = ids.indexOf(id);
      const to = e.key === back ? i - 1 : i + 1;
      if (to >= 0 && to < ids.length) onOrder(moved(ids, id, to));
    },
  });
}

/** The drop target shows a line where the dragged entry lands. */
export const DROP_SX = { '&[data-over="1"]': { outline: 2, outlineOffset: -2, outlineColor: "primary.main" } } as const;



// --- live quotes ------------------------------------------------------------------------------

export function useQuotes(symbols: string[], active: boolean) {
  const [quotes, setQuotes] = useState<Record<string, WatchlistQuote>>({});
  const [error, setError] = useState<string | null>(null);
  const [visible, setVisible] = useState(() => document.visibilityState === "visible");
  const key = [...new Set(symbols)].sort((a, b) => a.localeCompare(b)).join(",");

  useEffect(() => {
    const onVis = () => setVisible(document.visibilityState === "visible");
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  useEffect(() => {
    if (!active || !visible || !key) return;
    let cancelled = false;
    const load = () =>
      api
        .watchQuotes(key.split(","))
        .then((r) => {
          if (cancelled) return;
          setQuotes(r.quotes);
          setError(r.error ?? null);
        })
        .catch((err: unknown) => !cancelled && setError((err as Error).message));
    void load();
    const timer = setInterval(() => void load(), QUOTE_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [key, active, visible]);

  return { quotes, error };
}

/** WL-152: 24h is the rolling ticker; the others count from the open of the current candle (UTC), like TradingView. */
export const PERIODS: [WatchPeriod, string][] = [
  ["15m", "15m"],
  ["4h", "4h"],
  ["24h", "24h"],
  ["1d", "1D"],
  ["1w", "1W"],
  ["1M", "1M"],
];
const PERIOD_TITLE: Record<WatchPeriod, string> = {
  "15m": "Change since this 15m candle opened",
  "4h": "Change since this 4h candle opened",
  "24h": "Change over the last 24 hours",
  "1d": "Change since today's open (UTC)",
  "1w": "Change since this week's open (Monday, UTC)",
  "1M": "Change since this month's open (UTC)",
};

export function changeOf(q: WatchlistQuote | undefined, p: WatchPeriod): number | null | undefined {
  if (!q) return undefined;
  return q.changes?.[p] ?? (p === "24h" ? q.change_pct : null);
}

/** WL-152: up green with ▲, down red with ▼ (Sheryar asked for it; ruleset 9.3). */
export function Change({ q, period = "24h" }: Readonly<{ q: WatchlistQuote | undefined; period?: WatchPeriod }>) {
  const v = changeOf(q, period);
  if (v === undefined) return <Na reason="No Binance ticker for this pair" />;
  if (v === null) return <Na reason={`No ${period} candle yet for this pair`} />;
  const glyph = v > 0 ? "▲ " : v < 0 ? "▼ " : "";
  return (
    <Box
      component="span"
      sx={[monoSx, { color: v > 0 ? "success.main" : v < 0 ? "error.main" : "text.secondary", whiteSpace: "nowrap", textAlign: "right" }]}
      title={PERIOD_TITLE[period]}
    >
      {glyph}
      {fmtFixed(Math.abs(v), 2)}%
    </Box>
  );
}

/** The six periods side by side, with a header row from `ChangeHeads`. */
export function Changes({ q }: Readonly<{ q: WatchlistQuote | undefined }>) {
  return (
    <>
      {PERIODS.map(([p]) => (
        <Change key={p} q={q} period={p} />
      ))}
    </>
  );
}

type SortProps = Readonly<{ sort: Sort; onSort: (key: string, first?: "asc" | "desc") => void }>;

/** WL-153: a grid header that sorts its list on click, like `SortCell` in a table: high first, then low, then your order. */
export function SortHead({ id, label, sort, onSort, right = false, first = "desc", title }: SortProps & Readonly<{ id: string; label: string; right?: boolean; first?: "asc" | "desc"; title?: string }>) {
  const on = sort?.key === id;
  return (
    <Box component="span" title={title} sx={{ typography: "caption", color: "text.secondary", textAlign: right ? "right" : "left", minWidth: 0 }}>
      <TableSortLabel
        active={on}
        direction={on ? sort.dir : first}
        onClick={(e) => {
          e.stopPropagation();
          onSort(id, first);
        }}
        sx={right ? { flexDirection: "row-reverse" } : undefined}
      >
        {label}
      </TableSortLabel>
    </Box>
  );
}

export function ChangeHeads({ sort, onSort }: SortProps) {
  return (
    <>
      {PERIODS.map(([p, label]) => (
        <SortHead key={p} id={p} label={label} title={PERIOD_TITLE[p]} right sort={sort} onSort={onSort} />
      ))}
    </>
  );
}

/** WL-153: Pair sorts A to Z first, Last and the periods high first; a pair without a quote goes last. */
export function sortedItems(items: WatchlistItem[], sort: Sort, quotes: Record<string, WatchlistQuote>): WatchlistItem[] {
  return sortRows(items, sort, (it, k) => (k === "pair" ? short(it.symbol) : k === "last" ? quotes[it.symbol]?.price : changeOf(quotes[it.symbol], k as WatchPeriod)));
}

/** "Sorted by 1W, high first" for the header of a sorted list. */
export function sortLabel(sort: Sort): string {
  if (!sort) return "Your order";
  const name = sort.key === "pair" ? "Pair" : sort.key === "last" ? "Price" : (PERIODS.find(([p]) => p === sort.key)?.[1] ?? sort.key);
  const way = sort.key === "pair" ? (sort.dir === "asc" ? "A to Z" : "Z to A") : sort.dir === "desc" ? "high first" : "low first";
  return `${name}, ${way}`;
}

export function short(symbol: string): string {
  return symbol.replace(/USDT(\.P)?$/, (_m, p: string | undefined) => (p ? ".P" : ""));
}

/** WL-152: the ticker in bold with the instrument's name next to it, cut with an ellipsis when narrow. */
export function PairName({ item }: Readonly<{ item: WatchlistItem }>) {
  return (
    <Box sx={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={item.name ? `${item.symbol}: ${item.name}` : item.symbol}>
      <Num sx={{ fontWeight: 700 }}>{short(item.symbol)}</Num>
      {item.name ? (
        <Box component="span" sx={{ color: "text.secondary", ml: 0.75, fontSize: "0.75rem" }}>
          {item.name}
        </Box>
      ) : null}
    </Box>
  );
}

/** WL-152: rename, hide or delete a list from its header. Delete archives it (decision 0010): restore it on the Watchlists page. */
export function useListActions(list: WatchlistList) {
  const { run } = useWatchlists();
  const { ask } = useFeedback();
  return {
    rename: async () => {
      const name = await ask({ title: "Rename watchlist", label: "Name", input: true, okLabel: "Rename" });
      if (typeof name === "string" && name.trim()) await run(() => api.updateWatchlist(list.id, { name: name.trim() }), `Renamed to ${name.trim()}.`);
    },
    remove: async () => {
      const ok = await ask({
        title: `Delete ${list.name}?`,
        text: "It leaves the panel and the Watchlists page. Nothing is erased: it stays in the archive, and Show deleted watchlists brings it back.",
        okLabel: "Delete",
        danger: true,
      });
      if (ok) await run(() => api.archiveWatchlist(list.id), `${list.name} deleted.`);
    },
    hide: () => run(() => api.updateWatchlist(list.id, { is_open: false })),
  };
}

function ListMenu({ list }: Readonly<{ list: WatchlistList }>) {
  const { rename, remove, hide } = useListActions(list);
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const pick = (fn: () => unknown) => () => {
    setAnchor(null);
    void fn();
  };
  return (
    <>
      <IconButton size="small" aria-label={`${list.name}: rename, hide or delete`} aria-haspopup="menu" onClick={(e) => setAnchor(e.currentTarget)}>
        <MoreVert fontSize="small" />
      </IconButton>
      <Menu anchorEl={anchor} open={!!anchor} onClose={() => setAnchor(null)} anchorOrigin={{ vertical: "bottom", horizontal: "right" }} transformOrigin={{ vertical: "top", horizontal: "right" }}>
        <MenuItem onClick={pick(rename)}>Rename</MenuItem>
        <MenuItem onClick={pick(hide)}>Hide in the panel</MenuItem>
        <MenuItem onClick={pick(remove)} sx={{ color: "error.main" }}>
          Delete
        </MenuItem>
      </Menu>
    </>
  );
}

// --- the right panel --------------------------------------------------------------------------

const PANEL_MIN = 280;
const PANEL_MAX = 800;
/** From this width the panel shows all six periods instead of the chosen one (WL-153: 720, so the 76px columns fit). */
const PANEL_ALL = 720;

function PanelList({
  list,
  quotes,
  wide,
  onOpenPair,
  dragProps,
}: Readonly<{
  list: WatchlistList;
  quotes: Record<string, WatchlistQuote>;
  wide: boolean;
  onOpenPair: (symbol: string, exchange?: string) => void;
  dragProps: ReturnType<ReturnType<typeof useDragSort>>;
}>) {
  const { orderItems, folded, period } = useWatchlists();
  const [sort, onSort, unsort] = useSort(`cca_watch_panel_sort_${String(list.id)}`);
  const items = sortedItems(list.items, sort, quotes);
  const itemDrag = useDragSort(
    list.items.map((i) => i.id),
    (ids) => orderItems(list.id, ids),
  );
  const periodLabel = PERIODS.find(([p]) => p === period)?.[1] ?? period;
  const cols = wide ? "minmax(96px, 1fr) 96px repeat(6, 76px)" : "minmax(0, 1fr) auto 84px";

  return (
    <Box sx={{ ...DROP_SX, "& + &": { borderTop: 1, borderColor: "divider" } }} {...dragProps}>
      <Stack direction="row" spacing={0.5} sx={{ alignItems: "center", px: 1, py: 0.25, bgcolor: "action.hover", cursor: "grab" }}>
        <DragIndicator fontSize="small" sx={{ color: "text.disabled" }} aria-hidden />
        <Typography variant="subtitle2" noWrap sx={{ flex: 1, minWidth: 0 }} title="Drag to move the list; Alt plus Up or Down moves it too">
          {list.name}
        </Typography>
        {sort ? (
          <Tooltip title={`Sorted by ${sortLabel(sort)}; click for your own order`}>
            <Box
              component="button"
              type="button"
              onClick={unsort}
              sx={{ all: "unset", cursor: "pointer", typography: "caption", color: "text.secondary", px: 0.5, borderRadius: 0.5, "&:hover": { bgcolor: "action.selected" }, "&:focus-visible": { outline: 2, outlineColor: "primary.main" } }}
            >
              {sortLabel(sort)} ✕
            </Box>
          </Tooltip>
        ) : null}
        <ListMenu list={list} />
      </Stack>
      {folded ? null : items.length ? (
        <>
          <Box sx={{ display: "grid", gridTemplateColumns: cols, gap: 1, px: 1, py: 0.25, borderBottom: 1, borderColor: "divider" }}>
            <SortHead id="pair" label="Pair" first="asc" sort={sort} onSort={onSort} />
            <SortHead id="last" label="Price" title="Last traded price" right sort={sort} onSort={onSort} />
            {wide ? <ChangeHeads sort={sort} onSort={onSort} /> : <SortHead id={period} label={periodLabel} title={PERIOD_TITLE[period]} right sort={sort} onSort={onSort} />}
          </Box>
          {items.map((it) => {
            const q = quotes[it.symbol];
            const drag = sort ? null : itemDrag(it.id);
            const open = () => onOpenPair(it.symbol, it.exchange);
            return (
              <Box
                key={it.id}
                role="button"
                tabIndex={0}
                {...drag}
                onClick={open}
                onKeyDown={(e: KeyboardEvent) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    open();
                  } else drag?.onKeyDown(e);
                }}
                title={`${it.symbol}: open on the desk${sort ? "" : "; drag or Alt plus Up or Down to move"}`}
                sx={[
                  DROP_SX,
                  {
                    cursor: "pointer",
                    display: "grid",
                    gridTemplateColumns: cols,
                    gap: 1,
                    alignItems: "center",
                    px: 1,
                    minHeight: { xs: 48, md: 30 },
                    fontSize: "0.8125rem",
                    "&:hover": { bgcolor: "action.hover" },
                    "&:focus-visible": { outline: 2, outlineOffset: -2, outlineColor: "primary.main" },
                  },
                ]}
              >
                <PairName item={it} />
                <Num sx={{ textAlign: "right" }}>{q ? fmtPx(q.price) : <Na reason="No Binance ticker for this pair" />}</Num>
                {wide ? <Changes q={q} /> : <Change q={q} period={period} />}
              </Box>
            );
          })}
        </>
      ) : (
        <Typography variant="caption" component="div" sx={{ color: "text.secondary", p: 1 }}>
          No pairs yet. Add them on the Watchlists page.
        </Typography>
      )}
    </Box>
  );
}

/** The panel's menu: which lists show, fold to the names, manage. */
function PanelMenu({ onManage }: Readonly<{ onManage: () => void }>) {
  const { data, run, folded, setFolded } = useWatchlists();
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const lists = data?.watchlists ?? [];
  const openCount = lists.filter((w) => w.is_open).length;
  return (
    <>
      <Tooltip title="Choose the lists">
        <IconButton size="small" aria-label="Choose the lists" aria-haspopup="menu" aria-expanded={anchor ? "true" : undefined} onClick={(e) => setAnchor(e.currentTarget)}>
          <MoreVert fontSize="small" />
        </IconButton>
      </Tooltip>
      <Menu anchorEl={anchor} open={!!anchor} onClose={() => setAnchor(null)} anchorOrigin={{ vertical: "bottom", horizontal: "right" }} transformOrigin={{ vertical: "top", horizontal: "right" }}>
        {lists.length ? (
          lists.map((w) => (
            <MenuItem key={w.id} onClick={() => void run(() => api.updateWatchlist(w.id, { is_open: !w.is_open }))} aria-checked={w.is_open} role="menuitemcheckbox">
              <ListItemIcon>{w.is_open ? <Check fontSize="small" /> : null}</ListItemIcon>
              <ListItemText primary={w.name} secondary={`${String(w.items.length)} of ${String(data?.max_items ?? 40)} pairs`} />
            </MenuItem>
          ))
        ) : (
          <MenuItem disabled>
            <ListItemText primary="No watchlists yet" />
          </MenuItem>
        )}
        <Divider />
        <MenuItem disabled={!openCount} onClick={() => setFolded(!folded)}>
          <ListItemIcon>{folded ? <UnfoldMore fontSize="small" /> : <UnfoldLess fontSize="small" />}</ListItemIcon>
          <ListItemText primary={folded ? "Unfold the lists" : "Fold the lists to their names"} />
        </MenuItem>
        <MenuItem
          onClick={() => {
            setAnchor(null);
            onManage();
          }}
        >
          <ListItemIcon />
          <ListItemText primary="Manage watchlists" />
        </MenuItem>
      </Menu>
    </>
  );
}

function PanelBody({ width, onOpenPair, onManage, onClose }: Readonly<{ width: number; onOpenPair: (symbol: string, exchange?: string) => void; onManage: () => void; onClose: () => void }>) {
  const { data, error: listError, orderLists, period, setPeriod } = useWatchlists();
  const shown = (data?.watchlists ?? []).filter((w) => w.is_open);
  const { quotes, error } = useQuotes(
    shown.flatMap((w) => w.items.map((i) => i.symbol)),
    shown.length > 0,
  );
  const listDrag = useDragSort(
    shown.map((w) => w.id),
    (ids) => {
      const all = (data?.watchlists ?? []).map((w) => w.id);
      // The hidden lists keep their place after the shown ones moved.
      orderLists([...ids, ...all.filter((id) => !ids.includes(id))]);
    },
  );
  const wide = width >= PANEL_ALL;
  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      <Stack direction="row" spacing={0.5} sx={{ alignItems: "center", px: 1.5, py: 1, borderBottom: 1, borderColor: "divider" }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, flex: 1 }}>
          Watchlists
        </Typography>
        <PanelMenu onManage={onManage} />
        <Tooltip title="Close the panel">
          <IconButton size="small" aria-label="Close the watchlist panel" onClick={onClose}>
            <Close fontSize="small" />
          </IconButton>
        </Tooltip>
      </Stack>
      {wide ? null : (
        <Box sx={{ px: 1.5, py: 1, borderBottom: 1, borderColor: "divider", overflowX: "auto" }}>
          <Segmented value={period} options={PERIODS} onChange={setPeriod} label="Change over" />
        </Box>
      )}
      {error || listError ? (
        <Typography variant="caption" component="div" sx={{ color: "text.secondary", px: 1.5, py: 0.5 }}>
          {listError ? `Watchlists unavailable: ${listError}` : `Live prices unavailable: ${error ?? ""}`}
        </Typography>
      ) : null}
      <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        {shown.length ? (
          shown.map((w) => <PanelList key={w.id} list={w} quotes={quotes} wide={wide} onOpenPair={onOpenPair} dragProps={listDrag(w.id)} />)
        ) : (
          <Typography variant="body2" sx={{ color: "text.secondary", p: 1.5 }}>
            No list shown. Pick one with the ⋮ menu above.
          </Typography>
        )}
      </Box>
    </Box>
  );
}

/**
 * WL-152: the watchlists docked on the right like TradingView. On a desktop it takes its own column, so the
 * page moves over instead of being covered; drag its left edge to resize. On a phone it slides over the page.
 */
export function WatchPanel({ desktop, onOpenPair, onManage }: Readonly<{ desktop: boolean; onOpenPair: (symbol: string, exchange?: string) => void; onManage: () => void }>) {
  const { panelOpen, setPanelOpen } = useWatchlists();
  const [width, setWidth] = usePref("cca_watch_panel_w", 360, (v) => typeof v === "number" && v >= PANEL_MIN && v <= PANEL_MAX);
  const close = () => setPanelOpen(false);
  const openPair = (s: string, ex?: string) => {
    onOpenPair(s, ex);
    if (!desktop) close();
  };

  if (!desktop) {
    return (
      <Drawer anchor="right" open={panelOpen} onClose={close} slotProps={{ paper: { sx: { width: "min(100vw, 400px)" } } }}>
        <PanelBody width={PANEL_MIN} onOpenPair={openPair} onManage={onManage} onClose={close} />
      </Drawer>
    );
  }
  if (!panelOpen) return null;

  const startResize = (e: PointerEvent<HTMLElement>) => {
    e.preventDefault();
    const x0 = e.clientX;
    const w0 = width;
    const move = (ev: globalThis.PointerEvent) => setWidth(Math.round(Math.max(PANEL_MIN, Math.min(PANEL_MAX, w0 + x0 - ev.clientX))));
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  };
  const keyResize = (e: KeyboardEvent) => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    setWidth((w) => Math.max(PANEL_MIN, Math.min(PANEL_MAX, w + (e.key === "ArrowLeft" ? 20 : -20))));
  };

  return (
    <Box
      component="aside"
      aria-label="Watchlists"
      sx={{ position: "sticky", top: 0, height: "100vh", width, flexShrink: 0, borderLeft: 1, borderColor: "divider", bgcolor: "background.paper", display: "flex" }}
    >
      <Box
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize the watchlist panel"
        aria-valuenow={width}
        aria-valuemin={PANEL_MIN}
        aria-valuemax={PANEL_MAX}
        tabIndex={0}
        onPointerDown={startResize}
        onKeyDown={keyResize}
        title="Drag to resize (or Left and Right arrow keys)"
        sx={{ width: 6, ml: "-3px", cursor: "col-resize", flexShrink: 0, "&:hover, &:focus-visible": { bgcolor: "primary.main", outline: "none" } }}
      />
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <PanelBody width={width} onOpenPair={openPair} onManage={onManage} onClose={close} />
      </Box>
    </Box>
  );
}

/** Top right: opens and closes the watchlist panel. */
export function WatchPanelButton() {
  const { data, panelOpen, setPanelOpen } = useWatchlists();
  const shown = (data?.watchlists ?? []).filter((w) => w.is_open).length;
  return (
    <Tooltip title={panelOpen ? "Close the watchlist panel" : "Open the watchlist panel"}>
      <IconButton aria-label="Watchlist panel" aria-pressed={panelOpen} onClick={() => setPanelOpen(!panelOpen)} color={panelOpen ? "primary" : "default"}>
        <Badge badgeContent={shown} color="primary" invisible={!shown || panelOpen}>
          <ViewSidebarOutlined />
        </Badge>
      </IconButton>
    </Tooltip>
  );
}
