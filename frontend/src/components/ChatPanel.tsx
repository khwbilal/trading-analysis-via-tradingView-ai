import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import InputBase from "@mui/material/InputBase";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import ChatBubbleOutlined from "@mui/icons-material/ChatBubbleOutlined";
import Send from "@mui/icons-material/Send";
import { useEffect, useRef, useState, type FormEvent } from "react";
import type { TradeLevels } from "../api";
import { isCall, parseAnalysis } from "../lib/analysis";
import { biasClass, fmtConf, fmtPx, rewardRisk } from "../lib/format";
import AnalysisView from "./AnalysisView";
import { PROVIDER_LABEL } from "../lib/nav";
import { BiasPill, V } from "./ui";

export type UiMessage = {
  id: number;
  role: "user" | "assistant";
  text: string;
  levels?: TradeLevels;
  provider?: string;
  error?: boolean;
  thinking?: boolean;
  quiet?: boolean;
  choices?: string[]; // WL-112: buttons under the message, e.g. the timeframes to analyse
  chosen?: string;
  current?: string; // the choice that is already active, marked
  agents?: { id: string; name: string; note?: string }[]; // WL-131: Think like buttons, top Arena scorer first
  agent?: string; // the agent picked, marked
};

export type ChoiceKind = "timeframe" | "agent";

const SUGGESTIONS = [
  "Is this a long setup?",
  "Where is the invalidation?",
  "What would flip the bias?",
  "Summarise the risk",
];

const OVERRIDE = "DESK OVERRIDE:";

/**
 * Model output stays plain text: React escapes it, and only the leading `KEY:` of each line is
 * bolded. The DESK OVERRIDE line (the guards changed the analyst's bias) gets its own callout.
 */
export function AnalysisText({ text }: Readonly<{ text: string }>) {
  if (typeof text !== "string") return <PlainText text={String(text ?? "")} />;
  const parsed = parseAnalysis(text); // WL-114: a call with levels or an explanation renders as boxes
  if (isCall(parsed)) return <AnalysisView p={parsed} />;
  return <PlainText text={text} />;
}

