import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import Chip from "@mui/material/Chip";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormGroup from "@mui/material/FormGroup";
import FormLabel from "@mui/material/FormLabel";
import IconButton from "@mui/material/IconButton";
import Radio from "@mui/material/Radio";
import RadioGroup from "@mui/material/RadioGroup";
import Slider from "@mui/material/Slider";
import Stack from "@mui/material/Stack";
import Step from "@mui/material/Step";
import StepButton from "@mui/material/StepButton";
import Stepper from "@mui/material/Stepper";
import Switch from "@mui/material/Switch";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import Close from "@mui/icons-material/Close";
import PlayArrow from "@mui/icons-material/PlayArrow";
import { useMemo, useState } from "react";
import type { ArenaAgent, BacktestChoices, BacktestOptions, Strategy, Style } from "../api";
import { GROUP_LABEL, STYLE_LABEL } from "../lib/format";

const STEPS = ["Coins", "Strategies", "Styles and depth", "Review"] as const;
const ALL_STYLES: Style[] = ["scalp", "day", "swing", "position", "hold"];

type Draft = {
  strategies: string[];
  styles: Style[];
  groups: string[];
  depth: "quick" | "deep";
  bars: number;
  any_style: boolean;
  coins: "fixed" | "random" | "custom";
  random_count: number;
  seed: string;
  symbols: string; // WL-074: your own coins, as typed
  agents: string[]; // WL-074: Arena agents to run on the same setup
};

