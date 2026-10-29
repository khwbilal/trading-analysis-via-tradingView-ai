import Box from "@mui/material/Box";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import AssessmentOutlined from "@mui/icons-material/AssessmentOutlined";
import SchoolOutlined from "@mui/icons-material/SchoolOutlined";
import { useEffect, useState } from "react";
import { api, type ProReport } from "../api";
import { fmtFixed, fmtR, fmtRate, fmtWhen } from "../lib/format";
import { useFeedback } from "./feedback";
import { ActionButton, DataTable, EmptyState, Na, Num, SectionCard, SortCell, V, sortRows, useSort } from "./ui";

function Signed({ r, digits = 3 }: Readonly<{ r: number | null | undefined; digits?: number }>) {
  if (r === null || r === undefined) return <Na reason="No trades" />;
  const up = r > 0;
  return (
    <Num sx={{ color: r === 0 ? "text.secondary" : up ? "success.main" : "error.main", fontWeight: 600 }}>
      {r === 0 ? "" : up ? "▲ " : "▼ "}
      {fmtR(r, digits)}
    </Num>
  );
}

/** WL-144: the Pro report's sortable figure columns; drawdowns sort smallest first. */
const PRO_COLUMNS: [string, string, "asc" | "desc"][] = [
  ["trades", "Trades", "desc"],
  ["win_rate", "Win rate (95%)", "desc"],
  ["avg_r", "Expectancy (95%)", "desc"],
  ["profit_factor", "Profit factor", "desc"],
  ["payoff", "Payoff", "desc"],
  ["max_dd_r", "Max DD", "asc"],
  ["mc_dd95_r", "MC DD 95%", "asc"],
  ["out_of_sample", "Out-of-sample", "desc"],
  ["walk_forward", "Walk-forward", "desc"],
];

