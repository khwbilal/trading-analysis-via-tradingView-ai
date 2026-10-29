import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import AccountBalanceOutlined from "@mui/icons-material/AccountBalanceOutlined";
import { useEffect, useState, type ReactNode } from "react";
import { api, type FinancialQuarter, type FinancialsResponse } from "../api";
import { fmtCompact, fmtFixed, fmtPct, fmtPx, fmtWhen } from "../lib/format";
import { Na, Pill, SectionCard, V, monoSx } from "./ui";

type Col = { key: keyof FinancialQuarter; label: string; fmt: (v: unknown) => string | null; reason: string; qoq?: string };

const STOCK: Col[] = [
  { key: "revenue", label: "Revenue", fmt: (v) => fmtCompact(v, "$"), reason: "Not filed for this quarter yet", qoq: "revenue" },
  { key: "net_income", label: "Net income", fmt: (v) => fmtCompact(v, "$"), reason: "Not filed separately (often only in the annual report)", qoq: "net_income" },
  { key: "eps_diluted", label: "EPS", fmt: (v) => fmtFixed(v, 2), reason: "Not filed separately; Q4 EPS cannot be derived", qoq: "eps_diluted" },
  { key: "cash", label: "Cash", fmt: (v) => fmtCompact(v, "$"), reason: "No quarter-end cash filed" },
];
const MARKET: Col[] = [
  { key: "return_pct", label: "Return", fmt: (v) => fmtPct(v, 1), reason: "Not listed on Binance in this quarter" },
  { key: "high", label: "High", fmt: fmtPx, reason: "Not listed on Binance in this quarter" },
  { key: "low", label: "Low", fmt: fmtPx, reason: "Not listed on Binance in this quarter" },
  { key: "quote_volume", label: "Volume", fmt: (v) => fmtCompact(v, "$"), reason: "Not listed on Binance in this quarter" },
];
const PROTOCOL: Col[] = [
  { key: "fees", label: "Fees", fmt: (v) => fmtCompact(v, "$"), reason: "No DefiLlama fees for this quarter", qoq: "fees" },
  { key: "protocol_revenue", label: "Protocol revenue", fmt: (v) => fmtCompact(v, "$"), reason: "No DefiLlama revenue for this quarter" },
];

function Cell({ q, col }: Readonly<{ q: FinancialQuarter; col: Col }>) {
  const change = col.qoq && q.qoq ? q.qoq[col.qoq] : null;
  return (
    <TableCell align="right">
      <V value={col.fmt(q[col.key])} reason={col.reason} />
      {change !== null && change !== undefined ? (
        <Typography variant="caption" component="div" sx={[monoSx, { color: "text.secondary" }]}>
          {fmtPct(change, 0)} q/q
        </Typography>
      ) : null}
    </TableCell>
  );
}

const SOURCE_LABEL: Record<string, string> = { binance: "Binance", sec_edgar: "SEC EDGAR", defillama: "DefiLlama" };

/** The last 8 quarters for the pair on the desk (WL-046); cached on the server for 7 days. */
export default function FinancialsCard({ symbol, active }: Readonly<{ symbol: string; active: boolean }>) {
  const [data, setData] = useState<FinancialsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState("");

  useEffect(() => {
    if (!active || loaded === symbol) return;
    setLoaded(symbol);
    setData(null);
    setError(null);
    api
      .financials(symbol)
      .then(setData)
      .catch((err: unknown) => setError((err as Error).message));
  }, [active, symbol, loaded]);

  const icon = <AccountBalanceOutlined />;
  let cols: Col[] = MARKET;
  if (data?.kind === "stock") cols = [...STOCK, MARKET[0]];
  else if (data?.kind === "crypto" && data.protocol) cols = [...MARKET, ...PROTOCOL];

  let body: ReactNode;
  if (error) body = <Alert severity="warning">Financials unavailable: {error}</Alert>;
  else if (!data) body = <Skeleton height={120} />;
  else if (!data.quarters?.length) body = <Typography variant="body2" sx={{ color: "text.secondary" }}>No quarterly data from any source.</Typography>;
  else
    body = (
      <Box sx={{ overflowX: "auto", mx: -2 }}>
        <Table size="small" sx={{ minWidth: 560 }}>
          <TableHead>
            <TableRow>
              <TableCell>Quarter</TableCell>
              {cols.map((c) => (
                <TableCell key={c.key} align="right">
                  {c.label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {(data.quarters ?? []).map((q) => (
              <TableRow key={q.quarter}>
                <TableCell sx={[monoSx, { fontWeight: 600 }]}>
                  {q.quarter}
                  {q.partial ? (
                    <Typography variant="caption" component="div" sx={{ color: "text.secondary", fontFamily: "inherit" }}>
                      so far
                    </Typography>
                  ) : null}
                </TableCell>
                {cols.map((c) => (
                  <Cell key={c.key} q={q} col={c} />
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>
    );

  let note = "Quarterly market results from Binance.";
  if (data?.kind === "stock") note = `SEC EDGAR filings for ${data.ticker ?? "the company"} (calendar quarters; Q4 revenue and income derived from the annual report), return from Binance.`;
  else if (data?.kind === "etf") note = "ETFs file no earnings: quarterly market results only. Fund assets are not published by a free source.";
  else if (data?.kind === "crypto") note = data.protocol ? `Market results from Binance; fees and revenue of ${data.protocol} from DefiLlama.` : "No company results for a coin: quarterly market results from Binance.";

  return (
    <SectionCard
      title="Financials, last 8 quarters"
      icon={icon}
      right={
        data ? (
          <Stack direction="row" spacing={0.5}>
            {Object.entries(data.sources ?? {}).map(([name, s]) => (
              <Pill key={name} glyph={s.available ? "✓" : "✕"} label={SOURCE_LABEL[name] ?? name} tone={s.available ? "neutral" : "warn"} title={s.available ? `${SOURCE_LABEL[name] ?? name}: ok` : `${SOURCE_LABEL[name] ?? name}: ${s.error ?? "unavailable"}`} />
            ))}
          </Stack>
        ) : (
          <Na reason="Loading" />
        )
      }
    >
      {body}
      <Typography variant="caption" component="p" sx={{ color: "text.secondary", mt: 1.5, mb: 0 }}>
        {note} {data ? `Fetched ${fmtWhen(data.fetched_at) ?? "at an unknown time"}, refreshed weekly.` : ""}
      </Typography>
    </SectionCard>
  );
}
