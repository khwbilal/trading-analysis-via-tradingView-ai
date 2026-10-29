import Autocomplete from "@mui/material/Autocomplete";
import Badge from "@mui/material/Badge";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Collapse from "@mui/material/Collapse";
import InputAdornment from "@mui/material/InputAdornment";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import FilterList from "@mui/icons-material/FilterList";
import Search from "@mui/icons-material/Search";
import { type ReactElement, useMemo, useState } from "react";
import { usePref } from "../lib/storage";

/** One filterable column (WL-127): free text, a pick of the values present, or a number range. */
export type FilterColumn<T> =
  | { key: string; label: string; kind: "text"; get: (r: T) => string | null | undefined }
  | { key: string; label: string; kind: "choice"; get: (r: T) => string | string[] | null | undefined; labelOf?: (v: string) => string }
  | { key: string; label: string; kind: "range"; get: (r: T) => number | null | undefined; hint?: string };

type FilterState = {
  q: string;
  text: Record<string, string>;
  choice: Record<string, string[]>;
  min: Record<string, string>;
  max: Record<string, string>;
};

const EMPTY: FilterState = { q: "", text: {}, choice: {}, min: {}, max: {} };

function validState(v: unknown): boolean {
  const s = v as Partial<FilterState> | null;
  return Boolean(s) && typeof s?.q === "string" && ["text", "choice", "min", "max"].every((k) => typeof s?.[k as keyof FilterState] === "object");
}

const asList = (v: string | string[] | null | undefined): string[] => (v === null || v === undefined ? [] : Array.isArray(v) ? v : [v]);
const num = (s: string | undefined): number | null => (s === undefined || s.trim() === "" || !Number.isFinite(Number(s)) ? null : Number(s));

/** WL-127: a search box over `searchOf` plus a filter per column, kept per browser (WL-101).
 * Returns the rows that pass and the filter bar to render above the table. A number range leaves out the
 * rows where that value is missing. */
