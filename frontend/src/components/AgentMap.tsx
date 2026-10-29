import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import Add from "@mui/icons-material/Add";
import AutoGraphOutlined from "@mui/icons-material/AutoGraphOutlined";
import CandlestickChartOutlined from "@mui/icons-material/CandlestickChartOutlined";
import CenterFocusStrongOutlined from "@mui/icons-material/CenterFocusStrongOutlined";
import SmartToyOutlined from "@mui/icons-material/SmartToyOutlined";
import Remove from "@mui/icons-material/Remove";
import VisibilityOutlined from "@mui/icons-material/VisibilityOutlined";
import { useEffect, useMemo, useRef, type ReactElement } from "react";
import type { ArenaAgent, ArenaCharts, ArenaFigureSet, ArenaStanding } from "../api";
import { fmtR, fmtRate } from "../lib/format";
import { usePalette } from "./ArenaCharts";
import { ActionButton } from "./ui";
import { usePref, oneOf } from "../lib/storage";

/** The agent map (WL-095), like the Unefy Network page: candles feed the agents, agents fold open to the
 * strategies they traded, and G.O.A.T. links to the agents it copied. Follows the Arena filters. */

type Stance = "all" | "bull" | "bear" | "both";
const ROW = 64;
const NODE_W = 230;
const COL = [24, 400, 740];
const LABEL_END = 210; // edges leave a node after its label
const MAX_STRATS = 6;
const PAD = 24;

type Fig = Pick<ArenaFigureSet, "trades" | "total_r" | "win_rate"> | null;

function ring(f: Fig): { color: string; dashed: boolean; label: string } {
  if (!f || !f.trades) return { color: "text.disabled", dashed: true, label: "No trades for these filters" };
  if (f.total_r > 0) return { color: "success.main", dashed: false, label: `Made money: ${fmtR(f.total_r, 1) ?? ""}` };
  return { color: "error.main", dashed: false, label: `Lost: ${fmtR(f.total_r, 1) ?? ""}` };
}

function standingFig(r: ArenaStanding): Fig {
  return r.trades ? { trades: r.trades, total_r: r.total_r ?? 0, win_rate: r.win_rate } : null;
}

function caption(f: Fig): string {
  if (!f || !f.trades) return "no trades";
  const r = f.total_r;
  return `${r > 0 ? "▲" : r < 0 ? "▼" : ""} ${fmtR(r, 1) ?? ""} · ${f.trades.toLocaleString()} tr · ${fmtRate(f.win_rate) ?? ""} won`;
}

function Node({
  x,
  y,
  icon,
  name,
  note,
  fig,
  small = false,
  selected = false,
  onClick,
}: Readonly<{ x: number; y: number; icon: ReactElement; name: string; note: string; fig?: Fig; small?: boolean; selected?: boolean; onClick?: () => void }>) {
  const size = small ? 30 : 38;
  const st = fig === undefined ? null : ring(fig);
  return (
    <Stack
      direction="row"
      spacing={1}
      onClick={onClick}
      onKeyDown={(e) => e.key === "Enter" && onClick?.()}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      aria-pressed={onClick ? selected : undefined}
      sx={{
        position: "absolute",
        left: x,
        top: y - size / 2,
        width: NODE_W,
        alignItems: "center",
        cursor: onClick ? "pointer" : "default",
        borderRadius: 1,
        "&:focus-visible": { outline: 2, outlineColor: "primary.main" },
      }}
    >
      <Box
        sx={{
          position: "relative",
          width: size,
          height: size,
          flexShrink: 0,
          display: "grid",
          placeItems: "center",
          borderRadius: 1.5,
          border: selected ? 2 : 1,
          borderColor: selected ? "primary.main" : "divider",
          bgcolor: "background.paper",
          color: "text.secondary",
          boxShadow: 1,
          "& svg": { fontSize: small ? 16 : 20 },
        }}
      >
        {icon}
        {st ? (
          <Tooltip title={st.label}>
            <Box
              aria-label={st.label}
              sx={{ position: "absolute", top: -5, right: -5, width: 12, height: 12, borderRadius: "50%", border: 2, borderStyle: st.dashed ? "dashed" : "solid", borderColor: st.color, bgcolor: "background.paper" }}
            />
          </Tooltip>
        ) : null}
      </Box>
      <Box sx={{ minWidth: 0 }}>
        <Typography variant={small ? "caption" : "body2"} component="div" noWrap sx={{ fontWeight: 700, color: onClick ? "primary.main" : "text.primary", lineHeight: 1.25 }}>
          {name}
        </Typography>
        <Typography variant="caption" component="div" noWrap sx={{ color: "text.secondary", lineHeight: 1.25, fontSize: "0.6875rem" }}>
          {note}
        </Typography>
      </Box>
    </Stack>
  );
}

