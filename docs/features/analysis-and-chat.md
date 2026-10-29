# Analysis & chat

The Desk page has two ways to ask the AI: **Full analysis** gives a structured trade plan, and the **Analyst** chat answers follow-up questions.

## Think like an agent (WL-070)

**UI:** Desk → **Think like** (next to Full analysis; remembered in this browser) · **API:** `agent` on `/api/analyze` and `/api/chat`, the list from `GET /api/agents`.

The [Arena](arena.md) agents can drive the analysis. **Chillar g** (the default) is the current system: the prompt is exactly as before. Any other agent adds its playbook to the prompt:

- **Nadeem Gujjar:** his [v4.8](../reference/gujjar-v4.8.md) gate (RULE-000), RULE-007 entries, the timeframe stack for the desk timeframe (15m scalp, 1h and 4h day trading, 1D swing, 1W and 1M position) and his RULE-013-P layout: CMP, Safest Entry and Breakout Entry ranges on a completed close, SL (A) and (D), TP1 to TP4, R:R at TP3, A+ score, Confirm, Invalid, then the Explanation with citations. The desk shows his card as written (only the JSON block is removed); the JSON still gives entry (middle of the safest range), stop (A) and TP3.
- **Sheryar, Khuzaima, Khawaja Bilal, Turtle, Range trader:** their Arena rules and lean (bull, short only, or both sides). A bear with no short available says no trade.
- **G.O.A.T.:** the three best Arena agents for the timeframe's style right now (15m scalp, 1h day, 4h and 1D swing) with their records and rules; it applies the leader's rules and needs another agent to agree.

The guards still decide the plan's bias ([decision 0003](../decisions/0003-guards-decide-the-bias.md)): an agent changes how the AI reasons and writes, not the confluence and R:R checks. An analysis with an agent spends plan usage like any analysis.

## Full analysis

Timeframes: 15m, 1h, 4h, 1D, 1W and 1M (1W and 1M since WL-113: weekly and monthly Binance candles, MEXC for pairs Binance no longer trades; signals on them are checked over 12 weeks or 6 months; their Arena memory is the hold style). On 4h and above the suggested stop and targets come from structure (WL-104, `level_hints` in the prompt: `tps`, `final_tp`, `pattern`).

**UI:** Desk → **Full analysis** · **API:** `POST /api/analyze`

```json
{ "symbol": "SOLUSDT", "exchange": "BINANCE", "timeframe": "1h", "custom_prompt": "optional trader notes", "agent": "nadeem_gujjar" }
```

1. Builds the [market snapshot](../analysis-pipeline.md).
2. Sends it to the [AI provider](../ai-providers.md) with the desk-analyst prompt, which asks for a fixed card: BIAS, SETUP, SCORE, TREND, MTF, BOOK, LIQ, FLOW, REGIME, ENTRY, STOP, TARGET, SUPPORT, RESISTANCE, R:R, CONFIDENCE, WHY, PLAN, followed by a JSON block with the levels.
3. Parses the levels, fills gaps from local TA, and applies the [confluence and reward:risk guards](../ai-providers.md#what-happens-to-the-reply).
4. If an AI made the call and the result is a Buy or Sell with entry, stop and target, it is archived as a [signal](signals.md).

**Response** (abridged):

```json
{
  "symbol": "SOLUSDT", "exchange": "BINANCE", "timeframe": "1h",
  "tv_symbol": "BINANCE:SOLUSDT",
  "provider": "claude",
  "levels": {
    "bias": "Buy", "entry": 107.25, "stop_loss": 103.39, "take_profit": 108.53,
    "support": 103.67, "resistance": 108.25, "support_2": 105.8, "resistance_2": 108.25,
    "trend": "Bullish", "trend_line": "…", "ema20": 106.46, "ema50": 105.8,
    "confidence": 0.57, "reasoning": "…"
  },
  "analysis": "BIAS: Buy\nSETUP: trend_continuation — trade ok? yes\n…",
  "market": { "...": "full snapshot, see analysis-pipeline.md" }
}
```

### What the UI does with it

- **KPI strip:** bias, confluence, setup, entry (with SL and TP), reward:risk with confidence, price with 24h change.
- **Structure levels:** every returned level plus the last price, sorted from high to low, each with its own colour.
- **Insight cards:** confluence breakdown, setup and timeframes, whales and derivatives, liquidity and order book.
- **Analyst panel:** a trade card followed by the formatted reply.
- **Log to journal** becomes available.

Changing the pair or the timeframe clears these, so a plan is never shown against a pair or timeframe it wasn't made for.

## Chat

Every pair pick (search, watchlist, picks), also of the same pair again (WL-131), puts a question in the chat with a Think like row (every agent, top Arena scorer first by total R, the one in use filled) and a button per timeframe (WL-112); an agent chip sets the agent (the header select follows), a timeframe button sets the timeframe and runs the full analysis. Calls render as boxes (WL-114).

**UI:** the Analyst composer (Enter sends, Shift+Enter adds a new line). The suggestion chips send common questions.
**API:** `POST /api/chat`

```json
{
  "symbol": "SOLUSDT", "exchange": "BINANCE", "timeframe": "1h",
  "message": "Where is the invalidation?",
  "history": [{ "role": "user", "content": "…" }, { "role": "assistant", "content": "…" }]
}
```

Every chat turn fetches a **fresh** snapshot, so answers reflect the current tape. The prompt includes the last 6 history messages and asks for a reply under 120 words that leads with Bias / Entry / Stop / Target when relevant. Chat replies are not archived as signals.

**Clear** in the panel header resets the conversation. History lives only in the browser tab.
