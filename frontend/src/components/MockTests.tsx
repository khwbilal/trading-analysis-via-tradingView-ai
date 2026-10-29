import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Checkbox from "@mui/material/Checkbox";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormGroup from "@mui/material/FormGroup";
import FormLabel from "@mui/material/FormLabel";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import Close from "@mui/icons-material/Close";
import ScienceOutlined from "@mui/icons-material/ScienceOutlined";
import Sync from "@mui/icons-material/Sync";
import { Fragment, useCallback, useEffect, useState } from "react";
import { api, type ArenaAgent, type MockSession, type Strategy, type Style } from "../api";
import { GLYPH, STYLE_LABEL, biasClass, fmtPx, fmtR, fmtRate, fmtWhen } from "../lib/format";
import { useFeedback } from "./feedback";
import { ActionButton, DataTable, EmptyState, Na, Num, Pill, SectionCard, StatusPill, V } from "./ui";

const ALL_STYLES: Style[] = ["scalp", "day", "swing", "position", "hold"];

/** Start a mock test (WL-081): a strategy or an agent, styles, your coins, backtest now or paper trade live. */
export function MockTestDialog({
  strategies,
  agents,
  initial,
  onClose,
  onStarted,
}: Readonly<{
  strategies: Strategy[];
  agents: ArenaAgent[];
  initial?: { kind: "strategy" | "agent"; ref: string };
  onClose: () => void;
  onStarted: () => void;
}>) {
  const phone = useMediaQuery((t) => t.breakpoints.down("sm"));
  const { toast } = useFeedback();
  const testable = strategies.filter((s) => s.backtestable);
  const tradingAgents = agents.filter((a) => a.stance !== "meta");
  const [kind, setKind] = useState<"strategy" | "agent">(initial?.kind ?? "strategy");
  const [ref, setRef] = useState(initial?.ref ?? testable[0]?.id ?? "");
  const [mode, setMode] = useState<"backtest" | "paper">("backtest");
  const [styles, setStyles] = useState<Style[]>(["day"]);
  const [symbols, setSymbols] = useState("");
  const [days, setDays] = useState("7");
  const [depth, setDepth] = useState<"quick" | "deep">("quick");
  const [busy, setBusy] = useState(false);
  const coins = symbols.split(/[\s,]+/).filter(Boolean);
  const options = kind === "strategy" ? testable.map((s) => ({ id: s.id, name: s.name })) : tradingAgents.map((a) => ({ id: a.id, name: a.name }));
  const problem = !ref ? "Choose a strategy or agent." : !styles.length ? "Choose at least one style." : mode === "paper" && !coins.length ? "Paper mode needs your coins." : null;

  async function start() {
    setBusy(true);
    try {
      await api.startMock({ kind, ref, mode, styles, symbols: coins, days: Number(days) || 7, depth });
      toast(mode === "paper" ? "Mock paper test started; it checks with the paper job every 4 hours, or with Check now." : "Mock backtest started.");
      onStarted();
      onClose();
    } catch (err) {
      toast(`Mock test: ${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open onClose={onClose} fullScreen={phone} fullWidth maxWidth="sm" aria-labelledby="mockTitle">
      <DialogTitle id="mockTitle" sx={{ display: "flex", alignItems: "center", gap: 1, pr: 1 }}>
        <Box sx={{ flex: 1 }}>
          Mock test
          <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
            Try a strategy or an agent on your coins: a backtest now, or paper trades on live candles. No AI, nothing sent to Binance.
          </Typography>
        </Box>
        <IconButton aria-label="Close" onClick={onClose}>
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          <ToggleButtonGroup
            exclusive
            size="small"
            value={kind}
            onChange={(_e, v: "strategy" | "agent" | null) => {
              if (!v) return;
              setKind(v);
              setRef(v === "strategy" ? (testable[0]?.id ?? "") : (tradingAgents[0]?.id ?? ""));
            }}
            aria-label="What to test"
          >
            <ToggleButton value="strategy">Strategy</ToggleButton>
            <ToggleButton value="agent">Agent</ToggleButton>
          </ToggleButtonGroup>
          <TextField select size="small" label={kind === "strategy" ? "Strategy" : "Agent"} value={ref} onChange={(e) => setRef(e.target.value)}>
            {options.map((o) => (
              <MenuItem key={o.id} value={o.id}>
                {o.name}
              </MenuItem>
            ))}
          </TextField>
          <Box>
            <FormLabel component="legend">Styles</FormLabel>
            <FormGroup row>
              {ALL_STYLES.map((st) => (
                <FormControlLabel
                  key={st}
                  control={<Checkbox checked={styles.includes(st)} onChange={() => setStyles(styles.includes(st) ? styles.filter((x) => x !== st) : [...styles, st])} />}
                  label={STYLE_LABEL[st]}
                />
              ))}
            </FormGroup>
          </Box>
          <TextField
            size="small"
            label="Your coins"
            value={symbols}
            onChange={(e) => setSymbols(e.target.value)}
            placeholder="SOL, PEPEUSDT, TSLAUSDT"
            helperText={mode === "paper" ? "Required for paper mode" : "Empty: the fixed coin groups"}
          />
          <ToggleButtonGroup exclusive size="small" value={mode} onChange={(_e, v: "backtest" | "paper" | null) => v && setMode(v)} aria-label="Mode">
            <ToggleButton value="backtest">Backtest now</ToggleButton>
            <ToggleButton value="paper">Paper trade live</ToggleButton>
          </ToggleButtonGroup>
          {mode === "paper" ? (
            <TextField size="small" label="Days" value={days} onChange={(e) => setDays(e.target.value.replace(/\D/g, ""))} helperText="It opens trades on new signals for this long (up to 90)" />
          ) : (
            <TextField select size="small" label="Depth" value={depth} onChange={(e) => setDepth(e.target.value as "quick" | "deep")}>
              <MenuItem value="quick">Quick: the newest 1,000 candles</MenuItem>
              <MenuItem value="deep">Deep: 5,000 candles of history</MenuItem>
            </TextField>
          )}
          {problem ? <Alert severity="info">{problem}</Alert> : null}
          <Stack direction="row" sx={{ justifyContent: "flex-end" }}>
            <ActionButton primary busy={busy} busyLabel="Starting…" disabled={Boolean(problem)} onClick={() => void start()}>
              Start mock test
            </ActionButton>
          </Stack>
        </Stack>
      </DialogContent>
    </Dialog>
  );
}

/** The mock test sessions with their paper trades (WL-081). */
export function MockSessionsCard({
  active,
  names,
  version,
}: Readonly<{ active: boolean; names: Record<string, string>; version: number }>) {
  const { toast, ask } = useFeedback();
  const [sessions, setSessions] = useState<MockSession[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [openId, setOpenId] = useState<number | null>(null);

  const load = useCallback(() => {
    api
      .mocks()
      .then((r) => setSessions(r.sessions))
      .catch(() => setSessions([]));
  }, []);
  useEffect(() => {
    if (active) load();
  }, [active, load, version]);
  useEffect(() => {
    if (!active || !sessions?.some((s) => s.status === "running")) return;
    const id = setTimeout(load, 3000);
    return () => clearTimeout(id);
  }, [active, sessions, load]);

  async function checkNow() {
    setBusy(true);
    try {
      const r = await api.checkMocks();
      toast(`Opened ${String(r.scan.opened)} and closed ${String(r.check.closed)} mock trades.`);
      load();
    } catch (err) {
      toast(`Check failed: ${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  async function stop(s: MockSession) {
    const ok = await ask({ title: "Stop this mock test?", text: "It opens no new trades; open trades still close and everything stays stored.", okLabel: "Stop" });
    if (!ok) return;
    await api.stopMock(s.id);
    load();
  }

  return (
    <SectionCard
      title="Mock tests"
      icon={<ScienceOutlined />}
      right={
        <ActionButton compact icon={<Sync />} busy={busy} busyLabel="Checking…" onClick={() => void checkNow()}>
          Check now
        </ActionButton>
      }
      noPadding
    >
      {sessions && !sessions.length ? <EmptyState icon={<ScienceOutlined />} text="No mock tests yet. Start one with Mock test." /> : null}
      {sessions?.length ? (
        <DataTable minWidth={980} maxHeight={560}>
          <TableHead>
            <TableRow>
              <TableCell>Started</TableCell>
              <TableCell>Testing</TableCell>
              <TableCell>Mode</TableCell>
              <TableCell>Styles · coins</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Trades</TableCell>
              <TableCell align="right">Win rate</TableCell>
              <TableCell align="right">Total R</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {sessions.map((s) => (
              <Fragment key={s.id}>
                <TableRow hover onClick={() => setOpenId(openId === s.id ? null : s.id)} sx={{ cursor: "pointer" }}>
                  <TableCell sx={{ whiteSpace: "nowrap" }}>
                    <V value={fmtWhen(s.created_at)} />
                  </TableCell>
                  <TableCell>
                    {names[s.ref] ?? s.ref}
                    <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                      {s.kind}
                    </Typography>
                  </TableCell>
                  <TableCell>{s.mode === "paper" ? "Paper" : "Backtest"}</TableCell>
                  <TableCell sx={{ maxWidth: 240, overflowWrap: "anywhere" }}>
                    {s.styles.map((x) => STYLE_LABEL[x] ?? x).join(", ")}
                    <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                      {s.symbols.length ? s.symbols.join(", ") : "fixed coin groups"}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <StatusPill status={s.status === "active" ? "open" : s.status} title={s.message ?? (s.ends_at ? `Until ${fmtWhen(s.ends_at) ?? ""}` : undefined)} />
                    {s.mode === "backtest" && s.run_ref ? (
                      <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                        {s.kind === "agent" ? "Arena" : "Backtest"} run {s.run_ref}
                      </Typography>
                    ) : null}
                  </TableCell>
                  <TableCell align="right">
                    <Num>{s.mode === "paper" ? `${String(s.stats.closed)} / ${String(s.stats.trades)}` : (s.message ?? "")}</Num>
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtRate(s.stats.win_rate)} reason={s.mode === "paper" ? "No closed trades yet" : "See the run"} />
                  </TableCell>
                  <TableCell align="right">
                    <V value={fmtR(s.stats.total_r, 2)} reason={s.mode === "paper" ? "No closed trades yet" : "See the run"} />
                  </TableCell>
                  <TableCell>
                    {s.status === "active" ? (
                      <ActionButton compact onClick={() => void stop(s)}>
                        Stop
                      </ActionButton>
                    ) : null}
                  </TableCell>
                </TableRow>
                {openId === s.id && s.trades.length
                  ? s.trades.map((t) => {
                      const cls = biasClass(t.side);
                      return (
                        <TableRow key={`t-${String(t.id)}`} sx={{ "& td": { borderBottomStyle: "dashed" } }}>
                          <TableCell sx={{ pl: 4, whiteSpace: "nowrap" }}>
                            <V value={fmtWhen(new Date(t.signal_time).toISOString())} />
                          </TableCell>
                          <TableCell>
                            <Num sx={{ fontWeight: 700 }}>{t.symbol}</Num>
                          </TableCell>
                          <TableCell>
                            <Pill glyph={GLYPH[cls]} label={t.side} tone={cls === "buy" ? "buy" : "sell"} />
                          </TableCell>
                          <TableCell>{STYLE_LABEL[t.style] ?? t.style}</TableCell>
                          <TableCell>
                            <StatusPill status={t.status} />
                          </TableCell>
                          <TableCell align="right">
                            <V value={fmtPx(t.entry)} />
                          </TableCell>
                          <TableCell align="right">
                            <V value={fmtPx(t.exit)} reason="Still open" />
                          </TableCell>
                          <TableCell align="right">
                            <V value={fmtR(t.r_multiple, 2)} reason="Still open" />
                          </TableCell>
                          <TableCell sx={{ color: "text.secondary", maxWidth: 280 }}>{t.retro ?? t.exit_reason ?? ""}</TableCell>
                        </TableRow>
                      );
                    })
                  : null}
                {openId === s.id && !s.trades.length ? (
                  <TableRow>
                    <TableCell colSpan={9} sx={{ pl: 4, color: "text.secondary" }}>
                      {s.mode === "paper" ? "No signal yet. It checks with the paper job, or Check now." : <Na reason="Backtest results are on the Backtests or Arena page" />}
                    </TableCell>
                  </TableRow>
                ) : null}
              </Fragment>
            ))}
          </TableBody>
        </DataTable>
      ) : null}
    </SectionCard>
  );
}