function PlainText({ text }: Readonly<{ text: string }>) {
  const lines = text.split("\n");
  return (
    <>
      {lines.map((line, i) => {
        const key = `${String(i)}-${line.slice(0, 12)}`;
        const nl = i < lines.length - 1 ? "\n" : null;
        if (line.startsWith(OVERRIDE)) {
          return (
            <Box
              key={key}
              component="span"
              sx={{
                display: "block",
                bgcolor: "surface.warn",
                color: "text.primary",
                borderLeft: 3,
                borderColor: "warning.main",
                borderRadius: 1,
                px: 1,
                py: 0.5,
                my: 0.5,
              }}
            >
              <Box component="span" aria-hidden sx={{ color: "warning.main", fontWeight: 700, mr: 0.5 }}>
                !
              </Box>
              <strong>{OVERRIDE}</strong>
              {line.slice(OVERRIDE.length)}
            </Box>
          );
        }
        const m = /^([A-Z][A-Z0-9/:&' ]{1,18}):(.*)$/.exec(line);
        return (
          <span key={key}>
            {m ? (
              <>
                <strong>{m[1]}:</strong>
                {m[2]}
              </>
            ) : (
              line
            )}
            {nl}
          </span>
        );
      })}
    </>
  );
}

function TradeCard({ levels }: Readonly<{ levels: TradeLevels }>) {
  const rr = rewardRisk(levels.entry, levels.stop_loss, levels.take_profit);
  const cls = biasClass(levels.bias);
  let edge = "divider";
  if (cls === "buy") edge = "success.main";
  else if (cls === "sell") edge = "error.main";
  const cells: [string, string | null][] = [
    ["Entry", fmtPx(levels.entry)],
    ["Stop", fmtPx(levels.stop_loss)],
    ["Target", fmtPx(levels.take_profit)],
    ["Support", fmtPx(levels.support)],
    ["Resistance", fmtPx(levels.resistance)],
    ["R : R", rr === null ? null : `${rr.toFixed(1)} : 1`],
  ];
  return (
    <Box sx={{ border: 1, borderColor: "divider", borderLeft: 3, borderLeftColor: edge, borderRadius: 1, p: 1.25, mb: 1, bgcolor: "background.paper" }}>
      <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between", mb: 1 }}>
        <BiasPill bias={levels.bias} />
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          Confidence <V value={fmtConf(levels.confidence)} />
        </Typography>
      </Stack>
      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 1 }}>
        {cells.map(([label, value]) => (
          <Box key={label} sx={{ minWidth: 0 }}>
            <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
              {label}
            </Typography>
            <Box sx={{ fontWeight: 600, fontSize: "0.8125rem", overflow: "hidden", textOverflow: "ellipsis" }}>
              <V value={value} />
            </Box>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

function Choices({ m, onChoose }: Readonly<{ m: UiMessage; onChoose?: (id: number, value: string, kind: ChoiceKind) => void }>) {
  const agentName = m.agents?.find((a) => a.id === m.agent)?.name;
  if (m.chosen)
    return (
      <Typography variant="caption" sx={{ color: "text.secondary", mt: 0.5 }}>
        Picked {m.chosen}
        {agentName ? `, thinking like ${agentName}` : ""}
      </Typography>
    );
  return (
    <>
      {m.agents?.length ? (
        <>
          <Typography variant="caption" sx={{ color: "text.secondary", mt: 1 }}>
            Think like (top Arena scorer first)
          </Typography>
          <Stack direction="row" useFlexGap spacing={0.75} sx={{ flexWrap: "wrap", mt: 0.5 }} role="group" aria-label="Think like">
            {m.agents.map((a) => (
              <Chip
                key={a.id}
                size="small"
                label={a.name}
                title={a.note}
                variant={a.id === m.agent ? "filled" : "outlined"}
                color={a.id === m.agent ? "primary" : "default"}
                aria-pressed={a.id === m.agent}
                onClick={() => onChoose?.(m.id, a.id, "agent")}
              />
            ))}
          </Stack>
          <Typography variant="caption" sx={{ color: "text.secondary", mt: 1 }}>
            Timeframe (runs the analysis)
          </Typography>
        </>
      ) : null}
    <Stack direction="row" useFlexGap spacing={0.75} sx={{ flexWrap: "wrap", mt: m.agents?.length ? 0.5 : 1 }} role="group" aria-label="Timeframe">
      {m.choices?.map((c) => (
        <Button
          key={c}
          size="small"
          variant="outlined"
          color={c === m.current ? "primary" : "inherit"}
          aria-current={c === m.current ? "true" : undefined}
          sx={{ minWidth: 48, fontFamily: "monospace", borderColor: c === m.current ? "primary.main" : "divider", fontWeight: c === m.current ? 700 : 400 }}
          onClick={() => onChoose?.(m.id, c, "timeframe")}
        >
          {c}
        </Button>
      ))}
    </Stack>
    </>
  );
}

function Message({ m, onChoose }: Readonly<{ m: UiMessage; onChoose?: (id: number, value: string, kind: ChoiceKind) => void }>) {
  const user = m.role === "user";
  let who = "Analyst";
  if (user) who = "You";
  else if (m.provider) who = `Analyst · ${PROVIDER_LABEL[m.provider] ?? m.provider}`;
  let bg = "surface.paper2";
  let color = "text.primary";
  if (user) {
    bg = "primary.main";
    color = "primary.contrastText";
  } else if (m.error) {
    bg = "surface.crit";
  }
  return (
    <Stack sx={{ alignItems: user ? "flex-end" : "flex-start", mb: 1.5 }}>
      {m.quiet ? null : (
        <Typography variant="caption" sx={{ color: "text.secondary", mb: 0.5, fontWeight: 600 }}>
          {who}
        </Typography>
      )}
      {m.levels ? (
        <Box sx={{ width: "100%" }}>
          <TradeCard levels={m.levels} />
        </Box>
      ) : null}
      <Box
        sx={{
          bgcolor: m.quiet ? "transparent" : bg,
          color: m.quiet ? "text.secondary" : color,
          border: m.error ? 1 : 0,
          borderColor: "error.main",
          px: m.quiet ? 0 : 1.5,
          py: m.quiet ? 0 : 1,
          borderRadius: 1.5,
          maxWidth: user ? "85%" : "100%",
          whiteSpace: "pre-wrap",
          overflowWrap: "anywhere",
          typography: "body2",
          fontStyle: m.quiet ? "italic" : "normal",
        }}
      >
        {m.thinking ? (
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <Box
              component="span"
              aria-hidden
              sx={{
                display: "inline-flex",
                gap: 0.5,
                "& i": {
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  bgcolor: "text.secondary",
                  animation: "ccaPulse 1.2s infinite ease-in-out",
                },
                "& i:nth-of-type(2)": { animationDelay: "0.15s" },
                "& i:nth-of-type(3)": { animationDelay: "0.3s" },
                "@keyframes ccaPulse": { "0%, 80%, 100%": { opacity: 0.25 }, "40%": { opacity: 1 } },
              }}
            >
              <i />
              <i />
              <i />
            </Box>
            <span>{m.text}</span>
          </Stack>
        ) : m.role === "assistant" ? (
          <AnalysisText text={m.text} />
        ) : (
          m.text
        )}
      </Box>
      {m.choices ? <Choices m={m} onChoose={onChoose} /> : null}
    </Stack>
  );
}

export default function ChatPanel({
  symbol,
  messages,
  busy,
  onSend,
  onClear,
  onChoose,
}: Readonly<{
  symbol: string;
  messages: UiMessage[];
  busy: boolean;
  onSend: (text: string) => void;
  onClear: () => void;
  onChoose?: (id: number, value: string, kind: ChoiceKind) => void;
}>) {
  const [input, setInput] = useState("");
  const logRef = useRef<HTMLOutputElement>(null);

  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  function submit(e?: FormEvent) {
    e?.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    onSend(text);
  }

  return (
    <Card
      component="aside"
      aria-label="AI analyst chat"
      sx={{
        display: "flex",
        flexDirection: "column",
        minWidth: 0,
        height: { xs: 620, lg: "calc(100vh - 52px - 48px)" },
        position: { lg: "sticky" },
        top: { lg: 76 },
      }}
    >
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", px: 2, minHeight: 48, borderBottom: 1, borderColor: "divider" }}>
        <ChatBubbleOutlined sx={{ fontSize: 18, color: "text.secondary" }} />
        <Typography variant="h3" component="h3" sx={{ flex: 1 }}>
          Analyst
        </Typography>
        <Button size="small" color="inherit" onClick={onClear}>
          Clear
        </Button>
      </Stack>
      <Box component="output" aria-live="polite" ref={logRef} sx={{ display: "block", flex: 1, overflowY: "auto", p: 2 }}>
        {messages.map((m) => (
          <Message key={m.id} m={m} onChoose={onChoose} />
        ))}
      </Box>
      <Box component="form" onSubmit={submit} sx={{ p: 1.5, borderTop: 1, borderColor: "divider" }}>
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75, mb: 1 }}>
          {SUGGESTIONS.map((s) => (
            <Chip key={s} size="small" variant="outlined" label={s} disabled={busy} onClick={() => onSend(s)} sx={{ fontWeight: 500 }} />
          ))}
        </Box>
        <Stack
          direction="row"
         
          spacing={1}
          sx={{ alignItems: "flex-end", border: 1, borderColor: "divider", borderRadius: 1.5, pl: 1.5, pr: 0.5, py: 0.5, "&:focus-within": { borderColor: "primary.main" } }}
        >
          <InputBase
            multiline
            maxRows={6}
            placeholder={`Ask about ${symbol}…`}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) submit(e);
            }}
            sx={{ flex: 1, py: 0.75, typography: "body2" }}
            inputProps={{ "aria-label": `Ask about ${symbol}` }}
          />
          <IconButton type="submit" color="primary" aria-label="Send" disabled={busy}>
            <Send fontSize="small" />
          </IconButton>
        </Stack>
      </Box>
    </Card>
  );
}