/** Your coins as typed: comma or space separated; the server cleans them (BINANCE:SOLUSDT.P, sol, TSLAUSDT). */
function symbolList(text: string): string[] {
  return text
    .split(/[\s,]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function presetDraft(preset: "quick" | "deep" | "random", strategies: string[], choices: BacktestChoices): Draft {
  const fixedGroups = Object.keys(choices.groups);
  const base: Draft = {
    strategies,
    styles: [...ALL_STYLES],
    groups: fixedGroups,
    depth: "quick",
    bars: choices.depths.deep?.bars ?? 5000,
    any_style: false,
    coins: "fixed",
    random_count: 4,
    seed: "",
    symbols: "",
    agents: [],
  };
  if (preset === "deep") return { ...base, depth: "deep", any_style: true };
  if (preset === "random") return { ...base, depth: "deep", any_style: true, coins: "random", groups: [...choices.tiers], random_count: 6 };
  return base;
}

function toggle<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((x) => x !== item) : [...list, item];
}

/** Rough trade count: about one trade per 48 candles per strategy, coin and style (measured on the WL-054 deep run). */
function estimate(d: Draft, choices: BacktestChoices, strategies: Strategy[]): number {
  const own = symbolList(d.symbols).length;
  let coins = own;
  if (d.coins === "random") coins += d.groups.reduce((n, g) => n + (g === "major" ? Math.min(2, d.random_count) : d.random_count), 0);
  else if (d.coins === "fixed") coins += d.groups.reduce((n, g) => n + (g === "lowcap" || g === "stock" ? 4 : g === "commodity" ? 6 : (choices.groups[g]?.length ?? 0)), 0);
  const bars = d.depth === "deep" ? d.bars : 1000;
  let cells = 0;
  for (const s of strategies) {
    if (!d.strategies.includes(s.id)) continue;
    cells += d.styles.filter((st) => d.any_style || s.styles.includes(st)).length;
  }
  return Math.round((cells * coins * Math.max(bars - 300, 0)) / 48);
}

/** The backtest setup wizard (WL-055, WL-057): coins, strategies, styles and depth, then review and start. */
export default function BacktestWizard({
  choices,
  strategies,
  agents = [],
  onClose,
  onStart,
}: Readonly<{
  choices: BacktestChoices;
  strategies: Strategy[];
  agents?: ArenaAgent[];
  onClose: () => void;
  onStart: (options: BacktestOptions) => Promise<void>;
}>) {
  const phone = useMediaQuery((t) => t.breakpoints.down("sm"));
  const testable = useMemo(() => strategies.filter((s) => s.backtestable), [strategies]);
  const allIds = useMemo(() => testable.map((s) => s.id), [testable]);
  const [step, setStep] = useState(0);
  const [d, setD] = useState<Draft>(() => presetDraft("quick", allIds, choices));
  const [busy, setBusy] = useState(false);
  const families = useMemo(() => {
    const m = new Map<string, Strategy[]>();
    for (const s of testable) m.set(s.family, [...(m.get(s.family) ?? []), s]);
    return [...m.entries()];
  }, [testable]);

  const groupsOffered = d.coins === "random" ? choices.tiers : Object.keys(choices.groups);
  const own = symbolList(d.symbols);
  const problems = [
    d.strategies.length || d.agents.length ? null : "Choose at least one strategy or agent.",
    d.styles.length ? null : "Choose at least one style.",
    d.coins === "custom" || d.groups.length || own.length ? null : "Choose at least one coin group.",
    d.coins !== "custom" || own.length ? null : "Type at least one coin for Your coins only.",
  ].filter(Boolean) as string[];
  const trades = estimate(d, choices, testable);

  function set<K extends keyof Draft>(key: K, value: Draft[K]) {
    setD((prev) => ({ ...prev, [key]: value }));
  }

  async function start() {
    setBusy(true);
    try {
      const seed = d.seed.trim() === "" ? null : Number(d.seed);
      await onStart({
        strategies: d.strategies.length === allIds.length ? [] : d.strategies,
        styles: d.styles,
        groups: d.coins === "custom" ? [] : d.groups,
        depth: d.depth,
        bars: d.depth === "deep" ? d.bars : null,
        any_style: d.any_style,
        coins: d.coins,
        random_count: d.coins === "random" ? d.random_count : null,
        seed: seed !== null && Number.isFinite(seed) ? seed : null,
        symbols: own,
        agents: d.agents,
      });
      onClose();
    } finally {
      setBusy(false);
    }
  }

  const presets: { id: "quick" | "deep" | "random"; label: string; note: string }[] = [
    { id: "quick", label: "Daily quick", note: "The 15:45 run: 1,000 candles per coin, every trade kept" },
    { id: "deep", label: "Deep, every strategy", note: "5,000 candles per pair, every trade, all styles" },
    { id: "random", label: "Random coins, every tier", note: "6 random coins per tier, good coins to shit coins" },
  ];

  return (
    <Dialog open onClose={onClose} fullScreen={phone} fullWidth maxWidth="md" aria-labelledby="wizTitle">
      <DialogTitle id="wizTitle" sx={{ display: "flex", alignItems: "center", gap: 1, pr: 1 }}>
        <Box sx={{ flex: 1 }}>New backtest</Box>
        <IconButton aria-label="Close" onClick={onClose}>
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Stepper nonLinear activeStep={step} alternativeLabel={!phone} orientation="horizontal" sx={{ mb: 3, flexWrap: "wrap" }}>
          {STEPS.map((label, i) => (
            <Step key={label} completed={i < step}>
              <StepButton onClick={() => setStep(i)}>{phone && i !== step ? "" : label}</StepButton>
            </Step>
          ))}
        </Stepper>

        {step === 0 ? (
          <Stack spacing={3}>
            <Box>
              <FormLabel component="legend" sx={{ mb: 1 }}>
                Start from a preset
              </FormLabel>
              <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                {presets.map((p) => (
                  <Chip
                    key={p.id}
                    label={p.label}
                    title={p.note}
                    variant="outlined"
                    onClick={() => setD(presetDraft(p.id, allIds, choices))}
                    sx={{ minHeight: { xs: 40, sm: 32 } }}
                  />
                ))}
              </Stack>
            </Box>
            <Box>
              <FormLabel component="legend">Coins</FormLabel>
              <RadioGroup
                value={d.coins}
                onChange={(e) => {
                  const coins = e.target.value as Draft["coins"];
                  setD((prev) => ({ ...prev, coins, groups: coins === "random" ? [...choices.tiers] : coins === "custom" ? [] : Object.keys(choices.groups) }));
                }}
              >
                <FormControlLabel
                  value="fixed"
                  control={<Radio />}
                  label={
                    <span>
                      Fixed list{" "}
                      <Typography component="span" variant="caption" sx={{ color: "text.secondary" }}>
                        BTC, ETH, large caps, memes and 4 low caps picked by volume
                      </Typography>
                    </span>
                  }
                />
                <FormControlLabel
                  value="random"
                  control={<Radio />}
                  label={
                    <span>
                      Random coins per tier{" "}
                      <Typography component="span" variant="caption" sx={{ color: "text.secondary" }}>
                        liquid Binance USDT pairs drawn at random, from good coins to shit coins
                      </Typography>
                    </span>
                  }
                />
                <FormControlLabel
                  value="custom"
                  control={<Radio />}
                  label={
                    <span>
                      Your coins only{" "}
                      <Typography component="span" variant="caption" sx={{ color: "text.secondary" }}>
                        just the coins and stock perps you type below
                      </Typography>
                    </span>
                  }
                />
              </RadioGroup>
            </Box>
            <TextField
              label="Your coins"
              size="small"
              value={d.symbols}
              onChange={(e) => set("symbols", e.target.value)}
              placeholder="SOL, PEPEUSDT, TSLAUSDT, BINANCE:WIFUSDT.P"
              helperText={
                own.length
                  ? `${String(own.length)} coin${own.length === 1 ? "" : "s"}, tested as the group "Your coins"${d.coins === "custom" ? "" : " on top of the groups"}. Up to 40.`
                  : "Optional: any Binance coins, stock or commodity perps (XAUUSDT, CLUSDT), comma or space separated"
              }
            />
            <Box sx={{ display: d.coins === "custom" ? "none" : "block" }}>
              <FormLabel component="legend">{d.coins === "random" ? "Tiers" : "Coin groups"}</FormLabel>
              <FormGroup row>
                {groupsOffered.map((g) => (
                  <FormControlLabel
                    key={g}
                    control={<Checkbox checked={d.groups.includes(g)} onChange={() => set("groups", toggle(d.groups, g))} />}
                    label={
                      <span title={d.coins === "fixed" ? choices.groups[g]?.join(", ") || "Picked at run time" : undefined}>
                        {GROUP_LABEL[g] ?? g}
                      </span>
                    }
                  />
                ))}
              </FormGroup>
            </Box>
            {d.coins === "random" ? (
              <Stack direction={{ xs: "column", sm: "row" }} spacing={3} sx={{ alignItems: { sm: "center" } }}>
                <Box sx={{ flex: 1, px: 1 }}>
                  <Typography variant="body2" gutterBottom>
                    Coins per tier: {d.random_count}
                  </Typography>
                  <Slider
                    value={d.random_count}
                    min={1}
                    max={choices.max_random_per_tier}
                    step={1}
                    marks
                    onChange={(_, v) => set("random_count", v as number)}
                    aria-label="Coins per tier"
                  />
                </Box>
                <TextField
                  label="Seed"
                  size="small"
                  value={d.seed}
                  onChange={(e) => set("seed", e.target.value.replace(/\D/g, ""))}
                  helperText="Empty draws new coins; a number repeats a draw"
                  sx={{ width: { xs: "100%", sm: 220 } }}
                />
              </Stack>
            ) : null}
          </Stack>
        ) : null}

        {step === 1 ? (
          <Stack spacing={2}>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
              <Typography variant="body2" sx={{ flex: 1 }}>
                {d.strategies.length} of {allIds.length} strategies
              </Typography>
              <Button size="small" onClick={() => set("strategies", allIds)}>
                All
              </Button>
              <Button size="small" onClick={() => set("strategies", [])}>
                None
              </Button>
            </Stack>
            {agents.length ? (
              <Box>
                <FormLabel component="legend">Arena agents (also starts an Arena run on these coins)</FormLabel>
                <FormGroup row>
                  {agents.map((a) => (
                    <FormControlLabel
                      key={a.id}
                      control={<Checkbox checked={d.agents.includes(a.id)} onChange={() => set("agents", toggle(d.agents, a.id))} />}
                      label={a.name}
                    />
                  ))}
                </FormGroup>
              </Box>
            ) : null}
            {families.map(([family, list]) => (
              <Box key={family}>
                <FormLabel component="legend">{family}</FormLabel>
                <FormGroup>
                  {list.map((s) => (
                    <FormControlLabel
                      key={s.id}
                      control={<Checkbox checked={d.strategies.includes(s.id)} onChange={() => set("strategies", toggle(d.strategies, s.id))} />}
                      label={
                        <span>
                          {s.name}{" "}
                          <Typography component="span" variant="caption" sx={{ color: "text.secondary" }}>
                            {s.styles.map((st) => STYLE_LABEL[st]).join(", ")}
                          </Typography>
                        </span>
                      }
                    />
                  ))}
                </FormGroup>
              </Box>
            ))}
          </Stack>
        ) : null}

        {step === 2 ? (
          <Stack spacing={3}>
            <Box>
              <FormLabel component="legend">Styles</FormLabel>
              <FormGroup row>
                {ALL_STYLES.map((st) => (
                  <FormControlLabel
                    key={st}
                    control={<Checkbox checked={d.styles.includes(st)} onChange={() => set("styles", toggle(d.styles, st))} />}
                    label={`${STYLE_LABEL[st]} (${String(choices.styles[st]?.interval ?? "")})`}
                  />
                ))}
              </FormGroup>
              <FormControlLabel
                control={<Switch checked={d.any_style} onChange={(e) => set("any_style", e.target.checked)} />}
                label="Test every strategy in every chosen style, not only the styles it lists"
              />
            </Box>
            <Box>
              <FormLabel component="legend">Depth</FormLabel>
              <RadioGroup value={d.depth} onChange={(e) => set("depth", e.target.value as Draft["depth"])}>
                <FormControlLabel value="quick" control={<Radio />} label="Quick: the newest 1,000 candles, every trade kept" />
                <FormControlLabel value="deep" control={<Radio />} label="Deep: page back through Binance history and keep every trade" />
              </RadioGroup>
            </Box>
            {d.depth === "deep" ? (
              <Box sx={{ px: 1 }}>
                <Typography variant="body2" gutterBottom>
                  Candles per pair: {d.bars.toLocaleString()} (scalping {Math.round((d.bars * 15) / 1440)} days, day trading{" "}
                  {Math.round(d.bars / 24)} days, swing {Math.round((d.bars * 4) / 24)} days)
                </Typography>
                <Slider
                  value={d.bars}
                  min={1000}
                  max={choices.max_bars}
                  step={1000}
                  marks
                  onChange={(_, v) => set("bars", v as number)}
                  aria-label="Candles per pair"
                />
              </Box>
            ) : null}
          </Stack>
        ) : null}

        {step === 3 ? (
          <Stack spacing={1.5}>
            {problems.map((p) => (
              <Alert key={p} severity="warning">
                {p}
              </Alert>
            ))}
            <Review
              label="Coins"
              value={
                d.coins === "custom"
                  ? "Your coins only"
                  : d.coins === "random"
                    ? `Random, ${String(d.random_count)} per tier${d.seed ? `, seed ${d.seed}` : ""}`
                    : "Fixed list"
              }
            />
            {d.coins === "custom" ? null : (
              <Review label={d.coins === "random" ? "Tiers" : "Groups"} value={d.groups.map((g) => GROUP_LABEL[g] ?? g).join(", ")} />
            )}
            {own.length ? <Review label="Your coins" value={own.join(", ")} /> : null}
            {d.agents.length ? (
              <Review label="Arena agents" value={d.agents.map((id) => agents.find((a) => a.id === id)?.name ?? id).join(", ")} />
            ) : null}
            <Review label="Strategies" value={d.strategies.length === allIds.length ? `All ${String(allIds.length)}` : String(d.strategies.length)} />
            <Review label="Styles" value={d.styles.map((s) => STYLE_LABEL[s]).join(", ") + (d.any_style ? ", every strategy in each" : ", listed styles only")} />
            <Review label="Depth" value={d.depth === "deep" ? `Deep, ${d.bars.toLocaleString()} candles per pair, every trade` : "Quick"} />
            <Review label="Expected trades" value={`about ${trades.toLocaleString()}`} />
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              No AI is called. A deep run fetches history first; 14 coins at 5,000 candles took about 80 seconds. Every run and every trade is
              kept.
            </Typography>
          </Stack>
        ) : null}
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={step === 0 ? onClose : () => setStep(step - 1)} color="inherit">
          {step === 0 ? "Cancel" : "Back"}
        </Button>
        {step < STEPS.length - 1 ? (
          <Button variant="contained" onClick={() => setStep(step + 1)}>
            Next
          </Button>
        ) : (
          <Button variant="contained" startIcon={<PlayArrow />} disabled={busy || problems.length > 0} onClick={() => void start()}>
            {busy ? "Starting…" : "Start backtest"}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}

function Review({ label, value }: Readonly<{ label: string; value: string }>) {
  return (
    <Stack direction={{ xs: "column", sm: "row" }} spacing={{ xs: 0, sm: 2 }}>
      <Typography variant="body2" sx={{ color: "text.secondary", width: { sm: 160 }, flexShrink: 0 }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 600 }}>
        {value}
      </Typography>
    </Stack>
  );
}
