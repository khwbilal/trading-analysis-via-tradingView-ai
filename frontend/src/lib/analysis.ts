/**
 * WL-114: split an analysis text into parts that render as boxes: the plan levels, the TP ladder,
 * labelled rows, explanation points and the strategy line. Pure text in, pure text out: the model's
 * words are never turned into markup.
 */

export type Cell = { label: string; value: string; note: string };
export type Row = { label: string; text: string };
export type ParsedAnalysis = {
  title: string;
  source: string;
  override: string;
  levels: Cell[];
  ladder: Cell[];
  rows: Row[];
  points: Row[];
  strategy: string;
  rest: string[];
};

const LEVEL_KEY =
  /^(cmp|price|entry|safest entry.*|breakout entry|retest entry|stop|sl|stop loss|target|tp\d?|final tp|support|resistance|ema20\/50|r\s*:\s*r|confidence)$/i;
const NUMBERISH = /^([≈~]?-?\d[\d.,]*(?:\s*(?:–|-|\/|to)\s*-?\d[\d.,]*)?%?(?:\s*:\s*1)?)(.*)$/;
const KEY_VALUE = /^([A-Za-z][\w /+().'&-]{0,34}?)\s*:\s*(.*)$/;
const RR = /^(R\s*:\s*R)\s*:?\s*(.*)$/i;

export function emptyAnalysis(): ParsedAnalysis {
  return { title: "", source: "", override: "", levels: [], ladder: [], rows: [], points: [], strategy: "", rest: [] };
}

/** "170.8 to 172.9 (short) on a close" -> value "170.8 to 172.9", note "(short) on a close". */
function splitValue(value: string): { value: string; note: string } {
  const m = NUMBERISH.exec(value.trim());
  return m ? { value: m[1].trim(), note: m[2].replace(/^[\s,;.]+/, "").trim() } : { value: "", note: value.trim() };
}

function keyValue(line: string): Row | null {
  const rr = RR.exec(line);
  if (rr) return { label: "R:R", text: rr[2].trim() };
  const m = KEY_VALUE.exec(line);
  return m ? { label: m[1].trim(), text: m[2].trim() } : null;
}

export function hasStructure(p: ParsedAnalysis): boolean {
  return p.levels.length + p.ladder.length + p.rows.length + p.points.length > 0;
}

/** A trade call, not a chat answer that happens to hold a "Key:" line: it has levels or an explanation. */
export function isCall(p: ParsedAnalysis): boolean {
  return p.levels.length + p.ladder.length + p.points.length > 0;
}

export function parseAnalysis(text: string): ParsedAnalysis {
  const p = emptyAnalysis();
  let section: "main" | "explain" | "plan" = "main";
  let last: { kind: "cell"; cell: Cell } | { kind: "row"; row: Row } | null = null;

  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line || /^[-=_–—]{4,}$/.test(line)) continue;

    if (line.startsWith("DESK OVERRIDE:")) {
      p.override = line.slice("DESK OVERRIDE:".length).trim();
      continue;
    }
    if (/^source\s*:/i.test(line)) {
      p.source = line.replace(/^source\s*:\s*/i, "");
      continue;
    }
    if (/^(explanation|why)\s*:?\s*$/i.test(line)) {
      section = "explain";
      last = null;
      continue;
    }
    if (/^plan\s*:?\s*$/i.test(line)) {
      section = "plan";
      last = null;
      continue;
    }
    if (/^strategy\s*:/i.test(line)) {
      p.strategy = line.replace(/^strategy\s*:\s*/i, "");
      continue;
    }

    // An indented line carries on the item above it, e.g. the "(A) 183.4" options under "SL :".
    if (/^\s/.test(raw) && last) {
      if (last.kind === "cell") {
        const sv = splitValue(line.replace(/^\([A-Z]\)\s*/, ""));
        if (!last.cell.value && sv.value) last.cell.value = sv.value;
        last.cell.note = [last.cell.note, line].filter(Boolean).join("\n");
      } else {
        last.row.text = [last.row.text, line].filter(Boolean).join("\n");
      }
      continue;
    }

    if (section === "explain") {
      const bullet = line.replace(/^[-•*]\s*/, "");
      p.points.push(keyValue(bullet) ?? { label: "", text: bullet });
      continue;
    }
    if (section === "plan") {
      p.rest.push(line);
      continue;
    }

    const tps = [...line.matchAll(/\b(TP\d)\s*:?\s*([≈~]?\d[\d.,]*)/g)];
    if (tps.length > 1 && /^TP\d/i.test(line)) {
      for (const m of tps) p.ladder.push({ label: m[1], value: m[2], note: "" });
      last = null;
      continue;
    }

    // "BINANCE:SOLUSDT · 1h" heads the classic card; it is a title, not a key.
    if (!p.title && /^[A-Z0-9]+:[A-Z0-9.]+\s*·/.test(line)) {
      p.title = line;
      continue;
    }

    const kv = keyValue(line);
    if (kv) {
      const sv = splitValue(kv.text);
      if (LEVEL_KEY.test(kv.label) && (sv.value || !kv.text)) {
        const cell = { label: kv.label, value: sv.value, note: sv.note };
        p.levels.push(cell);
        last = { kind: "cell", cell };
      } else {
        const row = { label: kv.label, text: kv.text };
        p.rows.push(row);
        last = { kind: "row", row };
      }
      continue;
    }

    if (!p.title && !hasStructure(p)) p.title = line;
    else p.rest.push(line);
    last = null;
  }
  return p;
}

