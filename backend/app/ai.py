"""LLM layer: Claude (API key or Claude Code subscription), Cursor agents, or OpenAI."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from .config import Settings, claude_cli, resolve_provider
from .schemas import ChatMessage, TradeLevels

logger = logging.getLogger(__name__)

# Per-call AI usage for callers that want it (the job runner, WL-052). A list set by
# collect_usage(); contextvars follow asyncio.to_thread, so the blocking providers report too.
_usage_sink: ContextVar[list[dict[str, Any]] | None] = ContextVar("ai_usage_sink", default=None)


@contextmanager
def collect_usage() -> Iterator[list[dict[str, Any]]]:
    """Collect one dict per provider call made inside the block."""
    sink: list[dict[str, Any]] = []
    token = _usage_sink.set(sink)
    try:
        yield sink
    finally:
        _usage_sink.reset(token)


def _int(v: Any) -> int | None:
    return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _record_usage(
    provider: str,
    model: str | None,
    effort: str | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    cost_usd: float | None = None,
) -> None:
    """Tokens and cost stay None when the provider does not report them, never 0."""
    sink = _usage_sink.get()
    if sink is not None:
        sink.append(
            {
                "provider": provider,
                "model": model or None,
                "effort": effort or None,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": cost_usd,
            }
        )

SYSTEM_PROMPT = """You are a crypto trading desk analyst. Be clear and brief — like gptchart.ai.

Hard rules:
- Max ~240 words of prose (not counting the JSON block).
- No markdown tables. No "data note" / outage essays. No walls of numbers.
- Use ONLY fields present in the snapshot. Skip missing fields — do not invent data.
- Bias must be exactly one of: Buy, Sell, Neutral.
- CRITICAL: Respect snapshot.confluence.bias as the preferred bias.
  * If confluence.score is between -2.4 and +2.4 → bias MUST be Neutral (range/wait).
  * If setup.trade_allowed is false OR setup.type is chop → bias MUST be Neutral (no trade).
  * You may keep Buy/Sell only when confluence agrees OR score |x|>=2.5.
  * Do NOT flip to the opposite of confluence.bias.
- Match plan style to setup.type: trend_continuation / breakout / mean_revert / chop.
- Give one primary trade plan with entry, stop_loss, take_profit as real prices near the snapshot price.
- Never use entry/stop/target = 0. Prefer snapshot.level_hints / pivots / S-R.
- Reward:risk must be at least 1.5:1 (|target-entry| >= 1.5 x |entry-stop|). Put the stop
  beyond structure but within ~2 ATR; if no target with 1.5R exists, bias MUST be Neutral.
- Weigh: setup, confluence, mtf, ADX, BB, VWAP, orderbook, liquidity map (long-cascade vs short-squeeze magnets), whales/funding/OI, regime.
- If liquidity.bias is Short-squeeze bias, favor longs only with confluence support; Long-cascade bias favors shorts/caution on longs.
- data_source binance_local is valid.
- snapshot.strategy_fit lists the best-fitting strategies with backtested win rates: name the one or two that fit your plan on the STRATEGY line, with win rate and sample size as given (say "too few trades" when the rate is missing).
- Do not add disclaimers: no "not financial advice", no "I am not a financial adviser", no "do your own research" or risk-warning lines.

Full-analysis reply format (exactly this structure):

BIAS: Buy|Sell|Neutral
SETUP: chop|mean_revert|breakout|trend_continuation — trade ok? yes/no
SCORE: <confluence score>/10 — short note
TREND: Bullish|Bearish|Neutral — short note
MTF: 15m/1h/4h/1d one-liner
BOOK: orderbook bias / imbalance one-liner
LIQ: short-squeeze vs long-cascade | nearest long-liq / short-liq prices
FLOW: Whales … | Retail … | Funding … | OI … (one line)
REGIME: BTC … | risk mode …
ENTRY: <number or n/a>
STOP: <number or n/a>
TARGET: <number or n/a>
SUPPORT: <key support>
RESISTANCE: <key resistance>
R:R: <approx>
STRATEGY: <best strategy> (win rate % over N backtested trades) | <second>
CONFIDENCE: <0-100>%

