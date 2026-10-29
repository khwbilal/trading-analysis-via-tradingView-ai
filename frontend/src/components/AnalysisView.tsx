import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { Cell, ParsedAnalysis } from "../lib/analysis";
import { V } from "./ui";

const BOX = { border: 1, borderColor: "divider", borderRadius: 1, bgcolor: "background.paper", p: 1.25 } as const;

function Heading({ children }: Readonly<{ children: string }>) {
  return (
    <Typography variant="caption" component="div" sx={{ color: "text.secondary", fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.4, mb: 0.75 }}>
      {children}
    </Typography>
  );
}

function CellGrid({ title, cells }: Readonly<{ title: string; cells: Cell[] }>) {
  return (
    <Box sx={BOX}>
      <Heading>{title}</Heading>
      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 1 }}>
        {cells.map((c, i) => (
          <Box key={`${c.label}-${String(i)}`} sx={{ minWidth: 0, bgcolor: "surface.paper2", borderRadius: 1, px: 1, py: 0.75 }}>
            <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
              {c.label}
            </Typography>
            <Box sx={{ fontWeight: 700, fontSize: "0.875rem", overflowWrap: "anywhere" }}>
              <V value={c.value || null} reason="No single price given: see the note" />
            </Box>
            {c.note ? (
              <Typography variant="caption" component="div" sx={{ color: "text.secondary", whiteSpace: "pre-wrap", lineHeight: 1.35, mt: 0.25 }}>
                {c.note}
              </Typography>
            ) : null}
          </Box>
        ))}
      </Box>
    </Box>
  );
}

/** An analysis as boxes (WL-114): header, levels, TP ladder, the call's rows, explanation, strategy. */
export default function AnalysisView({ p }: Readonly<{ p: ParsedAnalysis }>) {
  return (
    <Stack spacing={1} sx={{ whiteSpace: "normal", width: "100%" }}>
      {p.title || p.source ? (
        <Box>
          {p.title ? (
            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
              {p.title}
            </Typography>
          ) : null}
          {p.source ? (
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              {p.source}
            </Typography>
          ) : null}
        </Box>
      ) : null}

      {p.override ? (
        <Box sx={{ bgcolor: "surface.warn", borderLeft: 3, borderColor: "warning.main", borderRadius: 1, px: 1.25, py: 0.75, typography: "body2" }}>
          <Box component="span" aria-hidden sx={{ color: "warning.main", fontWeight: 700, mr: 0.5 }}>
            !
          </Box>
          <strong>Desk override:</strong> {p.override}
        </Box>
      ) : null}

      {p.levels.length ? <CellGrid title="Levels" cells={p.levels} /> : null}
      {p.ladder.length ? <CellGrid title="Targets" cells={p.ladder} /> : null}

      {p.rows.length ? (
        <Box sx={BOX}>
          <Heading>The call</Heading>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "minmax(90px, max-content) 1fr" }, columnGap: 1.5, rowGap: 0.75 }}>
            {p.rows.map((r, i) => (
              <Box key={`${r.label}-${String(i)}`} sx={{ display: "contents" }}>
                <Typography variant="body2" sx={{ fontWeight: 700, color: "text.secondary" }}>
                  {r.label}
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", mb: { xs: 0.75, sm: 0 } }}>
                  {r.text}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      ) : null}

      {p.points.length ? (
        <Box sx={BOX}>
          <Heading>Explanation</Heading>
          <Stack spacing={0.75}>
            {p.points.map((r, i) => (
              <Box key={`${r.label}-${String(i)}`} sx={{ borderLeft: 3, borderColor: "divider", pl: 1, typography: "body2", overflowWrap: "anywhere" }}>
                {r.label ? <strong>{r.label}: </strong> : null}
                {r.text}
              </Box>
            ))}
          </Stack>
        </Box>
      ) : null}

      {p.rest.length ? (
        <Box sx={{ ...BOX, typography: "body2", whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{p.rest.join("\n")}</Box>
      ) : null}

      {p.strategy ? (
        <Box sx={{ ...BOX, bgcolor: "surface.action" }}>
          <Heading>Strategy record</Heading>
          <Typography variant="body2" sx={{ overflowWrap: "anywhere" }}>
            {p.strategy}
          </Typography>
        </Box>
      ) : null}
    </Stack>
  );
}