export default function AgentMap({
  charts,
  board,
  agents,
  selected,
  onPick,
}: Readonly<{ charts: ArenaCharts; board: ArenaStanding[]; agents: ArenaAgent[]; selected: string | null; onPick: (id: string) => void }>) {
  const pal = usePalette();
  const [stance, setStance] = usePref<Stance>("cca_map_stance", "all", oneOf("all", "bull", "bear", "both"));
  const [openList, setOpenList] = usePref<string[]>("cca_map_open", []);
  const open = useMemo(() => new Set(openList), [openList]);
  const setOpen = (next: Set<string> | ((s: Set<string>) => Set<string>)) =>
    setOpenList((l) => [...(typeof next === "function" ? next(new Set(l)) : next)]);
  const [zoom, setZoom] = usePref("cca_map_zoom", 1);
  const [copies, setCopies] = usePref("cca_map_copies", false);
  const boxRef = useRef<HTMLDivElement>(null);
  const names = Object.fromEntries(agents.map((a) => [a.id, a.name]));
  const goat = board.find((r) => r.stance === "meta");
  const rows = board.filter((r) => r.stance !== "meta" && (stance === "all" || r.stance === stance));

  // Lay the agents out top to bottom; an open agent takes one row per strategy.
  let cursor = 0;
  const placed = rows.map((r) => {
    const strats = charts.strategies[r.id] ?? [];
    const shown = strats.slice(0, MAX_STRATS);
    const rest = strats.slice(MAX_STRATS);
    const more = rest.length ? { key: `${String(rest.length)} more`, trades: rest.reduce((s, x) => s + x.trades, 0), wins: rest.reduce((s, x) => s + x.wins, 0), total_r: rest.reduce((s, x) => s + x.total_r, 0) } : null;
    const leaves = open.has(r.id) ? [...shown.map((s) => ({ ...s, more: false })), ...(more ? [{ ...more, win_rate: (100 * more.wins) / Math.max(1, more.trades), more: true }] : [])] : [];
    const span = Math.max(1, leaves.length);
    const top = cursor;
    cursor += span;
    return { r, strats, leaves, y: PAD + (top + span / 2) * ROW, leafY: (i: number) => PAD + (top + i + 0.5) * ROW };
  });
  const showGoat = Boolean(goat) && stance === "all";
  const height = PAD * 2 + Math.max(cursor, 1) * ROW + (showGoat ? ROW : 0);
  const anyOpen = placed.some((p) => p.leaves.length);
  const width = (anyOpen ? COL[2] : COL[1]) + NODE_W + 40;
  const srcY = placed.length ? (placed[0].y + placed[placed.length - 1].y) / 2 : PAD + ROW / 2;
  const goatY = height - PAD - ROW / 2;
  const at = Object.fromEntries(placed.map((p) => [p.r.id, p.y]));
  const followed = (goat && charts.strategies[goat.id]) || [];

  const fit = () => {
    const w = boxRef.current?.clientWidth ?? width;
    setZoom(Math.max(0.5, Math.min(1.25, (w - 8) / width)));
  };
  useEffect(() => {
    fit();
    // Fit once per layout width; zoom buttons change it after that.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [width]);

  const curve = (x1: number, y1: number, x2: number, y2: number) => {
    const dx = Math.max(40, (x2 - x1) / 2);
    return `M${String(x1)},${String(y1)} C${String(x1 + dx)},${String(y1)} ${String(x2 - dx)},${String(y2)} ${String(x2)},${String(y2)}`;
  };
  const edge = { bull: pal.success.main, bear: pal.error.main, both: pal.primary.main, meta: pal.text.secondary } as const;
  const stanceText = { bull: "▲ long", bear: "▼ short", both: "◇ both", meta: "◆ meta" } as const;
  const toggle = (id: string) =>
    setOpen((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  const srcX = COL[0] + LABEL_END;
  const showCopies = showGoat && (copies || selected === goat?.id);

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap", rowGap: 1, mb: 1.5 }}>
        <ToggleButtonGroup exclusive size="small" value={stance} aria-label="Stance" onChange={(_e, v: Stance | null) => v && setStance(v)}>
          {(
            [
              ["all", "All agents"],
              ["bull", "Bulls"],
              ["bear", "Bears"],
              ["both", "Both sides"],
            ] as [Stance, string][]
          ).map(([k, t]) => (
            <ToggleButton key={k} value={k} sx={{ px: 1.25, py: 0.25, fontSize: "0.75rem" }}>
              {t}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
        <ActionButton compact onClick={() => setOpen(new Set(rows.filter((r) => charts.strategies[r.id]?.length).map((r) => r.id)))}>
          Unfold all
        </ActionButton>
        <ActionButton compact disabled={!open.size} onClick={() => setOpen(new Set())}>
          Fold all
        </ActionButton>
        <ToggleButton
          size="small"
          value="copies"
          selected={showCopies}
          disabled={!showGoat}
          onChange={() => setCopies(!copies)}
          sx={{ px: 1.25, py: 0.25, fontSize: "0.75rem" }}
        >
          G.O.A.T. copies
        </ToggleButton>
        <Box sx={{ flex: 1 }} />
        <Stack direction="row" spacing={1.5} sx={{ flexWrap: "wrap", rowGap: 0.5, typography: "caption", color: "text.secondary", alignItems: "center" }}>
          {(["bull", "bear", "both"] as const).map((k) => (
            <Stack key={k} direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
              <Box sx={{ width: 16, height: 2, bgcolor: edge[k] }} />
              <span>{stanceText[k]}</span>
            </Stack>
          ))}
          <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
            <Box sx={{ width: 16, borderTop: 2, borderStyle: "dashed", borderColor: "text.secondary" }} />
            <span>G.O.A.T. copies</span>
          </Stack>
          <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
            <Box sx={{ width: 10, height: 10, borderRadius: "50%", border: 2, borderColor: "success.main" }} />
            <span>▲ made money</span>
          </Stack>
          <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
            <Box sx={{ width: 10, height: 10, borderRadius: "50%", border: 2, borderColor: "error.main" }} />
            <span>▼ lost</span>
          </Stack>
          <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
            <Box sx={{ width: 10, height: 10, borderRadius: "50%", border: 2, borderStyle: "dashed", borderColor: "text.disabled" }} />
            <span>no trades</span>
          </Stack>
        </Stack>
      </Stack>
      <Box sx={{ position: "relative" }}>
      <Box ref={boxRef} sx={{ height: { xs: 520, md: 680 }, overflow: "auto", border: 1, borderColor: "divider", borderRadius: 1, bgcolor: "surface.paper2" }}>
        <Box sx={{ width: width * zoom, height: height * zoom }}>
          <Box sx={{ position: "relative", width, height, transform: `scale(${String(zoom)})`, transformOrigin: "0 0" }}>
            <svg width={width} height={height} style={{ position: "absolute", inset: 0 }} aria-hidden>
              {placed.map((p) => (
                <g key={p.r.id}>
                  <path d={curve(srcX, srcY, COL[1], p.y)} fill="none" stroke={edge[p.r.stance]} strokeWidth={1.75} opacity={p.r.trades ? 1 : 0.4} />
                  <text x={COL[1] - 10} y={p.y - 7} fontSize={10.5} fontWeight={600} textAnchor="end" fill={edge[p.r.stance]}>
                    {stanceText[p.r.stance]}
                  </text>
                  {p.leaves.map((l, i) => (
                    <path key={l.key} d={curve(COL[1] + NODE_W + 14, p.y, COL[2], p.leafY(i))} fill="none" stroke={pal.text.disabled} strokeWidth={1.25} />
                  ))}
                </g>
              ))}
              {showCopies
                ? followed
                    .filter((f) => at[f.key] !== undefined)
                    .map((f) => (
                      <g key={f.key}>
                        <path d={curve(COL[0] + LABEL_END, goatY, COL[1], at[f.key] + 10)} fill="none" stroke={pal.text.secondary} strokeWidth={1.25} strokeDasharray="5 4" />
                        <text x={COL[1] - 10} y={at[f.key] + 22} fontSize={10} textAnchor="end" fill={pal.text.secondary}>
                          copied {f.trades.toLocaleString()}
                        </text>
                      </g>
                    ))
                : null}
            </svg>
            <Node
              x={COL[0]}
              y={srcY}
              icon={<CandlestickChartOutlined />}
              name="Binance candles"
              note={`${String(rows.length)} agents · fees and slippage`}
            />
            {showGoat && goat ? (
              <Node
                x={COL[0]}
                y={goatY}
                icon={<VisibilityOutlined />}
                name={goat.name}
                note={caption(standingFig(goat))}
                fig={standingFig(goat)}
                selected={selected === goat.id}
                onClick={() => onPick(goat.id)}
              />
            ) : null}
            {placed.map((p) => (
              <Box key={p.r.id}>
                <Node
                  x={COL[1]}
                  y={p.y}
                  icon={<SmartToyOutlined />}
                  name={`${p.r.name}${charts.filters[p.r.id] ? ` · ${String(charts.filters[p.r.id])} ${charts.filters[p.r.id] === 1 ? "filter" : "filters"}` : ""}`}
                  note={caption(standingFig(p.r))}
                  fig={standingFig(p.r)}
                  selected={selected === p.r.id}
                  onClick={() => onPick(p.r.id)}
                />
                {p.strats.length ? (
                  <Tooltip title={p.leaves.length ? "Fold" : `Show ${String(p.strats.length)} ${p.strats.length === 1 ? "strategy" : "strategies"}`}>
                    <IconButton
                      size="small"
                      aria-label={`${p.leaves.length ? "Fold" : "Unfold"} ${p.r.name}`}
                      aria-expanded={Boolean(p.leaves.length)}
                      onClick={() => toggle(p.r.id)}
                      sx={{
                        position: "absolute",
                        left: COL[1] + NODE_W + 2,
                        top: p.y - 11,
                        width: 22,
                        height: 22,
                        minWidth: 22,
                        minHeight: 22,
                        p: 0,
                        bgcolor: "primary.main",
                        color: "primary.contrastText",
                        "&:hover": { bgcolor: "primary.dark" },
                        "& svg": { fontSize: 14 },
                      }}
                    >
                      {p.leaves.length ? <Remove /> : <Add />}
                    </IconButton>
                  </Tooltip>
                ) : null}
                {p.leaves.map((l, i) => (
                  <Node
                    key={l.key}
                    x={COL[2]}
                    y={p.leafY(i)}
                    small
                    icon={<AutoGraphOutlined />}
                    name={l.more ? l.key : (names[l.key] ?? l.key)}
                    note={caption(l)}
                    fig={l}
                  />
                ))}
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
        <Stack
          sx={{ position: "absolute", left: 12, bottom: 12, width: 36, border: 1, borderColor: "divider", borderRadius: 1, bgcolor: "background.paper", boxShadow: 1 }}
        >
          <IconButton size="small" aria-label="Zoom in" onClick={() => setZoom((z) => Math.min(1.5, z + 0.1))}>
            <Add fontSize="small" />
          </IconButton>
          <IconButton size="small" aria-label="Zoom out" onClick={() => setZoom((z) => Math.max(0.4, z - 0.1))}>
            <Remove fontSize="small" />
          </IconButton>
          <IconButton size="small" aria-label="Fit to width" onClick={fit}>
            <CenterFocusStrongOutlined fontSize="small" />
          </IconButton>
        </Stack>
      </Box>
      <Typography variant="caption" sx={{ color: "text.secondary", display: "block", mt: 1 }}>
        Rings: did the agent make money for these filters. Strategies are the rules that fired, most trades first; for G.O.A.T., the agents it copied.
      </Typography>
    </Box>
  );
}
