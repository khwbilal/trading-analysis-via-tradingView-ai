import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import Chip from "@mui/material/Chip";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import Close from "@mui/icons-material/Close";
import DeleteOutline from "@mui/icons-material/DeleteOutlined";
import EditOutlined from "@mui/icons-material/EditOutlined";
import { useCallback, useEffect, useMemo, useState } from "react";
import ScienceOutlined from "@mui/icons-material/ScienceOutlined";
import { api, type ArenaAgent, type BacktestResponse, type BacktestResult, type Strategy, type StrategyNote } from "../api";
import { useFeedback } from "../components/feedback";
import StrategyDiagram from "../components/StrategyDiagram";
import { MockSessionsCard, MockTestDialog } from "../components/MockTests";
import { ActionButton, DataTable, EmptyState, Na, PageHeader, Pill, V } from "../components/ui";
import { STYLE_LABEL, fmtR, fmtRate, fmtWhen, humanize } from "../lib/format";
import { usePref } from "../lib/storage";

const STYLES = ["scalp", "day", "swing"] as const;

function bestRow(results: BacktestResult[], id: string, min: number): BacktestResult | null {
  const rows = results.filter((r) => r.strategy_id === id && r.coin_group === "all" && r.trades >= min);
  if (!rows.length) return null;
  return rows.reduce((a, b) => ((b.win_rate ?? -1) > (a.win_rate ?? -1) ? b : a));
}

function StyleChips({ styles }: Readonly<{ styles: string[] }>) {
  return (
    <Stack direction="row" spacing={0.5} useFlexGap sx={{ flexWrap: "wrap" }}>
      {styles.map((s) => (
        <Chip key={s} size="small" variant="outlined" label={STYLE_LABEL[s] ?? s} />
      ))}
    </Stack>
  );
}

function Rule({ label, text }: Readonly<{ label: string; text: string }>) {
  return (
    <Box>
      <Typography variant="overline" component="div" sx={{ color: "text.secondary" }}>
        {label}
      </Typography>
      <Typography variant="body2">{text}</Typography>
    </Box>
  );
}