export function useTableFilters<T>(
  prefKey: string,
  rows: readonly T[],
  columns: readonly FilterColumn<T>[],
  searchOf: (r: T) => string,
  noun = "rows",
): { shown: T[]; bar: ReactElement; active: number } {
  const [state, setState] = usePref<FilterState>(prefKey, EMPTY, validState);
  const [open, setOpen] = useState(false);

  const options = useMemo(() => {
    const out: Record<string, string[]> = {};
    for (const c of columns) {
      if (c.kind !== "choice") continue;
      const seen = new Set<string>();
      for (const r of rows) for (const v of asList(c.get(r))) seen.add(v);
      out[c.key] = [...seen].sort((a, b) => a.localeCompare(b));
    }
    return out;
  }, [rows, columns]);

  const shown = useMemo(() => {
    const q = state.q.trim().toLowerCase();
    return rows.filter((r) => {
      if (q && !searchOf(r).toLowerCase().includes(q)) return false;
      for (const c of columns) {
        if (c.kind === "text") {
          const want = (state.text[c.key] ?? "").trim().toLowerCase();
          if (want && !(c.get(r) ?? "").toLowerCase().includes(want)) return false;
        } else if (c.kind === "choice") {
          const want = state.choice[c.key] ?? [];
          if (want.length && !asList(c.get(r)).some((v) => want.includes(v))) return false;
        } else {
          const lo = num(state.min[c.key]);
          const hi = num(state.max[c.key]);
          if (lo === null && hi === null) continue;
          const v = c.get(r);
          if (v === null || v === undefined || (lo !== null && v < lo) || (hi !== null && v > hi)) return false;
        }
      }
      return true;
    });
  }, [rows, columns, state, searchOf]);

  const active =
    Object.values(state.text).filter((v) => v.trim()).length +
    Object.values(state.choice).filter((v) => v.length).length +
    columns.filter((c) => c.kind === "range" && (num(state.min[c.key]) !== null || num(state.max[c.key]) !== null)).length;
  const any = active > 0 || state.q.trim() !== "";
  const put = <K extends "text" | "choice" | "min" | "max">(part: K, key: string, value: FilterState[K][string]) =>
    setState((s) => ({ ...s, [part]: { ...s[part], [key]: value } }));

  const bar = (
    <Stack spacing={1.5}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ alignItems: { sm: "center" } }}>
        <TextField
          size="small"
          placeholder={`Search ${noun}`}
          value={state.q}
          onChange={(e) => setState((s) => ({ ...s, q: e.target.value }))}
          sx={{ flex: 1, maxWidth: { sm: 360 } }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <Search fontSize="small" />
                </InputAdornment>
              ),
            },
            htmlInput: { "aria-label": `Search ${noun}` },
          }}
        />
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <Button
            variant={open ? "contained" : "outlined"}
            color="primary"
            size="small"
            disableElevation
            startIcon={
              <Badge badgeContent={active} color="primary" invisible={!active || open}>
                <FilterList fontSize="small" />
              </Badge>
            }
            onClick={() => setOpen(!open)}
            aria-expanded={open}
          >
            Filters
          </Button>
          <Button size="small" disabled={!any} onClick={() => setState(EMPTY)}>
            Clear
          </Button>
          <Typography variant="caption" sx={{ color: "text.secondary", whiteSpace: "nowrap" }} aria-live="polite">
            {shown.length === rows.length ? `${String(rows.length)} ${noun}` : `${String(shown.length)} of ${String(rows.length)} ${noun}`}
          </Typography>
        </Stack>
      </Stack>
      <Collapse in={open} unmountOnExit>
        {/* WL-129: every filter is a caption over one 40px row, so the grid lines up whatever the kind. */}
        <Box sx={{ display: "grid", columnGap: 1.5, rowGap: 1.25, alignItems: "start", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}>
          {columns.map((c) => (
            <Box key={c.key} component="fieldset" title={c.kind === "range" ? c.hint : undefined} sx={{ border: 0, m: 0, p: 0, minWidth: 0 }}>
              <Typography component="legend" variant="caption" noWrap sx={{ display: "block", width: "100%", color: "text.secondary", p: 0, mb: 0.5 }}>
                {c.label}
              </Typography>
              {control(c)}
            </Box>
          ))}
        </Box>
      </Collapse>
    </Stack>
  );
  return { shown, bar, active };

  function control(c: FilterColumn<T>): ReactElement {
    if (c.kind === "text") {
      return (
        <TextField
          fullWidth
          size="small"
          placeholder="Contains"
          value={state.text[c.key] ?? ""}
          onChange={(e) => put("text", c.key, e.target.value)}
          slotProps={{ htmlInput: { "aria-label": c.label } }}
        />
      );
    }
    if (c.kind === "choice") {
      const chosen = state.choice[c.key] ?? [];
      return (
        <Autocomplete
          multiple
          fullWidth
          size="small"
          limitTags={1}
          options={options[c.key] ?? []}
          value={chosen}
          getOptionLabel={(v) => (c.labelOf ? c.labelOf(v) : v)}
          onChange={(_e, v) => put("choice", c.key, v)}
          slotProps={{ chip: { size: "small" } }}
          renderInput={(params) => (
            <TextField {...params} placeholder={chosen.length ? "" : "Any"} slotProps={{ ...params.slotProps, htmlInput: { ...params.slotProps.htmlInput, "aria-label": c.label } }} />
          )}
          sx={{ "& .MuiInputBase-root": { flexWrap: "nowrap", minHeight: 40 } }}
        />
      );
    }
    return (
      <Stack direction="row" spacing={0.75}>
        <TextField
          size="small"
          type="number"
          placeholder="From"
          value={state.min[c.key] ?? ""}
          onChange={(e) => put("min", c.key, e.target.value)}
          slotProps={{ htmlInput: { "aria-label": `${c.label} from` } }}
          sx={{ flex: 1, minWidth: 0 }}
        />
        <TextField
          size="small"
          type="number"
          placeholder="To"
          value={state.max[c.key] ?? ""}
          onChange={(e) => put("max", c.key, e.target.value)}
          slotProps={{ htmlInput: { "aria-label": `${c.label} to` } }}
          sx={{ flex: 1, minWidth: 0 }}
        />
      </Stack>
    );
  }
}