/** WL-079: the professional backtest reports: equal samples, intervals, out-of-sample and walk-forward. */
export function ProReportsCard({ active, running, version }: Readonly<{ active: boolean; running: boolean; version: unknown }>) {
  const { toast, ask } = useFeedback();
  const [reports, setReports] = useState<ProReport[] | null>(null);
  const [pick, setPick] = useState<number | null>(null);
  const [sortBy, onSort] = useSort("cca_arena_sort_pro", { key: "avg_r", dir: "desc" });
  const proSort = { sort: sortBy, onSort };
  useEffect(() => {
    if (!active) return;
    api
      .proReports()
      .then((r) => setReports(r.reports))
      .catch(() => setReports([]));
  }, [active, version]);

  async function runPro() {
    const ok = await ask({
      title: "Run a professional backtest?",
      text: "Every agent on more and more of the most traded Binance coins (and stock perpetuals) until each has 30,000 trades, or 150 coins. It pages years of candles and takes an hour or more, and adds several hundred MB to the database. No AI is used.",
      okLabel: "Run pro",
    });
    if (!ok) return;
    try {
      await api.runPro();
      toast("Professional run started; the report appears here when it finishes.");
    } catch (err) {
      toast(`Pro run: ${(err as Error).message}`);
    }
  }

  const report = reports?.find((r) => r.id === pick) ?? reports?.[0];
  // WL-144: sortable by any column; best expectancy first until a header is clicked.
  const rows = report
    ? sortRows(Object.entries(report.agents), sortBy, ([, a], k) => {
        if (k === "name") return a.name;
        if (k === "out_of_sample") return a.out_of_sample?.avg_r;
        if (k === "walk_forward") return a.walk_forward?.positive;
        const v = a[k as keyof typeof a];
        return typeof v === "number" ? v : null;
      })
    : [];
  return (
    <SectionCard
      title="Professional backtest"
      icon={<AssessmentOutlined />}
      right={
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          {reports && reports.length > 1 ? (
            <TextField select size="small" value={report?.id ?? ""} onChange={(e) => setPick(Number(e.target.value))} sx={{ minWidth: 200 }}>
              {reports.map((r) => (
                <MenuItem key={r.id} value={r.id}>
                  Report {r.id} · {fmtWhen(r.created_at) ?? r.created_at}
                </MenuItem>
              ))}
            </TextField>
          ) : null}
          <ActionButton compact disabled={running} onClick={() => void runPro()}>
            Run pro
          </ActionButton>
        </Stack>
      }
      noPadding
    >
      {reports && !reports.length ? <EmptyState text="No professional report yet. Run pro replays every agent until each has 30,000 trades." /> : null}
      {report ? (
        <>
          <Typography variant="body2" sx={{ color: "text.secondary", px: 2, pt: 2 }}>
            Report {report.id}: at most {report.params.sample.toLocaleString()} trades per agent (seed {report.params.seed}), in time order, after
            fees and slippage. In-sample is the first 70% in time, out-of-sample the last 30%. Win rate alone does not pay: read the expectancy and
            the out-of-sample column first.
          </Typography>
          <DataTable minWidth={1240} maxHeight="none">
            <TableHead>
              <TableRow>
                <SortCell id="name" first="asc" {...proSort}>
                  Agent
                </SortCell>
                {PRO_COLUMNS.map(([id, label, first]) => (
                  <SortCell key={id} id={id} align="right" first={first} {...proSort}>
                    {label}
                  </SortCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map(([id, a]) => (
                <TableRow key={id} hover>
                  <TableCell sx={{ fontWeight: 600 }}>{a.name}</TableCell>
                  <TableCell align="right">
                    <Num>{a.trades.toLocaleString()}</Num>
                    {a.available > a.trades ? (
                      <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                        of {a.available.toLocaleString()}
                      </Typography>
                    ) : null}
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtRate(a.win_rate)} />
                    {a.win_rate_ci ? (
                      <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                        {a.win_rate_ci[0]} to {a.win_rate_ci[1]}%
                      </Typography>
                    ) : null}
                  </TableCell>
                  <TableCell align="right">
                    <Signed r={a.avg_r} />
                    {a.avg_r_ci ? (
                      <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                        {fmtR(a.avg_r_ci[0], 3)} to {fmtR(a.avg_r_ci[1], 3)}
                      </Typography>
                    ) : null}
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtFixed(a.profit_factor, 2)} reason="No losses" />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtFixed(a.payoff, 2)} reason="No losses" />
                  </TableCell>
                  <TableCell align="right">
                    <V value={a.max_dd_r !== undefined ? `${fmtFixed(a.max_dd_r, 1) ?? ""}R` : null} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={a.mc_dd95_r !== null && a.mc_dd95_r !== undefined ? `${fmtFixed(a.mc_dd95_r, 1) ?? ""}R` : null} reason="Too few trades" />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtRate(a.out_of_sample?.win_rate)} reason="Too few trades" />
                    <Box>
                      <Signed r={a.out_of_sample?.avg_r} />
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Num>{a.walk_forward ? `${String(a.walk_forward.positive)} of ${String(a.walk_forward.folds.length)}` : ""}</Num>
                    <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                      folds positive
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </DataTable>
        </>
      ) : null}
    </SectionCard>
  );
}

/** WL-080: what the agents learned, the digest the analysis remembers, and their rivalry. */
export function LessonsCard({ active, names, version }: Readonly<{ active: boolean; names: Record<string, string>; version: unknown }>) {
  const [data, setData] = useState<Awaited<ReturnType<typeof api.arenaLessons>> | null>(null);
  useEffect(() => {
    if (!active) return;
    api
      .arenaLessons()
      .then(setData)
      .catch(() => setData(null));
  }, [active, version]);
  const rivalry = (data?.lessons ?? []).filter((l) => l.kind === "mock").slice(0, 8);
  const filters = (data?.filters ?? []).filter((f) => f.active);
  return (
    <SectionCard title="Lessons and rivalry" icon={<SchoolOutlined />}>
      {!data ? <Typography variant="body2" sx={{ color: "text.secondary" }}>No lessons yet; they are written after each Arena run.</Typography> : null}
      {data ? (
        <Stack spacing={2}>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              What the analysis remembers
            </Typography>
            <Box component="pre" sx={{ m: 0, whiteSpace: "pre-wrap", fontFamily: "inherit", fontSize: "0.85rem", color: "text.secondary" }}>
              {data.digest.replace(/^# Arena lessons\n\n/, "")}
            </Box>
          </Box>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              Learned filters (kept only when they also held on trades they never saw)
            </Typography>
            {filters.length ? (
              <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                {filters.map((f) => (
                  <Typography component="li" variant="body2" key={`${f.agent_id}-${f.text}`}>
                    {names[f.agent_id] ?? f.agent_id} {f.text}.
                  </Typography>
                ))}
              </Box>
            ) : (
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                None yet.
              </Typography>
            )}
          </Box>
          {rivalry.length ? (
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 700 }}>
                Rivalry
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                {rivalry.map((l) => (
                  <Typography component="li" variant="body2" key={l.id}>
                    {l.text}
                  </Typography>
                ))}
              </Box>
            </Box>
          ) : null}
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            Full history: docs/arena/agents/&lt;agent&gt;.md, docs/arena/rivalry.md and docs/arena/reports/.
          </Typography>
        </Stack>
      ) : null}
    </SectionCard>
  );
}