WHY:
- 4 short bullets max (setup/chop, MTF/confluence, book/whales, risk)

PLAN:
One sentence on the setup. One sentence on invalidation.

Then end with ONLY this JSON fence:
```json
{"bias":"Buy|Sell|Neutral","entry":0,"stop_loss":0,"take_profit":0,"support":0,"resistance":0,"support_2":0,"resistance_2":0,"trend":"Bullish","trend_line":"short note","ema20":0,"ema50":0,"confidence":0.0,"reasoning":"one short sentence"}
```
"""


def build_analysis_prompt(
    symbol: str,
    exchange: str,
    timeframe: str,
    market_block: str,
    custom_prompt: str | None = None,
    agent_block: str | None = None,
    memory_block: str | None = None,
    *,
    strategy_id: str = "desk",
    strategy_label: str = "Desk (default)",
    strategy_rules: str | None = None,
    uses_desk_pipeline: bool = True,
    stop_atr_min: float = 1.0,
    stop_atr_max: float = 2.5,
    min_reward_risk: float = 1.5,
    guard_mode: str = "enforce",
    stop_buffer_atr: float = 0.25,
    entry_style: str = "market",
    entry_offset_atr: float = 0.35,
) -> str:
    extra = f"\nTrader notes: {custom_prompt}" if custom_prompt else ""
    if memory_block:  # WL-080: the Arena backtests, remembered before every trade
        extra += f"\n{memory_block}"
    strategy_block = f"STRATEGY: {strategy_label} ({strategy_id})"
    if strategy_rules:
        strategy_block += f"\n{strategy_rules}"
    strategy_block += (
        f"\nRISK: stop within {stop_atr_min:g}..{stop_atr_max:g} ATR of entry "
        f"(plus ~{stop_buffer_atr:g} ATR buffer beyond structure); "
        f"min R:R {min_reward_risk:g}:1 (else Neutral). "
        f"ENTRY STYLE: {entry_style} (offset ~{entry_offset_atr:g} ATR when limit/reclaim)."
    )
    ai_only = (guard_mode or "enforce").strip().lower().replace("-", "_") == "ai_only"
    if ai_only:
        guard = (
            "GUARD MODE ai_only: YOU own bias, entry, stop_loss and take_profit. "
            "Confluence, chop and setup.trade_allowed are advisory context only. "
            "Still give real prices near the snapshot; prefer strategy RISK bands when they fit."
        )
    elif uses_desk_pipeline:
        guard = "Obey confluence + chop guardrails."
    else:
        guard = (
            "Follow the STRATEGY playbook and RISK line above. Use strategy_pack "
            "indicators only; do not invent missing fields. Desk chop confluence "
            f"Neutral rules do not apply; still require real prices and at least "
            f"{min_reward_risk:g}:1 R:R (else Neutral)."
        )
    if agent_block:
        # WL-070: think like an Arena agent; its own layout replaces the standard one.
        return f"""Full analysis: {exchange}:{symbol} · {timeframe}

{strategy_block}

Market snapshot (includes setup, confluence, MTF, orderbook, whales, regime):
{market_block}
{extra}

{agent_block}

{guard}
"""
    return f"""Full analysis: {exchange}:{symbol} · {timeframe}

{strategy_block}

Market snapshot (includes setup, confluence or strategy_fit, MTF, orderbook, whales, regime):
{market_block}
{extra}

Follow BIAS/SETUP/SCORE/TREND/MTF/BOOK/LIQ/FLOW/REGIME/ENTRY/STOP/TARGET/SUPPORT/RESISTANCE.
{guard} Keep it scannable.
"""


def build_chat_prompt(
    symbol: str,
    exchange: str,
    timeframe: str,
    market_block: str,
    message: str,
    history: list[ChatMessage],
    agent_block: str | None = None,
    memory_block: str | None = None,
) -> str:
    hist = "\n".join(f"{m.role.upper()}: {m.content}" for m in history[-6:])
    hist_block = f"\nRecent chat:\n{hist}\n" if hist else ""
    persona = f"\n{agent_block}\n" if agent_block else ""
    if memory_block:
        persona += f"\n{memory_block}\n"
    return f"""Pair: {exchange}:{symbol} ({timeframe})