function Notes({ strategyId, onCount }: Readonly<{ strategyId: string; onCount: (id: string, n: number) => void }>) {
  const { ask, toast } = useFeedback();
  const [notes, setNotes] = useState<StrategyNote[] | null>(null);
  const [draft, setDraft] = useState("");
  const [editing, setEditing] = useState<{ id: number; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const res = await api.notes(strategyId);
    setNotes(res.notes);
    onCount(strategyId, res.notes.length);
  }, [strategyId, onCount]);

  useEffect(() => {
    load().catch((err: unknown) => toast(`Notes: ${(err as Error).message}`));
  }, [load, toast]);

  async function add() {
    if (!draft.trim()) return;
    setBusy(true);
    try {
      await api.addNote(strategyId, draft);
      setDraft("");
      await load();
    } catch (err) {
      toast(`Note not saved: ${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    if (!editing) return;
    try {
      await api.updateNote(editing.id, editing.text);
      setEditing(null);
      await load();
    } catch (err) {
      toast(`Note not saved: ${(err as Error).message}`);
    }
  }

  async function remove(n: StrategyNote) {
    const ok = await ask({ title: "Delete this note?", text: n.body.slice(0, 120), okLabel: "Delete", danger: true });
    if (!ok) return;
    try {
      await api.deleteNote(n.id);
      await load();
    } catch (err) {
      toast(`Delete failed: ${(err as Error).message}`);
    }
  }

  return (
    <Stack spacing={1.5}>
      <Typography variant="h3" component="h3">
        My notes
      </Typography>
      <TextField
        multiline
        minRows={2}
        fullWidth
        label="Add a note"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        slotProps={{ htmlInput: { maxLength: 5000 } }}
      />
      <Box>
        <Button variant="contained" disabled={busy || !draft.trim()} onClick={() => void add()}>
          Save note
        </Button>
      </Box>
      {notes === null ? <Skeleton height={40} /> : null}
      {notes?.length === 0 ? (
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          No notes yet.
        </Typography>
      ) : null}
      {notes?.map((n) => (
        <Card key={n.id} variant="outlined" sx={{ p: 1.5 }}>
          {editing?.id === n.id ? (
            <Stack spacing={1}>
              <TextField multiline minRows={2} fullWidth value={editing.text} onChange={(e) => setEditing({ id: n.id, text: e.target.value })} />
              <Stack direction="row" spacing={1}>
                <Button variant="outlined" color="inherit" onClick={() => void save()} disabled={!editing.text.trim()}>
                  Save
                </Button>
                <Button color="inherit" onClick={() => setEditing(null)}>
                  Cancel
                </Button>
              </Stack>
            </Stack>
          ) : (
            <Stack direction="row" spacing={1} sx={{ alignItems: "flex-start" }}>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                {/* Plain text: React escapes it, so a note can never inject HTML. */}
                <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
                  {n.body}
                </Typography>
                <Typography variant="caption" sx={{ color: "text.secondary" }}>
                  {fmtWhen(n.created_at)}
                  {n.updated_at !== n.created_at ? ` · edited ${fmtWhen(n.updated_at) ?? ""}` : ""}
                </Typography>
              </Box>
              <Tooltip title="Edit">
                <IconButton size="small" aria-label="Edit note" onClick={() => setEditing({ id: n.id, text: n.body })}>
                  <EditOutlined fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete">
                <IconButton size="small" aria-label="Delete note" onClick={() => void remove(n)}>
                  <DeleteOutline fontSize="small" />
                </IconButton>
              </Tooltip>
            </Stack>
          )}
        </Card>
      ))}
    </Stack>
  );
}

function StrategyDialog({
  strategy,
  backtests,
  onClose,
  onNotes,
}: Readonly<{ strategy: Strategy; backtests: BacktestResponse | null; onClose: () => void; onNotes: (id: string, n: number) => void }>) {
  const phone = useMediaQuery((t) => t.breakpoints.down("sm"));
  const min = backtests?.min_trades ?? 20;
  const rows = (backtests?.results ?? []).filter((r) => r.strategy_id === strategy.id && r.coin_group === "all");
  const failures = Object.entries(backtests?.failures[strategy.id] ?? {}).sort((a, b) => b[1] - a[1]);
  return (
    <Dialog open onClose={onClose} fullScreen={phone} fullWidth maxWidth="md" aria-labelledby="stratTitle">
      <DialogTitle id="stratTitle" sx={{ display: "flex", alignItems: "center", gap: 1, pr: 1 }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          {strategy.name}
          <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
            {strategy.family} · fits {strategy.setups.map(humanize).join(", ")}
          </Typography>
        </Box>
        <IconButton aria-label="Close" onClick={onClose}>
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5}>
          <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "minmax(0, 1fr)", md: "minmax(0, 1fr) minmax(0, 1fr)" } }}>
            <StrategyDiagram diagram={strategy.diagram} />
            <Stack spacing={1.5}>
              <Typography variant="body2">{strategy.summary}</Typography>
              <StyleChips styles={strategy.styles} />
              <Rule label="Entry" text={strategy.entry} />
              <Rule label="Stop" text={strategy.stop} />
              <Rule label="Exit" text={strategy.exit} />
            </Stack>
          </Box>
          <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "minmax(0, 1fr)", md: "repeat(3, minmax(0, 1fr))" } }}>
            <Rule label="Works when" text={strategy.works_when} />
            <Rule label="Fails when" text={strategy.fails_when} />
            <Rule label="Worked example" text={strategy.example} />
          </Box>
          <Box>
            <Typography variant="h3" component="h3" sx={{ mb: 1 }}>
              Backtest (Bhalu trades)
            </Typography>
            {!strategy.backtestable ? (
              <Alert severity="info">{strategy.backtest_note ?? "Not back-tested."}</Alert>
            ) : rows.length === 0 ? (
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                No backtest yet. Run one on the Backtests page.
              </Typography>
            ) : (
              <DataTable minWidth={520} maxHeight="none">
                <TableHead>
                  <TableRow>
                    <TableCell>Style</TableCell>
                    <TableCell align="right">Trades</TableCell>
                    <TableCell align="right">Win rate</TableCell>
                    <TableCell align="right">Avg R</TableCell>
                    <TableCell align="right">Total R</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((r) => (
                    <TableRow key={r.style}>
                      <TableCell>{STYLE_LABEL[r.style]}</TableCell>
                      <TableCell align="right">
                        <V value={String(r.trades)} />
                      </TableCell>
                      <TableCell align="right">
                        {r.trades < min ? <Na reason="too few trades" /> : <V value={fmtRate(r.win_rate)} />}
                      </TableCell>
                      <TableCell align="right">
                        <V value={fmtR(r.avg_r)} />
                      </TableCell>
                      <TableCell align="right">
                        <V value={fmtR(r.total_r, 1)} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </DataTable>
            )}
            {failures.length ? (
              <Box sx={{ mt: 1.5 }}>
                <Typography variant="overline" component="div" sx={{ color: "text.secondary" }}>
                  Why losers lost
                </Typography>
                <Stack direction="row" spacing={0.75} useFlexGap sx={{ flexWrap: "wrap" }}>
                  {failures.map(([tag, n]) => (
                    <Pill key={tag} glyph="✕" label={`${tag} · ${String(n)}`} />
                  ))}
                </Stack>
              </Box>
            ) : null}
          </Box>
          <Notes strategyId={strategy.id} onCount={onNotes} />
        </Stack>
      </DialogContent>
    </Dialog>
  );
}

/** The strategy library with diagrams, backtest results and notes (WL-031, WL-032). */
export default function Strategies({ active }: Readonly<{ active: boolean }>) {
  const [strategies, setStrategies] = useState<Strategy[] | null>(null);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [backtests, setBacktests] = useState<BacktestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<Strategy | null>(null);
  const [style, setStyle] = usePref<string>("cca_strategies_style", ""); // WL-101: kept per browser
  const [mockOpen, setMockOpen] = useState(false); // WL-081
  const [mockVersion, setMockVersion] = useState(0);
  const [arenaAgents, setArenaAgents] = useState<ArenaAgent[]>([]);
  useEffect(() => {
    if (!active || arenaAgents.length) return;
    api
      .agents()
      .then((r) => setArenaAgents(r.agents))
      .catch(() => undefined);
  }, [active, arenaAgents]);

  useEffect(() => {
    if (!active) return;
    api
      .strategies()
      .then((r) => {
        setStrategies(r.strategies);
        setCounts(r.note_counts);
        setError(null);
      })
      .catch((err: unknown) => setError((err as Error).message));
    api
      .backtests()
      .then(setBacktests)
      .catch(() => setBacktests(null));
  }, [active]);

  const onNotes = useCallback((id: string, n: number) => setCounts((c) => ({ ...c, [id]: n })), []);

  const shown = useMemo(() => (strategies ?? []).filter((s) => !style || s.styles.includes(style as Strategy["styles"][number])), [strategies, style]);
  const min = backtests?.min_trades ?? 20;

  let body: React.ReactNode;
  if (error) body = <Alert severity="warning">Strategies unavailable: {error}</Alert>;
  else if (!strategies)
    body = (
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(3, 1fr)" } }}>
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} variant="rounded" height={260} />
        ))}
      </Box>
    );
  else if (!shown.length) body = <EmptyState text="No strategy fits this style." />;
  else
    body = (
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "minmax(0, 1fr)", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(3, minmax(0, 1fr))" } }}>
        {shown.map((s) => {
          const best = bestRow(backtests?.results ?? [], s.id, min);
          return (
            <Card key={s.id} sx={{ display: "flex" }}>
              <CardActionArea onClick={() => setOpen(s)} sx={{ p: 2, display: "flex", flexDirection: "column", alignItems: "stretch", gap: 1.25 }}>
                <StrategyDiagram diagram={s.diagram} compact />
                <Box>
                  <Typography variant="h3" component="h3">
                    {s.name}
                  </Typography>
                  <Typography variant="caption" sx={{ color: "text.secondary" }}>
                    {s.family}
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: "text.secondary", flex: 1 }}>
                  {s.summary}
                </Typography>
                <StyleChips styles={s.styles} />
                <Stack direction="row" spacing={1} sx={{ alignItems: "center", justifyContent: "space-between" }}>
                  <Typography variant="caption" sx={{ color: "text.secondary" }}>
                    {!s.backtestable ? (
                      "Not back-tested from candles"
                    ) : best ? (
                      <>
                        Best: {STYLE_LABEL[best.style]} <V value={fmtRate(best.win_rate)} /> over {best.trades} trades
                      </>
                    ) : (
                      <>
                        Win rate <Na reason={backtests?.run ? "too few trades" : "no backtest yet"} />
                      </>
                    )}
                  </Typography>
                  {counts[s.id] ? <Chip size="small" label={`${String(counts[s.id])} notes`} /> : null}
                </Stack>
              </CardActionArea>
            </Card>
          );
        })}
      </Box>
    );

  return (
    <Stack spacing={2}>
      <PageHeader
        title="Strategies"
        subtitle="Well-known strategies with their rules, a diagram, backtested win rates and your own notes. Mock test any strategy or Arena agent on your coins."
        actions={
          <ActionButton icon={<ScienceOutlined />} primary disabled={!strategies} onClick={() => setMockOpen(true)}>
            Mock test
          </ActionButton>
        }
      />
      <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }} role="group" aria-label="Filter by style">
        {[{ key: "", label: "All styles" }, ...STYLES.map((k) => ({ key: k, label: STYLE_LABEL[k] }))].map((f) => (
          <Chip
            key={f.key || "all"}
            label={f.label}
            color={style === f.key ? "primary" : "default"}
            variant={style === f.key ? "filled" : "outlined"}
            aria-pressed={style === f.key}
            onClick={() => setStyle(f.key)}
            sx={{ minHeight: { xs: 40, sm: 32 } }}
          />
        ))}
      </Stack>
      {body}
      <MockSessionsCard
        active={active}
        names={Object.fromEntries([...(strategies ?? []).map((x) => [x.id, x.name]), ...arenaAgents.map((a) => [a.id, a.name])])}
        version={mockVersion}
      />
      {open ? <StrategyDialog strategy={open} backtests={backtests} onClose={() => setOpen(null)} onNotes={onNotes} /> : null}
      {mockOpen && strategies ? (
        <MockTestDialog strategies={strategies} agents={arenaAgents} onClose={() => setMockOpen(false)} onStarted={() => setMockVersion((v) => v + 1)} />
      ) : null}
    </Stack>
  );
}
