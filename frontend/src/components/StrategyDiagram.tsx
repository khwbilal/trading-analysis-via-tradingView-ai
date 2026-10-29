import Box from "@mui/material/Box";
import { useTheme } from "@mui/material/styles";
import type { DiagramMarker, StrategyDiagram as Diagram } from "../api";

/** Draws a strategy's diagram data (0..100 grid, y up is price up) as SVG with theme colours (WL-031). */

const W = 320;
const H = 180;
const PAD = 12;

const sx = (x: number) => PAD + (x / 100) * (W - 2 * PAD);
const sy = (y: number) => H - PAD - (y / 100) * (H - 2 * PAD);
const pts = (p: number[][]) => p.map(([x, y]) => `${sx(x).toFixed(1)},${sy(y).toFixed(1)}`).join(" ");

const MARKER_GLYPH: Record<DiagramMarker["kind"], string> = { entry: "●", stop: "✕", target: "◆", note: "○" };

export default function StrategyDiagram({ diagram, compact = false }: Readonly<{ diagram: Diagram; compact?: boolean }>) {
  const t = useTheme();
  const v = t.vars?.palette ?? t.palette;
  const color: Record<string, string> = {
    entry: v.levels.entry,
    stop: v.levels.stop,
    target: v.levels.target,
    note: v.text.secondary,
    fast: v.levels.ema20,
    slow: v.levels.ema50,
    level: v.text.disabled,
  };
  return (
    <Box
      component="figure"
      sx={{ m: 0, border: 1, borderColor: "divider", borderRadius: 1, bgcolor: "surface.paper2", overflow: "hidden" }}
    >
      <Box
        component="svg"
        viewBox={`0 0 ${String(W)} ${String(H)}`}
        role="img"
        aria-label={diagram.caption}
        sx={{ display: "block", width: "100%", height: "auto", fontFamily: t.typography.fontFamily }}
      >
        {diagram.zones.map((z) => (
          <g key={`z-${z.label}`}>
            <rect
              x={sx(z.x0)}
              y={sy(z.y1)}
              width={sx(z.x1) - sx(z.x0)}
              height={sy(z.y0) - sy(z.y1)}
              fill={v.primary.main}
              fillOpacity={0.08}
              stroke={v.primary.main}
              strokeOpacity={0.35}
              strokeDasharray="3 3"
            />
            {compact ? null : (
              <text x={sx(z.x0) + 4} y={sy(z.y1) + 11} fontSize={9} fill={v.text.secondary}>
                {z.label}
              </text>
            )}
          </g>
        ))}
        {diagram.lines.map((l, i) => (
          <g key={`l-${l.label}`}>
            <polyline
              points={pts(l.points)}
              fill="none"
              stroke={color[l.kind]}
              strokeWidth={l.kind === "level" ? 1 : 1.5}
              strokeDasharray={l.kind === "level" ? "4 3" : undefined}
            />
            {compact ? null : (
              <text
                x={sx(l.points[l.points.length - 1][0]) - 2}
                y={sy(l.points[l.points.length - 1][1]) + (i % 2 ? 12 : -5)}
                fontSize={9}
                textAnchor="end"
                fill={color[l.kind]}
              >
                {l.label}
              </text>
            )}
          </g>
        ))}
        <polyline points={pts(diagram.path)} fill="none" stroke={v.text.primary} strokeWidth={2} strokeLinejoin="round" />
        {diagram.markers.map((m) => (
          <g key={`m-${m.kind}-${m.label}`}>
            <circle cx={sx(m.x)} cy={sy(m.y)} r={4} fill={color[m.kind]} stroke={v.background.paper} strokeWidth={1.5} />
            {compact ? null : (
              <text
                x={sx(m.x) + (m.x > 70 ? -7 : 7)}
                y={sy(m.y) + 3}
                fontSize={9.5}
                fontWeight={600}
                textAnchor={m.x > 70 ? "end" : "start"}
                fill={color[m.kind]}
              >
                {MARKER_GLYPH[m.kind]} {m.label}
              </text>
            )}
          </g>
        ))}
      </Box>
      {compact ? null : (
        <Box component="figcaption" sx={{ px: 1.5, py: 1, borderTop: 1, borderColor: "divider", typography: "caption", color: "text.secondary" }}>
          {diagram.caption}
        </Box>
      )}
    </Box>
  );
}