Snapshot:
{market_block}
{hist_block}{persona}
USER: {message}

Reply in under 120 words. If levels apply, lead with Bias / Entry / Stop / Target.
"""


def build_live_review_prompt(signal: dict[str, Any], review: dict[str, Any]) -> str:
    """Hybrid live review: AI stance + reason beside the rule stance (WL-067)."""
    advice = review.get("level_advice") if isinstance(review.get("level_advice"), dict) else {}
    pressure = review.get("pressure") if isinstance(review.get("pressure"), dict) else {}
    micro = review.get("micro_tape") if isinstance(review.get("micro_tape"), dict) else {}
    micro_tfs = micro.get("timeframes") if isinstance(micro.get("timeframes"), dict) else {}
    m1 = micro_tfs.get("1m") if isinstance(micro_tfs.get("1m"), dict) else {}
    m5 = micro_tfs.get("5m") if isinstance(micro_tfs.get("5m"), dict) else {}
    return f"""Live review of an OPEN crypto signal. Original plan is frozen.

Original: {signal.get('symbol')} {signal.get('timeframe')} {signal.get('bias')}
strategy={signal.get('strategy_id') or 'desk'}
entry={signal.get('entry')} stop={signal.get('stop_loss')} target={signal.get('take_profit')}
notes={str(signal.get('notes') or '')[:240]}

Live (deterministic desk already computed):
price={review.get('price')} rule_stance={review.get('stance')}
unrealized_r={review.get('unrealized_r')} entry_status={review.get('entry_status')}
summary={review.get('summary')}
level_advice={advice}
revised_entry={review.get('revised_entry')} revised_sl={review.get('revised_stop_loss')} revised_tp={review.get('revised_take_profit')}

Micro tape: 1m trend={m1.get('trend')} rsi={m1.get('rsi')} | 5m trend={m5.get('trend')} rsi={m5.get('rsi')}
Pressure: side={pressure.get('side')} score={pressure.get('score')} summary={pressure.get('summary')}

Give YOUR stance independently (you may agree or disagree with rule_stance).
Use exactly one of: hold | caution | exit_early | wait_entry
- if entry_status is filled, entry is LOCKED: never suggest moving/chasing entry; do not use wait_entry; only discuss stop/target management
- wait_entry only if entry_status is waiting (not filled) and chasing is wrong
- exit_early if banking or cutting makes more sense than the rule band
- caution if structure/flow looks fragile even when rules say hold
- weigh 1m/5m pressure: sellers pressing into a Buy, or buyers pressing into a Sell, raise caution or exit_early

