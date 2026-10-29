import Autocomplete from "@mui/material/Autocomplete";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import InputAdornment from "@mui/material/InputAdornment";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import ArrowForward from "@mui/icons-material/ArrowForward";
import History from "@mui/icons-material/History";
import Search from "@mui/icons-material/Search";
import { forwardRef, useEffect, useState, type ReactNode } from "react";
import { api, type SymbolResult } from "../api";
import { readRecents } from "../lib/storage";
import { monoSx } from "./ui";
import { PAGES, type PageKey } from "../lib/nav";

type PairOption = {
  kind: "pair";
  group: string;
  symbol: string;
  exchange: string;
  tv: string;
  name?: string | null;
  type?: string;
  detail: string;
};
type PageOption = { kind: "page"; group: string; key: PageKey; label: string };
type Option = PairOption | PageOption;

function toPair(r: SymbolResult, group: string): PairOption {
  return {
    kind: "pair",
    group,
    symbol: r.symbol,
    exchange: r.exchange,
    tv: r.tv_symbol,
    name: r.name,
    type: r.type,
    detail: `${r.exchange} · ${r.kind}`,
  };
}

/** Recent pairs, then the commodities (WL-097), then the pages. */
function defaultOptions(commodities: Option[] = [], withPages = true): Option[] {
  const recent: Option[] = readRecents().map((r) => ({
    kind: "pair",
    group: "Recent",
    symbol: r.symbol,
    exchange: r.exchange,
    tv: r.tv_symbol,
    detail: r.exchange,
  }));
  const pages: Option[] = (withPages ? (Object.keys(PAGES) as PageKey[]) : []).map((key) => ({
    kind: "page",
    group: "Go to",
    key,
    label: PAGES[key],
  }));
  return [...recent, ...commodities, ...pages];
}

/** Wrap the first case-insensitive match of the query in a <mark>; the text stays plain React text. */
function Highlight({ text, query }: Readonly<{ text: string; query: string }>): ReactNode {
  const q = query.trim().replace(/[/:\s-]/g, "");
  if (!q) return text;
  const i = text.toLowerCase().indexOf(q.toLowerCase());
  if (i < 0) return text;
  return (
    <>
      {text.slice(0, i)}
      <Box component="mark" sx={{ bgcolor: "primary.light", color: "primary.main", borderRadius: 0.5, px: 0 }}>
        {text.slice(i, i + q.length)}
      </Box>
      {text.slice(i + q.length)}
    </>
  );
}

export type PairSearchProps = {
  exchange: string;
  onPickPair: (symbol: string, exchange?: string, tv?: string) => void;
  /** WL-149: without it the search lists pairs only (adding to a watchlist). */
  onPickPage?: (page: PageKey) => void;
  placeholder?: string;
  /** Open the list and focus the input on mount (the phone dialog). */
  autoFocus?: boolean;
  onDone?: () => void;
};