const PART_LABEL: Record<string, string> = {
  mtf: "Timeframes",
  momentum: "Momentum",
  structure: "Structure",
  flow: "Flow",
  regime: "Regime",
  orderbook: "Order book",
  liquidity: "Liquidity",
};

/**
 * The notes stored on signals from before WL-107: "summary | setup -- detail | Buy (+2.92) · setup=x ·
 * mtf=+0.0, momentum=+1.9, ...". Split into rows and one cell per confluence part.
 */
export function parseNotes(notes: string): ParsedAnalysis {
  const p = emptyAnalysis();
  for (const part of notes.split(" | ").map((s) => s.trim()).filter(Boolean)) {
    if (part.includes("setup=") || /=[+-]?\d/.test(part)) {
      for (const bit of part.split(" · ").map((s) => s.trim())) {
        if (bit.startsWith("setup=")) p.rows.push({ label: "Setup", text: bit.slice(6).replaceAll("_", " ") });
        else if (/=[+-]?\d/.test(bit)) {
          for (const kv of bit.split(",")) {
            const [k, v] = kv.split("=").map((s) => s.trim());
            if (k && v) p.levels.push({ label: PART_LABEL[k] ?? k, value: v, note: "" });
          }
        } else if (bit) p.rows.push({ label: "Score", text: bit });
      }
    } else if (part.includes(" -- ")) {
      const [setup, detail] = part.split(" -- ");
      p.rows.push({ label: "Setup read", text: `${setup.trim()}: ${detail.trim()}` });
    } else if (p.rows.length === 0 && !p.title) {
      p.rows.push({ label: "Call", text: part });
    } else {
      p.rest.push(part);
    }
  }
  return p;
}

/** The numbers in a level's value: "170.8 to 172.9" gives [170.8, 172.9]; thousands commas are dropped. */
export function numbersIn(value: string): number[] {
  return [...value.replaceAll(",", "").matchAll(/-?\d+(?:\.\d+)?/g)].map((m) => Number(m[0])).filter((x) => Number.isFinite(x));
}

export type ChartMarks = {
  zone: [number, number] | null; // the entry zone, low to high
  tps: { label: string; price: number }[];
  finalTp: number | null;
  pattern: string;
};

/** WL-106: what a stored analysis draws on its chart: entry zone, TP ladder, final TP and the pattern. */
export function chartMarks(p: ParsedAnalysis): ChartMarks {
  let zone: [number, number] | null = null;
  let finalTp: number | null = null;
  for (const c of p.levels) {
    const nums = numbersIn(c.value);
    if (!nums.length) continue;
    if (/final tp/i.test(c.label)) finalTp = nums[0];
    else if (!zone && /entry/i.test(c.label) && !/breakout/i.test(c.label) && nums.length >= 2) {
      zone = [Math.min(nums[0], nums[1]), Math.max(nums[0], nums[1])];
    }
  }
  const tps = p.ladder.flatMap((c) => {
    const n = numbersIn(c.value);
    return n.length ? [{ label: c.label, price: n[0] }] : [];
  });
  const pat = p.points.find((r) => /^pattern/i.test(r.label));
  return { zone, tps, finalTp, pattern: pat ? pat.text : "" };
}