Reply with a short prose reason (under 100 words), then end with ONLY this JSON fence:
```json
{{"ai_stance":"hold|caution|exit_early|wait_entry","reasoning":"one or two short sentences"}}
```
No disclaimers.
"""


_AI_STANCES = frozenset({"hold", "caution", "exit_early", "wait_entry"})


def parse_live_review_ai(text: str) -> dict[str, Any]:
    """Extract ai_stance + reasoning from live-review model text (WL-067)."""
    out: dict[str, Any] = {
        "ai_stance": None,
        "ai_stance_reason": None,
        "ai_reasoning": (text or "").strip()[:1200] or None,
    }
    raw = text or ""
    m = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.S | re.I)
    blob = m.group(1) if m else None
    if not blob:
        m2 = re.search(
            r'\{\s*"ai_stance"\s*:\s*"(hold|caution|exit_early|wait_entry)".*?\}',
            raw,
            re.S | re.I,
        )
        blob = m2.group(0) if m2 else None
    if blob:
        try:
            data = json.loads(blob)
            stance = str(data.get("ai_stance") or "").strip().lower().replace("-", "_")
            if stance == "exit early":
                stance = "exit_early"
            if stance in ("wait for entry", "wait"):
                stance = "wait_entry"
            if stance in _AI_STANCES:
                out["ai_stance"] = stance
            reason = data.get("reasoning") or data.get("reason") or data.get("summary")
            if isinstance(reason, str) and reason.strip():
                out["ai_stance_reason"] = reason.strip()[:400]
                prose = re.sub(r"```json\s*\{.*?\}\s*```", "", raw, flags=re.S | re.I).strip()
                out["ai_reasoning"] = (prose or reason.strip())[:1200]
        except Exception:  # noqa: BLE001
            pass
    if out["ai_stance"] is None:
        m3 = re.search(
            r"\b(?:ai[_\s-]?stance|stance)\s*[:=]\s*(hold|caution|exit_early|wait_entry|exit\s+early|wait)\b",
            raw,
            re.I,
        )
        if m3:
            s = m3.group(1).lower().replace(" ", "_").replace("-", "_")
            if s == "wait":
                s = "wait_entry"
            if s in _AI_STANCES:
                out["ai_stance"] = s
    return out


def extract_levels(text: str) -> TradeLevels:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    raw = None
    if match:
        raw = match.group(1)
    else:
        match2 = re.search(
            r'\{\s*"bias"\s*:\s*"(Buy|Sell|Neutral)".*?\}',
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if match2:
            raw = match2.group(0)

    if not raw:
        bias = "Neutral"
        lower = text.lower()
        if re.search(r"\bbuy\b|\blong\b", lower) and not re.search(
            r"\bdo not buy\b|\bavoid buy\b", lower
        ):
            bias = "Buy"
        elif re.search(r"\bsell\b|\bshort\b", lower):
            bias = "Sell"
        return TradeLevels(bias=bias, reasoning="Parsed from narrative (no JSON block).")

    try:
        data = json.loads(raw)
        bias = str(data.get("bias", "Neutral")).title()
        if bias not in ("Buy", "Sell", "Neutral"):
            bias = "Neutral"
        return TradeLevels(
            bias=bias,  # type: ignore[arg-type]
            entry=_num(data.get("entry")),
            stop_loss=_num(data.get("stop_loss") or data.get("stopLoss")),
            take_profit=_num(data.get("take_profit") or data.get("takeProfit")),
            support=_num(data.get("support")),
            resistance=_num(data.get("resistance")),
            support_2=_num(data.get("support_2") or data.get("support2")),
            resistance_2=_num(data.get("resistance_2") or data.get("resistance2")),
            trend=str(data["trend"]) if data.get("trend") else None,
            trend_line=str(data["trend_line"]) if data.get("trend_line") else None,
            ema20=_num(data.get("ema20")),
            ema50=_num(data.get("ema50")),
            confidence=_confidence(data.get("confidence")),
            reasoning=str(data.get("reasoning") or ""),
        )
    except json.JSONDecodeError:
        return TradeLevels(bias="Neutral", reasoning="Could not parse levels JSON.")


def _num(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    # Model often emits 0 when data was missing — treat as absent
    if n == 0:
        return None
    return n


def _confidence(v: Any) -> float | None:
    """Accept 0–1 or 0–100 from the model; store as 0–1."""
    if v is None or v == "":
        return None
    try:
        n = float(str(v).strip().rstrip("%"))
    except (TypeError, ValueError):
        return None
    if n > 1:
        n = n / 100.0
    if n < 0:
        return None
    return min(n, 1.0)


def strip_json_fence(text: str) -> str:
    return re.sub(
        r"```json\s*\{.*?\}\s*```",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()


def format_clear_brief(
    symbol: str,
    exchange: str,
    timeframe: str,
    levels: TradeLevels,
    raw_text: str,
    keep_layout: bool = False,
) -> str:
    """Normalize model output into a short, scannable desk card. keep_layout keeps an agent's own
    layout (WL-070, Gujjar's RULE-013-P) as the model wrote it, without the JSON fence."""
    body = strip_json_fence(raw_text)
    if keep_layout and body.strip():
        return re.sub(r'\{\s*"bias"\s*:.*\}\s*$', "", body, flags=re.DOTALL | re.IGNORECASE).strip()
    # If the model ignored the format, rebuild from levels + short excerpt
    conf = levels.confidence
    conf_pct = f"{int(round(conf * 100))}%" if conf is not None and conf <= 1 else (
        f"{int(conf)}%" if conf is not None else "—"
    )
    entry = _fmt_px(levels.entry)
    stop = _fmt_px(levels.stop_loss)
    target = _fmt_px(levels.take_profit)
    rr = _rr(levels.entry, levels.stop_loss, levels.take_profit)

    why = levels.reasoning.strip() if levels.reasoning else ""
    # Prefer model body if it already looks structured; else assemble
    if re.search(r"(?i)^BIAS\s*:", body, re.MULTILINE):
        cleaned = body
        # Drop trailing leftover JSON object if any
        cleaned = re.sub(
            r'\{\s*"bias"\s*:.*\}\s*$',
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        ).strip()
        return cleaned

    lines = [
        f"{exchange}:{symbol} · {timeframe}",
        "",
        f"BIAS: {levels.bias}",
        f"TREND: {levels.trend or '—'} — {levels.trend_line or ''}".rstrip(" —"),
        f"ENTRY: {entry}",
        f"STOP: {stop}",
        f"TARGET: {target}",
        f"SUPPORT: {_fmt_px(levels.support)}"
        + (f" / {_fmt_px(levels.support_2)}" if levels.support_2 else ""),
        f"RESISTANCE: {_fmt_px(levels.resistance)}"
        + (f" / {_fmt_px(levels.resistance_2)}" if levels.resistance_2 else ""),
        f"EMA20/50: {_fmt_px(levels.ema20)} / {_fmt_px(levels.ema50)}",
        f"R:R: {rr}",
        f"CONFIDENCE: {conf_pct}",
        "",
        "WHY:",
        f"- {why}" if why else "- See plan below.",
    ]
    # Keep a short slice of model prose if useful
    prose = re.sub(r"(?i)^BIAS\s*:.*?(?=WHY:|PLAN:|$)", "", body, flags=re.DOTALL).strip()
    prose = re.sub(r"\n{3,}", "\n\n", prose)
    if prose and len(prose) < 600 and "BIAS:" not in prose[:40]:
        lines.extend(["", "PLAN:", prose[:500]])
    return "\n".join(lines)


def _fmt_px(v: float | None) -> str:
    if v is None:
        return "n/a"
    if abs(v) >= 1000:
        return f"{v:,.2f}"
    if abs(v) >= 1:
        return f"{v:.4g}"
    return f"{v:.6g}"


def _rr(entry: float | None, stop: float | None, target: float | None) -> str:
    if entry is None or stop is None or target is None:
        return "n/a"
    risk = abs(entry - stop)
    reward = abs(target - entry)
    if risk <= 0:
        return "n/a"
    return f"{reward / risk:.1f}:1"


async def generate_text(prompt: str, settings: Settings) -> tuple[str, str]:
    """Returns (text, provider_name)."""
    provider = resolve_provider(settings)
    if provider == "claude":
        text = await _claude_generate(prompt, settings)
        return text, "claude"
    if provider == "claude_code":
        text = await asyncio.to_thread(_claude_code_generate, prompt, settings)
        return text, "claude_code"
    if provider == "cursor":
        text = await _cursor_generate(prompt, settings)
        return text, "cursor"
    if provider == "openai":
        text = await _openai_generate(prompt, settings)
        return text, "openai"

    return (_offline_stub(prompt), "offline")


# Models that accept the server-side refusal fallback (`fallbacks: "default"`).
_CLAUDE_FALLBACK_MODELS = {
    "claude-fable-5-1",
    "claude-opus-5-5",
    "claude-opus-5",
    "claude-sonnet-5-5",
}


async def _claude_generate(prompt: str, settings: Settings) -> str:
    """Claude via the Anthropic Messages API (ANTHROPIC_API_KEY)."""
    import anthropic

    model = settings.anthropic_model.strip()
    request: dict[str, Any] = {
        "model": model,
        "max_tokens": 16000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
    }
    effort = (settings.anthropic_effort or "").strip().lower()
    if effort:
        request["output_config"] = {"effort": effort}

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key.strip())
    try:
        if model in _CLAUDE_FALLBACK_MODELS:
            # A declined request is re-run on Anthropic's recommended fallback model.
            resp = await client.beta.messages.create(
                **request,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        else:
            resp = await client.messages.create(**request)
    except anthropic.AuthenticationError as exc:
        raise RuntimeError("Claude rejected ANTHROPIC_API_KEY — check backend/.env") from exc
    except anthropic.NotFoundError as exc:
        raise RuntimeError(f"Claude model not found: {model} (ANTHROPIC_MODEL)") from exc
    except anthropic.RateLimitError as exc:
        raise RuntimeError("Claude rate limit hit — wait a moment and retry") from exc
    except anthropic.APIStatusError as exc:
        raise RuntimeError(f"Claude API error {exc.status_code}: {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise RuntimeError("Cannot reach the Claude API — check your network") from exc
    finally:
        await client.close()

    u = resp.usage
    _record_usage(
        "claude",
        resp.model,
        effort,
        sum(_int(getattr(u, k, None)) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
        _int(u.output_tokens),
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("Claude declined this request")
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    if resp.stop_reason == "max_tokens":
        logger.warning("Claude reply hit max_tokens (request %s)", resp._request_id)
    return text


_NOT_LOGGED_IN = ("not logged in", "/login", "invalid api key", "oauth token", "authentication")
# On Windows the CLI gets its own process group, so a Ctrl+C in the server window does not abort it (WL-082).
_CLI_FLAGS = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


def claude_code_error(data: dict | None, stderr: str, out: str, returncode: int | None) -> str:
    """A short, actionable message for a failed `claude -p` call instead of its raw JSON (WL-082)."""
    data = data or {}
    subtype = str(data.get("subtype") or "")
    text = str(data.get("result") or "").strip()
    errors = data.get("errors") if isinstance(data.get("errors"), list) else []
    detail = text or "; ".join(str(e) for e in errors) or (stderr or "").strip() or out or f"exit code {returncode}"
    detail = detail.replace("Terminate batch job (Y/N)?", "").strip()
    if any(k in detail.lower() for k in _NOT_LOGGED_IN):
        return ("Claude Code is not logged in: run `claude auth login`, or put a token from "
                "`claude setup-token` in CLAUDE_CODE_OAUTH_TOKEN")
    if subtype == "error_during_execution" and not text:
        return ("Claude Code stopped before it answered (error_during_execution). This happens when the server "
                "restarts during the call (start.ps1 runs with --reload, so a code change restarts it) or the call "
                "is interrupted. Run the analysis again.")
    if subtype == "error_max_turns":
        return "Claude Code ran out of turns before answering (error_max_turns). Run the analysis again."
    return f"Claude Code error{f' ({subtype})' if subtype else ''}: {detail[-300:]}"


def _cli_json(out: str) -> dict | None:
    """The result object of `claude -p --output-format json`; a stray line after it (an old cmd.exe
    wrapper's batch prompt) is ignored."""
    start = out.find("{")
    try:
        data = json.JSONDecoder().raw_decode(out[start:])[0] if start >= 0 else None
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _record_cli_usage(data: dict, model: str, effort: str) -> None:
    u = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    used = list(data["modelUsage"]) if isinstance(data.get("modelUsage"), dict) else []
    ins = [_int(u.get(k)) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")]
    cost = data.get("total_cost_usd")
    _record_usage(
        "claude_code",
        ", ".join(used) or model or "plan default",
        effort,
        sum(i or 0 for i in ins) if any(i is not None for i in ins) else None,
        _int(u.get("output_tokens")),
        float(cost) if isinstance(cost, (int, float)) else None,
    )


def _claude_code_generate(prompt: str, settings: Settings) -> str:
    """Claude through the local Claude Code CLI — billed to your Claude subscription.

    Runs `claude -p` headless with no tools, no MCP servers, no settings or
    CLAUDE.md files and no saved session, from an empty temp directory, so the
    model sees only our system prompt and the market snapshot. Blocking: call it
    via asyncio.to_thread (uvicorn's loop on Windows cannot spawn subprocesses).
    """
    cli = claude_cli(settings)
    if not cli:
        raise RuntimeError(
            "Claude Code CLI not found — install it (npm install -g @anthropic-ai/claude-code) "
            "or set CLAUDE_CODE_PATH in backend/.env"
        )

    env = os.environ.copy()
    # An API key in the environment would make the CLI bill the API instead of the plan.
    env.pop("ANTHROPIC_API_KEY", None)
    token = (settings.claude_code_oauth_token or "").strip()
    if token:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = token

    with tempfile.TemporaryDirectory(prefix="cca-claude-") as work:
        system_file = Path(work) / "system.md"
        system_file.write_text(SYSTEM_PROMPT, encoding="utf-8")
        cmd = [
            cli,
            "-p",
            "--output-format", "json",
            "--system-prompt-file", str(system_file),
            "--tools", "",
            "--strict-mcp-config",
            "--setting-sources", "",
            "--no-session-persistence",
        ]
        model = settings.claude_code_model.strip()
        if model:
            cmd += ["--model", model]
        effort = settings.claude_code_effort.strip().lower()
        if effort:
            cmd += ["--effort", effort]
        try:
            proc = subprocess.run(  # noqa: S603 — fixed argv, prompt goes in on stdin
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=work,
                env=env,
                timeout=settings.claude_code_timeout,
                creationflags=_CLI_FLAGS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"Claude Code did not answer within {settings.claude_code_timeout}s (CLAUDE_CODE_TIMEOUT)"
            ) from exc

    out = (proc.stdout or "").strip()
    data = _cli_json(out)
    if data is not None:
        _record_cli_usage(data, model, effort)
    if data is not None and not data.get("is_error") and data.get("result"):
        return str(data["result"])
    raise RuntimeError(claude_code_error(data, proc.stderr, out, proc.returncode))


async def _cursor_generate(prompt: str, settings: Settings) -> str:
    """Run Cursor in a worker thread with its own event loop.

    Why: uvicorn's loop on Windows cannot create subprocesses for the SDK bridge
    (NotImplementedError), and the sync Agent.prompt fails too (WinError 10038).
    A fresh ProactorEventLoop in a worker thread works.
    """
    return await asyncio.to_thread(_cursor_generate_blocking, prompt, settings)


def _cursor_generate_blocking(prompt: str, settings: Settings) -> str:
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_cursor_generate_async(prompt, settings))
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:  # noqa: BLE001
                pass
            loop.close()
            asyncio.set_event_loop(None)
    return asyncio.run(_cursor_generate_async(prompt, settings))


async def _cursor_generate_async(prompt: str, settings: Settings) -> str:
    from cursor_sdk import AgentOptions, AsyncAgent, AsyncClient, LocalAgentOptions

    workspace = str(Path(__file__).resolve().parents[1])
    full_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{prompt}"

    async with await AsyncClient.launch_bridge(workspace=workspace) as client:
        result = await AsyncAgent.prompt(
            full_prompt,
            AgentOptions(
                api_key=settings.cursor_api_key,
                model=settings.cursor_model,
                local=LocalAgentOptions(cwd=workspace),
            ),
            client=client,
        )

    _record_usage("cursor", settings.cursor_model)  # the Cursor SDK reports no token counts
    if getattr(result, "status", None) == "error":
        raise RuntimeError(f"Cursor run error: {getattr(result, 'id', result)}")
    out = getattr(result, "result", None)
    if out is None:
        out = getattr(result, "text", None)
    return str(out if out is not None else result)


async def _openai_generate(prompt: str, settings: Settings) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    u = resp.usage
    _record_usage(
        "openai",
        resp.model,
        None,
        _int(getattr(u, "prompt_tokens", None)),
        _int(getattr(u, "completion_tokens", None)),
    )
    return resp.choices[0].message.content or ""


def _offline_stub(prompt: str) -> str:
    return (
        "No AI provider is selected or configured. Restart with start.ps1 / start.sh "
        "and pick one (Claude subscription, Claude API, Cursor or OpenAI), or set "
        "AI_PROVIDER and its key in backend/.env.\n\n"
        "Market context was still fetched successfully for this request — see the "
        "Market panel / API `market` field.\n\n"
        "```json\n"
        '{"bias":"Neutral","entry":null,"stop_loss":null,"take_profit":null,'
        '"confidence":0,"reasoning":"No LLM key configured"}\n'
        "```\n\n"
        f"(Prompt length received: {len(prompt)} chars)"
    )