const PairSearch = forwardRef<HTMLInputElement, PairSearchProps>(function PairSearch(
  { exchange, onPickPair, onPickPage, autoFocus = false, onDone, placeholder },
  inputRef,
) {
  const [input, setInput] = useState("");
  const [results, setResults] = useState<Option[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [open, setOpen] = useState(autoFocus);
  const withPages = !!onPickPage;
  const [defaults, setDefaults] = useState<Option[]>(() => defaultOptions([], withPages));
  const [commodities, setCommodities] = useState<Option[]>([]);

  useEffect(() => {
    let cancelled = false;
    api
      .symbolsByType("commodity")
      .then((res) => {
        if (cancelled) return;
        const list = res.results.map((r) => toPair(r, "Commodities"));
        setCommodities(list);
        setDefaults(defaultOptions(list, withPages));
      })
      .catch(() => undefined); // the group is optional; search still works without it
    return () => {
      cancelled = true;
    };
  }, [withPages]);

  const query = input.trim();

  useEffect(() => {
    if (!query) {
      setResults([]);
      setLoading(false);
      setError(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    const timer = setTimeout(() => {
      api
        .searchSymbols(query, exchange)
        .then((res) => {
          if (cancelled) return;
          setResults(
            res.results.map((r) => toPair(r, "Pairs")),
          );
          setError(false);
          setLoading(false);
        })
        .catch(() => {
          if (cancelled) return;
          setResults([]);
          setError(true);
          setLoading(false);
        });
    }, 160);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, exchange]);

  const options = query ? results : defaults;

  let noOptions = "No matches. Try BTC, ZEC or SOLUSDT.P, or press Enter to open the text as a pair.";
  if (error) noOptions = "Search is unavailable. Is the backend running?";

  function finish() {
    setInput("");
    setOpen(false);
    onDone?.();
  }

  return (
    <Autocomplete<Option, false, false, true>
      freeSolo
      autoHighlight
      openOnFocus
      blurOnSelect
      clearOnBlur
      handleHomeEndKeys
      open={open}
      onOpen={() => {
        setDefaults(defaultOptions(commodities, withPages));
        setOpen(true);
      }}
      onClose={() => setOpen(false)}
      options={options}
      value={null}
      inputValue={input}
      onInputChange={(_e, v, reason) => {
        if (reason !== "reset") setInput(v);
      }}
      filterOptions={(x) => x}
      groupBy={(o) => o.group}
      getOptionLabel={(o) => (typeof o === "string" ? o : o.kind === "page" ? o.label : o.symbol)}
      loading={loading}
      loadingText="Searching…"
      noOptionsText={noOptions}
      onChange={(_e, value) => {
        if (value === null) return;
        if (typeof value === "string") {
          // Enter with no match: try the raw text as a pair, as before.
          if (value.trim()) onPickPair(value.trim());
        } else if (value.kind === "page") {
          onPickPage?.(value.key);
        } else {
          onPickPair(value.symbol, value.exchange, value.tv);
        }
        finish();
      }}
      // WL-102: the popper itself is 420 px wide so the overflow guard keeps it inside the window (the wider paper was
      // cut off at the right), and fixed positioning keeps it under the fixed top bar while the page scrolls.
      slotProps={{
        listbox: { sx: { maxHeight: { xs: "70vh", sm: "min(420px, calc(100vh - 120px))" } } },
        popper: {
          placement: "bottom-start",
          popperOptions: { strategy: "fixed" },
          modifiers: [{ name: "preventOverflow", options: { padding: 8, altAxis: true } }, { name: "flip", enabled: false }],
          sx: { minWidth: { sm: 420 }, maxWidth: "calc(100vw - 16px)" },
        },
      }}
      renderOption={(props, o) => {
        const { key, ...rest } = props;
        if (o.kind === "page") {
          return (
            <Box component="li" key={key} {...rest} sx={{ gap: 1.5 }}>
              <ArrowForward fontSize="small" sx={{ color: "text.secondary" }} />
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {o.label}
              </Typography>
            </Box>
          );
        }
        return (
          <Box component="li" key={key} {...rest} sx={{ gap: 1.5, minHeight: 48 }}>
            {o.group === "Recent" ? <History fontSize="small" sx={{ color: "text.secondary" }} /> : null}
            <Box sx={{ minWidth: 0, flex: 1 }}>
              <Box sx={[monoSx, { fontWeight: 600, fontSize: "0.875rem" }]}>
                <Highlight text={o.symbol} query={query} />
              </Box>
              {o.name ? (
                <Typography variant="caption" component="div" noWrap sx={{ color: "text.secondary" }}>
                  <Highlight text={o.name} query={query} />
                </Typography>
              ) : null}
            </Box>
            {o.type ? <Chip size="small" variant="outlined" label={o.type} sx={{ textTransform: "lowercase" }} /> : null}
            <Typography variant="caption" noWrap sx={{ color: "text.secondary", flexShrink: 0 }}>
              {o.detail}
            </Typography>
          </Box>
        );
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          inputRef={inputRef}
          autoFocus={autoFocus}
          size="small"
          placeholder={placeholder ?? "Search pairs, stocks, ETFs"}
          slotProps={{
            ...params.slotProps,
            input: {
              ...params.slotProps.input,
              startAdornment: (
                <InputAdornment position="start">
                  <Search fontSize="small" />
                </InputAdornment>
              ),
              endAdornment: (
                <>
                  <Box
                    component="kbd"
                    sx={{
                      display: { xs: "none", md: onPickPage ? "inline-block" : "none" },
                      fontSize: "0.6875rem",
                      color: "text.secondary",
                      border: 1,
                      borderColor: "divider",
                      borderRadius: 1,
                      px: 0.75,
                      mr: 0.5,
                    }}
                  >
                    Ctrl K
                  </Box>
                  {params.slotProps.input.endAdornment}
                </>
              ),
            },
            htmlInput: { ...params.slotProps.htmlInput, spellCheck: false, "aria-label": "Search pairs" },
          }}
        />
      )}
    />
  );
});

export default PairSearch;
