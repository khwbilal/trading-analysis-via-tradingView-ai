"""FastAPI entry — analyze + chat endpoints for Crypto Chart AI."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .ai import (
    build_analysis_prompt,
    build_chat_prompt,
    extract_levels,
    format_clear_brief,
    generate_text,
    strip_json_fence,
)
from .config import get_settings, provider_model, resolve_provider
from .db import init_db
from .market import (
    context_to_prompt_block,
    fetch_coin_context_async,
    normalize_pair,
    tv_symbol,
)
from .schemas import (
    AgentPicksResponse,
    BacktestChoices,
    BacktestOptions,
    BacktestResponse,
    BacktestTradesResponse,
    DeepDiveHistory,
    DeepDiveResponse,
    FinancialsResponse,
    HypeResponse,
    PaperResponse,
    PickHistoryResponse,
    Position,
    PositionClose,
    PositionOpen,
    PositionsResponse,
    PicksResponse,
    Wallet,
    WalletCharts,
    WalletCreate,
    WalletDetail,
    WalletEntry,
    WalletEntryCreate,
    WalletsResponse,
    WalletTradeBook,
    WalletTradeClose,
    WalletUpdate,
    StrategiesResponse,
    StrategyNote,
    StrategyNoteBody,
    StrategyNotesResponse,
    TaskState,
    AnalyzeRequest,
    CalendarResponse,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    CorrelationResponse,
    HealthResponse,
    JobRunsResponse,
    JobsResponse,
    JournalClose,
    JournalCreate,
    PulseResponse,
    TradeLevels,
    WatchlistCreate,
    WatchlistItemAdd,
    WatchlistList,
    WatchlistOrder,
    WatchlistQuotes,
    WatchlistRequest,
    WatchlistsResponse,
    WatchlistUpdate,
)


def _apply_confluence_guardrail(levels: TradeLevels, market: dict) -> TradeLevels:
    """Keep AI bias aligned with deterministic confluence score."""
    conf = market.get("confluence") if isinstance(market, dict) else None
    setup = market.get("setup") if isinstance(market, dict) else None
    if not isinstance(conf, dict) or conf.get("bias") not in ("Buy", "Sell", "Neutral"):
        return levels
    preferred = conf["bias"]
    score = float(conf.get("score") or 0)
    bias = levels.bias
    # Chop / no-trade setup → force Neutral
    if isinstance(setup, dict) and setup.get("trade_allowed") is False:
        bias = "Neutral"
    # Soft zone → force Neutral
    elif abs(score) < 2.5:
        bias = "Neutral"
    # Never allow opposite of strong confluence
    elif preferred == "Buy" and bias == "Sell":
        bias = "Buy"
    elif preferred == "Sell" and bias == "Buy":
        bias = "Sell"
    # A model Neutral stands: the guards make a plan more cautious, never create one (WL-021).

    conf_val = levels.confidence
    if conf.get("confidence") is not None:
        # blend
        c2 = float(conf["confidence"])
        conf_val = c2 if conf_val is None else round((conf_val + c2) / 2, 2)
    if isinstance(setup, dict) and setup.get("trade_allowed") is False:
        # A missing confidence defaults to the cap; a real 0.0 stays 0.0 (WL-026).
        conf_val = 0.4 if conf_val is None else min(conf_val, 0.4)

    reason = levels.reasoning or ""
    guard = conf.get("summary") or conf.get("guardrail") or ""
    if isinstance(setup, dict) and setup.get("summary"):
        guard = f"{setup['summary']} | {guard}".strip(" |")
    if guard and guard not in reason:
        reason = f"{reason} | {guard}".strip(" |")

    return levels.model_copy(
        update={"bias": bias, "confidence": conf_val, "reasoning": reason}
    )


MIN_REWARD_RISK = 1.0


def normalize_guard_mode(raw: str | None) -> str:
    """WL-063: enforce (default) or ai_only (keep model plan, no bias override)."""
    v = (raw or "enforce").strip().lower().replace("-", "_")
    if v in ("ai_only", "aioff", "off", "none", "raw"):
        return "ai_only"
    return "enforce"


def _live_price_from_market(market: dict | None) -> float | None:
    if not isinstance(market, dict):
        return None
    live = market.get("live_price") if isinstance(market.get("live_price"), dict) else {}
    if live.get("available") and isinstance(live.get("price"), (int, float)):
        return float(live["price"])
    yahoo = market.get("yahoo_price") if isinstance(market.get("yahoo_price"), dict) else {}
    if isinstance(yahoo.get("price"), (int, float)):
        return float(yahoo["price"])
    coin = market.get("coin_analysis") if isinstance(market.get("coin_analysis"), dict) else {}
    px = ((coin.get("price_data") or {}) if isinstance(coin.get("price_data"), dict) else {}).get(
        "current_price"
    )
    return float(px) if isinstance(px, (int, float)) else None


def stamp_live_price(market: dict, pair: str) -> dict:
    """Refresh last trade into the snapshot so long ensemble runs are not stuck on a stale print."""
    from .binance_ta import fetch_live_last_price

    if not isinstance(market, dict):
        return market
    px = fetch_live_last_price(pair)
    if px is None:
        return {**market, "live_price": {"available": False}}
    out = {
        **market,
        "live_price": {"available": True, "price": px, "source": "binance_ticker"},
        "yahoo_price": {"price": px, "source": "binance_ticker"},
    }
    coin = out.get("coin_analysis") if isinstance(out.get("coin_analysis"), dict) else None
    if coin is not None:
        price_data = dict(coin.get("price_data") or {})
        price_data["current_price"] = px
        price_data["live_refreshed"] = True
        out["coin_analysis"] = {**coin, "price_data": price_data}
    return out


def _apply_stop_breached_guard(levels: TradeLevels, market: dict | None) -> TradeLevels:
    """Neutral when live mark is already through the stop (WL-081)."""
    if levels.bias not in ("Buy", "Sell"):
        return levels
    stop = levels.stop_loss
    if stop is None:
        return levels
    price = _live_price_from_market(market)
    if price is None:
        return levels
    breached = (levels.bias == "Buy" and price <= float(stop)) or (
        levels.bias == "Sell" and price >= float(stop)
    )
    if not breached:
        return levels
    note = (
        f"Live price {price:g} already through stop {float(stop):g} -> Neutral "
        "(plan invalidated before entry)"
    )
    reason = f"{levels.reasoning} | {note}".strip(" |")
    return levels.model_copy(update={"bias": "Neutral", "reasoning": reason})


def _apply_absurd_levels_guard(levels: TradeLevels, market: dict | None) -> TradeLevels:
    """Neutral when AI entry is far from the live mark (WL-082)."""
    from .binance_ta import level_near_price

    if levels.bias not in ("Buy", "Sell"):
        return levels
    entry = levels.entry
    if entry is None:
        return levels
    price = _live_price_from_market(market)
    if price is None:
        return levels
    if level_near_price(price, entry, max_rel=0.35):
        return levels
    note = (
        f"Entry {float(entry):g} far from live price {price:g} -> Neutral "
        "(structure/price scale mismatch)"
    )
    reason = f"{levels.reasoning} | {note}".strip(" |")
    return levels.model_copy(update={"bias": "Neutral", "reasoning": reason})


def _attach_traps(market: dict) -> dict:
    from .traps import classify_traps

    if not isinstance(market, dict):
        return market
    if isinstance(market.get("traps"), dict) and market["traps"].get("summary") is not None:
        return market
    return {**market, "traps": classify_traps(market)}


def _apply_reward_risk_guard(levels: TradeLevels, *, min_rr: float | None = None) -> TradeLevels:
    """A directional plan must have levels on the right sides and pay at least min_rr."""
    floor = MIN_REWARD_RISK if min_rr is None else float(min_rr)
    if levels.bias not in ("Buy", "Sell"):
        return levels
    entry, stop, target = levels.entry, levels.stop_loss, levels.take_profit
    if entry is None or stop is None or target is None:
        return levels

    if levels.bias == "Buy":
        wrong_side = not (stop < entry < target)
    else:
        wrong_side = not (target < entry < stop)
    risk = abs(entry - stop)
    reward_risk = abs(target - entry) / risk if risk else 0.0

    if wrong_side:
        note = "Levels on the wrong side of entry → Neutral"
    elif reward_risk < floor:
        note = f"R:R {reward_risk:.2f} below {floor:g}:1 → Neutral"
    else:
        return levels
    reason = f"{levels.reasoning} | {note}".strip(" |")
    return levels.model_copy(update={"bias": "Neutral", "reasoning": reason})


def _fill_levels_from_market(levels: TradeLevels, market: dict) -> TradeLevels:
    """Fill blank trade/structure levels from market snapshot."""
    coin = market.get("coin_analysis") if isinstance(market, dict) else None
    if not isinstance(coin, dict):
        return levels
    sug = coin.get("suggested_levels") if isinstance(coin.get("suggested_levels"), dict) else {}
    sr = coin.get("support_resistance") if isinstance(coin.get("support_resistance"), dict) else {}
    structure = coin.get("market_structure") if isinstance(coin.get("market_structure"), dict) else {}
    ema = coin.get("ema") if isinstance(coin.get("ema"), dict) else {}

    def pick(*vals):
        for v in vals:
            if v is not None:
                return v
        return None

    return TradeLevels(
        bias=levels.bias,
        entry=pick(levels.entry, sug.get("entry")),
        stop_loss=pick(levels.stop_loss, sug.get("stop_loss")),
        take_profit=pick(levels.take_profit, sug.get("take_profit")),
        support=pick(levels.support, sug.get("support"), sr.get("nearest_support")),
        resistance=pick(
            levels.resistance, sug.get("resistance"), sr.get("nearest_resistance")
        ),
        support_2=pick(levels.support_2, sug.get("support_2"), sr.get("support_2"), ema.get("ema50")),
        resistance_2=pick(
            levels.resistance_2, sug.get("resistance_2"), sr.get("resistance_2"), ema.get("ema20")
        ),
        trend=levels.trend or sug.get("trend") or structure.get("trend"),
        trend_line=levels.trend_line
        or sug.get("trend_line")
        or structure.get("trend_line"),
        ema20=pick(levels.ema20, sug.get("ema20"), ema.get("ema20")),
        ema50=pick(levels.ema50, sug.get("ema50"), ema.get("ema50")),
        confidence=levels.confidence if levels.confidence not in (None, 0) else 0.45,
        reasoning=levels.reasoning
        or f"Filled from local {market.get('data_source')} structure hints.",
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The React + MUI portal build (WL-047 phase C). start.ps1 / start.sh run `npm run build` first.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
_boot = get_settings()


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    # Migrate the SQLite db and import any old journal.json / signals.json once.
    init_db()
    # WL-103: Nadeem Gujjar's charted setups, stored once.
    from . import reference

    try:
        reference.seed()
    except Exception:  # noqa: BLE001
        logger.warning("reference setups not seeded", exc_info=True)
    # First start: fill the instrument catalogue in a background thread (WL-044).
    from .instruments import refresh_in_background_if_empty

    refresh_in_background_if_empty()
    # Same for the calendar when nothing is stored from today onward (WL-039).
    from .calendar_feed import refresh_in_background_if_empty as calendar_if_empty

    calendar_if_empty()
    yield


app = FastAPI(title=_boot.app_name, version="0.1.0", lifespan=_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_boot.origins + ["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

_NO_BUILD = (
    "<!doctype html><meta charset=utf-8><title>Crypto Chart AI</title>"
    "<p>The portal is not built yet. Run <code>npm run build</code> in <code>frontend/</code> "
    "(start.ps1 and start.sh do this), or use <code>npm run dev</code> on :5173.</p>"
)


@app.get("/", response_model=None)
async def index() -> FileResponse | HTMLResponse:
    page = FRONTEND_DIST / "index.html"
    if page.is_file():
        return FileResponse(page)
    return HTMLResponse(_NO_BUILD, status_code=503)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    tv_ready = False
    try:
        import tradingview_mcp  # noqa: F401

        tv_ready = True
    except ImportError:
        tv_ready = False
    provider = resolve_provider(settings)
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        ai_provider=provider,
        ai_model=provider_model(settings, provider),
        tradingview_ready=tv_ready,
    )


def _agent_block(agent: str | None, pair: str, exchange: str, timeframe: str) -> str | None:
    """WL-070: the playbook of the Arena agent to think like; 422 for an unknown id."""
    from . import agents

    if agent and agent not in agents.BY_ID:
        raise HTTPException(422, f"unknown agent {agent}")
    return agents.playbook(agent, pair, exchange.upper(), timeframe)


def _memory_block(timeframe: str) -> str | None:
    """WL-080: the Arena's record for this timeframe's style, for the prompt; None when there is none.
    WL-103: on 4h and 1D the chart method from Nadeem Gujjar's charts comes first."""
    from . import reference

    parts = [reference.prompt_block(timeframe)]
    try:
        from . import lessons

        parts.append(lessons.prompt_block(timeframe))
    except Exception:  # noqa: BLE001
        logger.warning("backtest memory unavailable", exc_info=True)
    return "\n\n".join(p for p in parts if p) or None


@app.get("/api/reference-setups")
def reference_setups(symbol: str | None = None) -> dict:
    """WL-103: the setups read off Nadeem Gujjar's charts, newest chart first."""
    from . import reference

    return {"setups": reference.setups(symbol), "method": reference.METHOD}


@app.get("/api/arena/lessons")
def arena_lessons(agent: str | None = None, limit: int = 100) -> dict:
    """WL-080: the newest lessons (and rivalry lines with agent=rivalry), the learned filters and the digest."""
    from . import db, lessons

    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM agent_lessons" + (" WHERE agent_id = ?" if agent else "") +
                            " ORDER BY id DESC LIMIT ?", ((agent, min(limit, 500)) if agent else (min(limit, 500),))).fetchall()
        filters = conn.execute("SELECT * FROM agent_filters ORDER BY agent_id, id").fetchall()
    for f in filters:
        f["text"] = lessons.describe(f["kind"], f["value"])
    return {"lessons": rows, "filters": filters, "digest": lessons.digest()}


@app.get("/api/agents")
def agents_list() -> dict:
    from . import agents

    return {"agents": agents.scored_agents(), "default": agents.DEFAULT_AGENT}


@app.get("/api/packs")
def packs_list() -> dict:
    """Analysis packs for Desk multi-analyze (merged catalog)."""
    from .packs import catalog_ids, list_strategies as list_packs

    return {"packs": list_packs(), "multi_ids": catalog_ids(), "default": "desk"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    from .packs import get_pack
    from .traps import apply_pack_quality_guard, apply_trap_guard

    settings = get_settings()
    pair = normalize_pair(req.symbol)
    if not pair:
        raise HTTPException(400, "Invalid symbol")
    guard_mode = normalize_guard_mode(req.guard_mode)
    agent_block = _agent_block(req.agent, pair, req.exchange, req.timeframe)
    memory_block = _memory_block(req.timeframe)

    # All-strategies multi-analyze (ported from khwAI).
    if (req.strategy_id or "").strip().lower() == "all":
        from .multi_analyze import normalize_optimize_mode, run_multi_analyze

        mode = normalize_optimize_mode(req.optimize_mode)
        try:
            multi = await run_multi_analyze(
                pair=pair,
                exchange=req.exchange,
                desk_tf=req.timeframe,
                settings=settings,
                optimize_mode=mode,
                custom_prompt=req.custom_prompt,
                fill_levels=_fill_levels_from_market,
                apply_confluence=_apply_confluence_guardrail,
                apply_rr=_apply_reward_risk_guard,
                guard_mode=guard_mode,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("multi analyze failed")
            detail = str(exc).strip() or type(exc).__name__
            raise HTTPException(status_code=502, detail=f"AI error: {detail}") from exc

        levels: TradeLevels = multi["levels"]
        market = _attach_traps(multi["market"] or {})
        analysis = multi["analysis"]
        provider = multi["provider"]
        effective_tf = str(multi.get("timeframe") or req.timeframe)
        final_sid = multi["strategy_id"]
        strategy_label = multi["strategy_label"]
        packs = multi.get("packs")
        multi_blob = multi.get("multi_analysis")
        winner = get_pack(final_sid)
        if guard_mode == "enforce":
            levels = apply_pack_quality_guard(levels, market)
            levels = apply_trap_guard(levels, market)
            levels = _apply_reward_risk_guard(levels, min_rr=winner.risk.min_reward_risk)
        pre_live = levels.bias
        market = stamp_live_price(market, pair)
        levels = _apply_stop_breached_guard(levels, market)
        levels = _apply_absurd_levels_guard(levels, market)
        if pre_live != levels.bias and levels.bias == "Neutral":
            analysis = (
                f"LIVE INVALIDATION: {pre_live} plan dropped; mark already through the stop "
                "or entry far from live price.\n\n"
                + analysis
            )
        market = {**market, "guard_mode": guard_mode}

        analysis_id: int | None = None
        try:
            from . import analyses

            analysis_id = await asyncio.to_thread(
                analyses.record,
                symbol=pair,
                exchange=req.exchange,
                timeframe=effective_tf,
                agent=None,
                provider=provider,
                levels=levels.model_dump(),
                analysis=analysis,
                market=market,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("analysis archive failed: %s", exc)

        if provider != "offline" and levels.bias in ("Buy", "Sell", "Neutral"):
            try:
                from .signals import record_signal

                sig = record_signal(
                    symbol=pair,
                    timeframe=effective_tf,
                    levels=levels.model_dump(),
                    market=market,
                    analysis_id=analysis_id,
                    strategy_id=final_sid,
                    multi_analysis=multi_blob,
                )
                if sig:
                    market = {**market, "recorded_signal_id": sig.get("id")}
                    if analysis_id is not None:
                        from . import analyses

                        analyses.link_signal(analysis_id, sig["id"])
            except Exception as exc:  # noqa: BLE001
                logger.warning("signal archive failed: %s", exc)

        return AnalyzeResponse(
            symbol=pair,
            exchange=req.exchange.upper(),
            timeframe=effective_tf,
            tv_symbol=tv_symbol(pair, req.exchange),
            strategy_id=final_sid,
            strategy_label=strategy_label,
            market=market,
            levels=levels,
            analysis=analysis,
            provider=provider,
            analysis_id=analysis_id,
            guard_mode=guard_mode,
            optimize_mode=mode,
            final_strategy_id=final_sid,
            packs=packs,
        )

    pack = get_pack(req.strategy_id)
    market = await fetch_coin_context_async(
        pair, req.exchange, req.timeframe, settings, pack.id
    )
    effective_tf = str(market.get("timeframe") or req.timeframe)
    risk = pack.risk
    prompt = build_analysis_prompt(
        pair,
        req.exchange.upper(),
        effective_tf,
        context_to_prompt_block(market),
        req.custom_prompt,
        agent_block,
        memory_block,
        strategy_id=pack.id,
        strategy_label=pack.label,
        strategy_rules=pack.prompt_rules or None,
        uses_desk_pipeline=pack.uses_desk_pipeline,
        stop_atr_min=risk.stop_atr_min,
        stop_atr_max=risk.stop_atr_max,
        min_reward_risk=risk.min_reward_risk,
        guard_mode=guard_mode,
        stop_buffer_atr=risk.stop_buffer_atr,
        entry_style=risk.entry_style,
        entry_offset_atr=risk.entry_offset_atr,
    )
    try:
        text, provider = await generate_text(prompt, settings)
    except Exception as exc:  # noqa: BLE001
        logger.exception("AI generate failed")
        detail = str(exc).strip() or f"{type(exc).__name__}"
        raise HTTPException(status_code=502, detail=f"AI error: {detail}") from exc
    levels = extract_levels(text)
    model_bias = levels.bias
    market = _attach_traps(market)
    levels = _fill_levels_from_market(levels, market)
    if guard_mode == "enforce":
        if pack.uses_desk_pipeline:
            levels = _apply_confluence_guardrail(levels, market)
        else:
            levels = apply_pack_quality_guard(levels, market)
        levels = apply_trap_guard(levels, market)
        levels = _apply_reward_risk_guard(levels, min_rr=risk.min_reward_risk)
    pre_live = levels.bias
    market = stamp_live_price(market, pair)
    levels = _apply_stop_breached_guard(levels, market)
    levels = _apply_absurd_levels_guard(levels, market)
    market = {**market, "guard_mode": guard_mode}
    analysis = format_clear_brief(
        pair, req.exchange.upper(), effective_tf, levels, text, keep_layout=agent_block is not None
    )
    if (
        guard_mode == "enforce"
        and provider != "offline"
        and levels.bias != model_bias
        and pack.uses_desk_pipeline
    ):
        conf = market.get("confluence") if isinstance(market.get("confluence"), dict) else {}
        analysis = (
            f"DESK OVERRIDE: the analyst said {model_bias}; the plan is {levels.bias} "
            f"(confluence {float(conf.get('score') or 0):+.1f}/10 and the R:R guard decide the bias).\n\n"
            + analysis
        )
    elif provider != "offline" and levels.bias != model_bias and levels.bias == "Neutral":
        analysis = (
            f"LIVE INVALIDATION: the analyst said {model_bias}; the plan is Neutral "
            "(live mark already through the stop or absurd entry).\n\n"
            + analysis
        )
    logger.info(
        "analyze %s %s strategy=%s via %s guard=%s -> %s",
        pair,
        effective_tf,
        pack.id,
        provider,
        guard_mode,
        levels.bias,
    )

    analysis_id = None
    try:
        from . import analyses

        analysis_id = await asyncio.to_thread(
            analyses.record,
            symbol=pair,
            exchange=req.exchange,
            timeframe=effective_tf,
            agent=req.agent if agent_block else None,
            provider=provider,
            levels=levels.model_dump(),
            analysis=analysis,
            market=market,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("analysis archive failed: %s", exc)

    if provider != "offline" and levels.bias in ("Buy", "Sell", "Neutral"):
        try:
            from .signals import record_signal

            sig = record_signal(
                symbol=pair,
                timeframe=effective_tf,
                levels=levels.model_dump(),
                market=market,
                analysis_id=analysis_id,
                strategy_id=pack.id,
            )
            if sig:
                market = {**market, "recorded_signal_id": sig.get("id")}
                if analysis_id is not None:
                    from . import analyses

                    analyses.link_signal(analysis_id, sig["id"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("signal archive failed: %s", exc)

    return AnalyzeResponse(
        symbol=pair,
        exchange=req.exchange.upper(),
        timeframe=effective_tf,
        tv_symbol=tv_symbol(pair, req.exchange),
        strategy_id=pack.id,
        strategy_label=pack.label,
        market=market,
        levels=levels,
        analysis=analysis,
        provider=provider,
        agent=req.agent if agent_block else None,
        analysis_id=analysis_id,
        guard_mode=guard_mode,
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    settings = get_settings()
    pair = normalize_pair(req.symbol)
    if not pair or not req.message.strip():
        raise HTTPException(400, "symbol and message are required")
    agent_block = _agent_block(req.agent, pair, req.exchange, req.timeframe)

    market = await fetch_coin_context_async(
        pair, req.exchange, req.timeframe, settings
    )
    prompt = build_chat_prompt(
        pair,
        req.exchange.upper(),
        req.timeframe,
        context_to_prompt_block(market),
        req.message.strip(),
        req.history,
        agent_block,
        _memory_block(req.timeframe),
    )
    try:
        text, provider = await generate_text(prompt, settings)
    except Exception as exc:  # noqa: BLE001
        logger.exception("AI generate failed")
        detail = str(exc).strip() or f"{type(exc).__name__}"
        raise HTTPException(status_code=502, detail=f"AI error: {detail}") from exc
    reply = strip_json_fence(text)
    try:  # WL-107: the turn is kept with the analysis it follows
        from . import analyses

        await asyncio.to_thread(
            analyses.record_chat, analysis_id=req.analysis_id, symbol=pair, timeframe=req.timeframe,
            agent=req.agent if agent_block else None, question=req.message.strip(), answer=reply, provider=provider,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("chat archive failed: %s", exc)
    return ChatResponse(
        symbol=pair,
        reply=reply,
        market_snapshot=None,
        provider=provider,
    )


@app.get("/api/market/{symbol}")
async def market_only(
    symbol: str,
    exchange: str = "BINANCE",
    timeframe: str = "1h",
):
    settings = get_settings()
    pair = normalize_pair(symbol)
    return await fetch_coin_context_async(pair, exchange, timeframe, settings)


@app.get("/api/correlation/{symbol}", response_model=CorrelationResponse)
def correlation(symbol: str) -> CorrelationResponse:
    """Correlation and beta to BTC and ETH, 30d of 1h and 90d of 1d (sync: runs in the threadpool)."""
    from .correlation import compute_correlation

    return CorrelationResponse(**compute_correlation(symbol))


@app.get("/api/pulse", response_model=PulseResponse)
async def pulse() -> PulseResponse:
    """BTC and ETH price, 24h change and a per-timeframe pulse; cached 20 s per cell."""
    from .pulse import build_pulse

    return PulseResponse(**await build_pulse())


@app.get("/api/symbols/search")
async def symbols_search(q: str = "", exchange: str = "BINANCE", limit: int = 25, type: str = ""):  # noqa: A002
    from .symbols import search_symbols

    if type and not q.strip():
        # WL-097: one catalogue type (commodity, ...) without a query, perpetuals first
        from .instruments import search_items

        items = sorted((i for i in search_items() if i["type"] == type), key=lambda i: i["market"] != "usdm")
        return {"results": items[: min(limit, 40)]}
    if not q.strip():
        return {"results": []}
    return {"results": search_symbols(q, exchange=exchange, limit=min(limit, 40))}


@app.post("/api/watchlist/score")
async def watchlist_score(req: WatchlistRequest):
    from .watchlist import score_watchlist

    # WL-149: a list holds up to 40 pairs, so scoring runs off the event loop
    return await asyncio.to_thread(score_watchlist, req.symbols, req.timeframe)


@app.get("/api/watchlist/score")
async def watchlist_score_get(timeframe: str = "1h", symbols: str = ""):
    from .watchlist import DEFAULT_WATCHLIST, score_watchlist

    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()] or None
    return score_watchlist(syms or DEFAULT_WATCHLIST, timeframe)


@app.get("/api/journal/stats")
async def journal_stats():
    from .journal import stats

    return stats()


@app.get("/api/signals")
async def signals_list(
    limit: int = 80,
    symbol: str = "",
    strategy_id: str = "",
    kind: str = "trades",
):
    from .signals import list_signals, signal_stats, with_paper

    rows, price_error = await asyncio.to_thread(
        with_paper,
        list_signals(limit, symbol or None, strategy_id or None, kind),
    )
    return {"signals": rows, "stats": signal_stats(), "price_error": price_error}


@app.get("/api/signals/dashboard")
def signals_dashboard() -> dict:
    from .dashboard import build_dashboard

    return build_dashboard()


@app.get("/api/signals/{signal_id}")
async def signal_get(signal_id: str):
    from .signals import get_signal, with_paper

    sig = get_signal(signal_id)
    if not sig:
        raise HTTPException(404, "signal not found")
    rows, _ = await asyncio.to_thread(with_paper, [sig])
    return {"signal": rows[0] if rows else sig}


@app.delete("/api/signals/{signal_id}")
def signal_delete(signal_id: str) -> dict:
    from .signals import delete_signal

    if not delete_signal(signal_id):
        raise HTTPException(404, "signal not found")
    return {"ok": True}


@app.post("/api/signals/{signal_id}/review")
async def signal_review_one(signal_id: str):
    from .live_review import live_review_one
    from .signals import signal_stats, with_paper

    updated, review, err = await live_review_one(signal_id, with_ai=True)
    if updated is None:
        raise HTTPException(404, err or "signal not found")
    if err and review is None:
        raise HTTPException(400, err)
    rows, _ = await asyncio.to_thread(with_paper, [updated])
    return {"signal": rows[0] if rows else updated, "review": review, "stats": signal_stats()}


@app.post("/api/signals/review")
async def signals_review_open(limit: int = 30):
    from .live_review import live_review_all

    return await live_review_all(only_open=True, limit=limit)


@app.patch("/api/signals/{signal_id}")
def signal_paper_update(signal_id: str, body: dict) -> dict:
    """WL-109: change one signal's paper margin, leverage or margin mode."""
    from .signals import update_paper, with_paper

    try:
        sig = update_paper(signal_id, body)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not sig:
        raise HTTPException(404, "signal not found")
    return {"signal": with_paper([sig])[0][0]}


@app.get("/api/signals/{signal_id}/chart")
def signal_chart(signal_id: str) -> dict:
    """WL-107: live candles from before the call up to now, plus decision levels."""
    from . import analyses
    from .live_review import build_decision_levels
    from .signals import get_signal

    sig = get_signal(signal_id)
    if not sig:
        raise HTTPException(404, "signal not found")
    data = analyses.chart(
        symbol=sig["symbol"],
        timeframe=sig["timeframe"],
        created_at=sig["created_at"],
        analysis_id=sig.get("analysis_id"),
    )
    ctx = sig.get("market_context_json") if isinstance(sig.get("market_context_json"), dict) else {}
    archived = ctx.get("decision_levels") if isinstance(ctx.get("decision_levels"), list) else None
    if archived:
        data["decision_levels"] = archived
    else:
        data["decision_levels"] = build_decision_levels(
            {
                "entry": sig.get("entry"),
                "stop_loss": sig.get("stop_loss"),
                "take_profit": sig.get("take_profit"),
            },
            ctx,
        )
    data["live"] = True
    return data


@app.get("/api/paper-settings")
def paper_settings_get() -> dict:
    """WL-109: the paper trade defaults new signals get."""
    from . import paper_settings

    return paper_settings.get()


@app.put("/api/paper-settings")
def paper_settings_put(body: dict) -> dict:
    from . import paper_settings

    try:
        return paper_settings.save(body)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/analyses")
def analyses_list(symbol: str = "", limit: int = 100, offset: int = 0, kind: Literal["all", "watch"] = "all") -> dict:
    """WL-107: stored analyses, newest first, text cut short. kind=watch: the Neutral calls on watch (WL-117)."""
    from . import analyses

    return analyses.list_analyses(symbol or None, limit, offset, kind)


@app.get("/api/analyses/{analysis_id}")
def analysis_detail(analysis_id: int) -> dict:
    """WL-107: one analysis with its chat."""
    from . import analyses

    row = analyses.detail(analysis_id)
    if not row:
        raise HTTPException(404, "analysis not found")
    return row


@app.get("/api/analyses/{analysis_id}/chart")
def analysis_chart(analysis_id: int) -> dict:
    from . import analyses
    from .live_review import build_decision_levels

    row = analyses.detail(analysis_id)
    if not row:
        raise HTTPException(404, "analysis not found")
    data = analyses.chart(
        symbol=row["symbol"],
        timeframe=row["timeframe"],
        created_at=row["created_at"],
        analysis_id=analysis_id,
    )
    levels = row.get("levels") if isinstance(row.get("levels"), dict) else {}
    data["decision_levels"] = build_decision_levels(levels, {})
    data["live"] = True
    return data


@app.post("/api/signals/verify")
async def signals_verify(symbol: str = "", only_open: bool = True, limit: int = 50):
    """Re-check archived signals vs later candles (TP/SL/expired)."""
    from .signals import verify_all

    return verify_all(
        symbol=symbol or None,
        only_open=only_open,
        limit=limit,
    )


@app.post("/api/signals/{signal_id}/verify")
async def signal_verify_one(signal_id: str):
    from .signals import signal_stats, verify_one

    sig = verify_one(signal_id, force=True)
    if not sig:
        raise HTTPException(404, "signal not found")
    return {"signal": sig, "stats": signal_stats()}


@app.get("/api/calendar", response_model=CalendarResponse)
def calendar_list(days: int = 7, kind: str = "") -> CalendarResponse:
    """Events from today 00:00 PKT for `days` more days, sorted by time, plus source status."""
    from .calendar_feed import list_events, source_status

    if kind and kind not in ("macro", "earnings", "crypto", "binance"):
        raise HTTPException(400, "kind must be macro, earnings, crypto or binance")
    return CalendarResponse(events=list_events(days, kind or None), sources=source_status())


@app.get("/api/jobs", response_model=JobsResponse)
def jobs_status() -> JobsResponse:
    """Last run per scheduled job plus its next run (sync: runs in the threadpool)."""
    from .jobs import job_status

    return JobsResponse(jobs=job_status())


@app.get("/api/jobs/runs", response_model=JobRunsResponse)
def jobs_runs(limit: int = 200, job: str = "") -> JobRunsResponse:
    """Run history, newest first, with UTC times, duration and AI usage (WL-052)."""
    from .jobs import list_runs

    return JobRunsResponse(runs=list_runs(limit, job or None))


@app.get("/api/journal")
async def journal_list(limit: int = 100):
    from .journal import list_entries, stats

    return {"entries": list_entries(limit), "stats": stats()}


@app.post("/api/journal")
async def journal_add(req: JournalCreate):
    from .journal import add_entry

    return add_entry(req.model_dump())


@app.post("/api/journal/{entry_id}/close")
async def journal_close(entry_id: str, req: JournalClose):
    from .journal import close_entry

    try:
        return close_entry(entry_id, req.status, req.exit_price)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.delete("/api/journal/{entry_id}")
async def journal_delete(entry_id: str):
    from .journal import delete_entry

    if not delete_entry(entry_id):
        raise HTTPException(404, "entry not found")
    return {"ok": True}


# --- strategies and notes (WL-031, WL-032) -------------------------------------------


def _strategy_or_404(strategy_id: str):
    from .strategies import get as get_strategy

    strat = get_strategy(strategy_id)
    if strat is None:
        raise HTTPException(404, "strategy not found")
    return strat


@app.get("/api/strategies", response_model=StrategiesResponse)
def strategies_list() -> StrategiesResponse:
    from .strategies import list_strategies
    from .strategy_notes import counts

    return StrategiesResponse(strategies=list_strategies(), note_counts=counts())


@app.get("/api/strategies/{strategy_id}/notes", response_model=StrategyNotesResponse)
def strategy_notes(strategy_id: str) -> StrategyNotesResponse:
    from .strategy_notes import list_notes

    _strategy_or_404(strategy_id)
    return StrategyNotesResponse(notes=list_notes(strategy_id))


@app.post("/api/strategies/{strategy_id}/notes", response_model=StrategyNote)
def strategy_note_add(strategy_id: str, req: StrategyNoteBody) -> StrategyNote:
    from .strategy_notes import add_note

    _strategy_or_404(strategy_id)
    try:
        return StrategyNote(**add_note(strategy_id, req.body))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.put("/api/notes/{note_id}", response_model=StrategyNote)
def strategy_note_update(note_id: int, req: StrategyNoteBody) -> StrategyNote:
    from .strategy_notes import update_note

    try:
        note = update_note(note_id, req.body)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if note is None:
        raise HTTPException(404, "note not found")
    return StrategyNote(**note)


@app.delete("/api/notes/{note_id}")
def strategy_note_delete(note_id: int):
    from .strategy_notes import delete_note

    if not delete_note(note_id):
        raise HTTPException(404, "note not found")
    return {"ok": True}


# --- backtests (WL-033) -----------------------------------------------------------------


@app.get("/api/backtests", response_model=BacktestResponse)
def backtests(run_id: int | None = None, pooled: bool = False) -> BacktestResponse:
    """One run (the newest finished by default), or with pooled=true every finished run combined (WL-065);
    `run` is then the newest finished run, for the fees and options."""
    from . import backtest, tasks

    run = backtest.latest_run(None if pooled else run_id) or (backtest.latest_run() if run_id is not None else None)
    runs = backtest.list_runs()
    task = tasks.status("backtest")
    # A run started by Task Scheduler lives in another process; its row tells us it is going (WL-053).
    live = next((r for r in runs if r["state"] == "running"), None)
    if live:
        task.update(
            running=True,
            started_at=task.get("started_at") or live["started_at"],
            progress_done=live["progress_done"],
            progress_total=live["progress_total"],
            progress_note=live["progress_note"],
        )
    return BacktestResponse(
        run=run,
        runs=runs,
        results=(backtest.results() if pooled else backtest.results(run["id"])) if run else [],
        failures=(backtest.failure_breakdown(pooled=True) if pooled else backtest.failure_breakdown(run["id"])) if run else {},
        pooled=backtest.pooled_info() if pooled and run else None,
        task=task,
        min_trades=backtest.MIN_TRADES_FOR_RATE,
        choices=BacktestChoices(
            styles=backtest.STYLES,
            groups={k: list(v) for k, v in backtest.GROUPS.items()} | {"lowcap": [], "stock": [], "commodity": []},
            tiers=list(backtest.TIERS),
            depths=backtest.DEPTHS,
            max_bars=backtest.MAX_BARS,
            max_random_per_tier=backtest.MAX_RANDOM_PER_TIER,
        ),
    )


@app.get("/api/backtests/trades", response_model=BacktestTradesResponse)
def backtest_trades(strategy: str, style: str, group: str = "all", limit: int = 100,
                    run_id: int | None = None, pooled: bool = False) -> BacktestTradesResponse:
    from . import backtest

    return BacktestTradesResponse(
        trades=backtest.trades(strategy, style, group, run_id=run_id, limit=min(max(limit, 1), 500), pooled=pooled)
    )


@app.get("/api/backtests/search")
def backtest_search(symbol: str | None = None, strategy: str | None = None, style: str | None = None,
                    group: str | None = None, side: str | None = None, outcome: str | None = None,
                    date_from: str | None = None, date_to: str | None = None, limit: int = 100,
                    offset: int = 0) -> dict:
    """WL-077: search every finished run's distinct trades."""
    import re

    from . import backtest

    for d in (date_from, date_to):
        if d and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            raise HTTPException(422, "dates are YYYY-MM-DD")
    filters = {"symbol": symbol, "strategy": strategy, "style": style, "group": group, "side": side,
               "outcome": outcome, "date_from": date_from, "date_to": date_to}
    return backtest.search_trades(filters, min(max(limit, 1), 1000), max(offset, 0))


@app.post("/api/backtests/run", response_model=TaskState)
def backtest_start(body: BacktestOptions | None = None) -> TaskState:
    from . import backtest, tasks

    options = body.model_dump() if body else None
    try:
        backtest.normalize_options(options)  # a bad option is a 422 now, not a failed background run
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not tasks.start("backtest", lambda: backtest.run_backtest(refresh=True, options=options)):
        raise HTTPException(409, "a backtest is already running")
    return TaskState(**tasks.status("backtest"))


# --- the Arena: trading agents compete (WL-069) ------------------------------------------------


def backtest_styles() -> tuple[str, ...]:
    """The styles a back test or Arena run knows (WL-105 added hold)."""
    from . import backtest

    return tuple(backtest.STYLES)


def _arena_filters(agents_: str | None, date_from: str | None, date_to: str | None, **more: str | None) -> dict:
    """Query parameters to Arena filters (WL-075, WL-077). `agents` is a comma list; dates are YYYY-MM-DD."""
    import re

    from . import agents

    for d in (date_from, date_to):
        if d and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            raise HTTPException(422, "dates are YYYY-MM-DD")
    ids = [a for a in (agents_ or "").split(",") if a]
    unknown = [a for a in ids if a not in agents.BY_ID]
    if unknown:
        raise HTTPException(404, f"no agent {', '.join(unknown)}")
    return {"agents": ids, "date_from": date_from, "date_to": date_to, **{k: v for k, v in more.items() if v}}


@app.get("/api/arena")
def arena_overview(style: str = "all", days: int = 30, agents: str | None = None, date_from: str | None = None,
                   date_to: str | None = None) -> dict:
    """Standings (with the per-bucket rows), days and history for the filters; days up to 3,650."""
    from . import agents as arena

    if style not in ("all", *backtest_styles()):
        raise HTTPException(422, f"style must be all or one of {', '.join(backtest_styles())}")
    filters = _arena_filters(agents, date_from, date_to)
    return arena.overview(style, min(max(days, 1), 3650), filters)


@app.get("/api/arena/charts")
def arena_charts(style: str = "all", agents: str | None = None, date_from: str | None = None,
                 date_to: str | None = None) -> dict:
    """The Arena graphs and agent map (WL-094, WL-095): R per day, figures per style, strategies per agent."""
    from . import agents as arena

    if style not in ("all", *backtest_styles()):
        raise HTTPException(422, f"style must be all or one of {', '.join(backtest_styles())}")
    return arena.charts(style, _arena_filters(agents, date_from, date_to))


@app.get("/api/arena/runs")
def arena_runs() -> dict:
    from . import agents

    return {"runs": agents.list_runs()}


@app.get("/api/arena/trades")
def arena_trades(agent: str | None = None, agents: str | None = None, style: str | None = None,
                 date_from: str | None = None, date_to: str | None = None, bucket: str | None = None,
                 coin_group: str | None = None, symbol: str | None = None, strategy: str | None = None,
                 side: str | None = None, outcome: str | None = None, limit: int = 200, offset: int = 0,
                 sort: str | None = None, order: str = "desc") -> dict:
    """Search agent trades (WL-077): any mix of filters, newest close first or by `sort` (WL-144), `total` for paging."""
    from . import agents as arena

    filters = _arena_filters(agents or agent, date_from, date_to, style=style, bucket=bucket,
                             coin_group=coin_group, symbol=symbol, strategy=strategy, side=side, outcome=outcome)
    return arena.search_trades(filters, min(max(limit, 1), 1000), max(offset, 0), sort, order != "asc")


# --- mock tests (WL-081) ----------------------------------------------------------------------


@app.post("/api/mock")
def mock_start(body: dict) -> dict:
    """Start a mock test: {kind: strategy|agent, ref, mode: backtest|paper, styles, symbols, days, depth, bars}."""
    from . import mock

    try:
        return mock.start(body)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/mock")
def mock_list(limit: int = 50) -> dict:
    from . import mock

    return {"sessions": mock.list_sessions(min(max(limit, 1), 200))}


@app.post("/api/mock/check")
def mock_check() -> dict:
    """Open and resolve mock paper trades now (the paper job does it every 4 hours)."""
    from . import mock

    return mock.run()


@app.post("/api/mock/{session_id}/stop")
def mock_stop(session_id: int) -> dict:
    from . import mock

    try:
        return mock.stop(session_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/arena/reports")
def arena_reports(limit: int = 20) -> dict:
    """WL-079: the professional backtest reports, newest first."""
    from . import evaluation

    return {"reports": evaluation.list_reports(min(max(limit, 1), 100))}


@app.post("/api/arena/pro")
def arena_pro(target: int = 30000, max_coins: int = 150, agents: str | None = None) -> dict:
    """WL-079: start a professional run in the background: coins are added until every agent has `target`
    trades (or `max_coins` is reached), then an equal-sample report. No AI."""
    from . import agents as arena
    from . import evaluation, tasks

    ids = [a for a in (agents or "").split(",") if a]
    if [a for a in ids if a not in arena.BY_ID]:
        raise HTTPException(422, "unknown agent")
    target, max_coins = min(max(target, 100), 100_000), min(max(max_coins, 1), 400)
    if not tasks.start("arena", lambda: evaluation.run_pro(target, ids or None, max_coins)):
        raise HTTPException(409, "an Arena run is already going")
    return tasks.status("arena")


@app.get("/api/arena/review")
def arena_review(agent: str, style: str | None = None, date_from: str | None = None, date_to: str | None = None) -> dict:
    """WL-078: why an agent wins and loses, and what it should change."""
    from . import agents as arena

    filters = _arena_filters(agent, date_from, date_to, style=style)
    return arena.review(agent, filters)


@app.post("/api/arena/run", response_model=TaskState)
def arena_start(body: BacktestOptions | None = None) -> TaskState:
    from . import agents, tasks

    options = body.model_dump() if body else None
    try:
        from . import backtest

        backtest.normalize_options(options)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    unknown = [a for a in (options or {}).get("agents") or [] if a not in agents.BY_ID]
    if unknown:
        raise HTTPException(422, f"no agent {', '.join(unknown)}")
    if not agents.run_in_background(options):
        raise HTTPException(409, "an Arena run is already going")
    return TaskState(**tasks.status("arena"))


# --- picks and paper trades (WL-037, WL-038) ------------------------------------------------


@app.get("/api/picks", response_model=PicksResponse)
def picks_list(day: str = "", include_stocks: bool = False) -> PicksResponse:
    from . import picks, tasks

    return PicksResponse(**picks.get_picks(day or None, include_stocks), task=tasks.status("picks"))


@app.get("/api/picks/history", response_model=PickHistoryResponse)
def picks_history(symbol: str, limit: int = 200) -> PickHistoryResponse:
    """Every day a symbol was picked, with its paper result (WL-059)."""
    from . import picks

    return PickHistoryResponse(symbol=symbol.upper(), rows=picks.symbol_history(symbol, min(max(limit, 1), 1000)))


@app.get("/api/picks/agents", response_model=AgentPicksResponse)
def picks_agents(day: str = "") -> AgentPicksResponse:
    """Each Arena agent's own Top 10 per style for a day, with its Arena standing per style (WL-128)."""
    from . import picks

    return AgentPicksResponse(**picks.get_agent_picks(day or None))


@app.post("/api/picks/run", response_model=TaskState)
def picks_start() -> TaskState:
    from . import picks, tasks

    if not tasks.start("picks", lambda: picks.build_picks(include_stocks=True)):
        raise HTTPException(409, "picks are already being built")
    return TaskState(**tasks.status("picks"))


@app.get("/api/paper", response_model=PaperResponse)
def paper_list(limit: int = 300) -> PaperResponse:
    from . import paper

    return PaperResponse(**paper.list_trades(min(max(limit, 1), 1000)))


@app.post("/api/paper/check")
def paper_check():
    from . import paper, positions

    return {**paper.check_open(), "positions": positions.check_open()}


# --- leveraged paper positions (WL-061) -----------------------------------------------------


@app.get("/api/positions", response_model=PositionsResponse)
def positions_list(limit: int = 300) -> PositionsResponse:
    from . import positions

    return PositionsResponse(**positions.list_positions(min(max(limit, 1), 1000)))


@app.post("/api/positions", response_model=Position)
def positions_open(body: PositionOpen) -> Position:
    from . import positions

    try:
        return Position(**positions.open_position({**body.model_dump(), "symbol": body.symbol.upper().replace(".P", "")}))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Binance price unavailable: {exc}") from exc


@app.post("/api/positions/{pos_id}/close", response_model=Position)
def positions_close(pos_id: int, body: PositionClose) -> Position:
    from . import positions

    try:
        row = positions.close_position(pos_id, body.price)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Binance price unavailable: {exc}") from exc
    if not row:
        raise HTTPException(404, "no open position with that id")
    return Position(**row)


# --- watchlists: up to 4 lists of 40 pairs (WL-149) ----------------------------------------------


@app.get("/api/watchlists", response_model=WatchlistsResponse)
def watchlists_list(include_archived: bool = False) -> WatchlistsResponse:
    from . import watchlists

    return WatchlistsResponse(**watchlists.list_watchlists(include_archived))


@app.post("/api/watchlists", response_model=WatchlistList)
def watchlists_create(body: WatchlistCreate) -> WatchlistList:
    from . import watchlists

    return WatchlistList(**_wallet_call(watchlists.create_watchlist, body.model_dump()))


@app.put("/api/watchlists/order", response_model=WatchlistsResponse)
def watchlists_order(body: WatchlistOrder) -> WatchlistsResponse:
    from . import watchlists

    return WatchlistsResponse(**_wallet_call(watchlists.reorder_watchlists, body.ids))


@app.get("/api/watchlists/quotes", response_model=WatchlistQuotes)
def watchlists_quotes(symbols: str = "") -> WatchlistQuotes:
    from . import watchlists

    return WatchlistQuotes(**_wallet_call(watchlists.quotes, symbols.split(",")))


@app.patch("/api/watchlists/{list_id}", response_model=WatchlistList)
def watchlists_update(list_id: int, body: WatchlistUpdate) -> WatchlistList:
    from . import watchlists

    return WatchlistList(**_wallet_call(watchlists.update_watchlist, list_id, body.model_dump()))


@app.post("/api/watchlists/{list_id}/archive", response_model=WatchlistList)
def watchlists_archive(list_id: int, restore: bool = False) -> WatchlistList:
    from . import watchlists

    return WatchlistList(**_wallet_call(watchlists.archive_watchlist, list_id, not restore))


@app.post("/api/watchlists/{list_id}/items", response_model=WatchlistList)
def watchlists_add(list_id: int, body: WatchlistItemAdd) -> WatchlistList:
    from . import watchlists

    return WatchlistList(**_wallet_call(watchlists.add_item, list_id, body.model_dump()))


@app.post("/api/watchlists/{list_id}/items/{item_id}/archive", response_model=WatchlistList)
def watchlists_remove(list_id: int, item_id: int) -> WatchlistList:
    from . import watchlists

    return WatchlistList(**_wallet_call(watchlists.remove_item, list_id, item_id))


@app.put("/api/watchlists/{list_id}/order", response_model=WatchlistList)
def watchlists_items_order(list_id: int, body: WatchlistOrder) -> WatchlistList:
    from . import watchlists

    return WatchlistList(**_wallet_call(watchlists.reorder_items, list_id, body.ids))


# --- wallets: trades opened on Binance by hand, booked here (WL-063) ---------------------------


def _wallet_call(fn, *args):
    """Run a wallets function and map its errors: LookupError 404, ValueError 400."""
    try:
        return fn(*args)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/wallets", response_model=WalletsResponse)
def wallets_list(include_archived: bool = False) -> WalletsResponse:
    from . import wallets

    return WalletsResponse(**wallets.list_wallets(include_archived))


@app.post("/api/wallets", response_model=Wallet)
def wallets_create(body: WalletCreate) -> Wallet:
    from . import wallets

    return Wallet(**_wallet_call(wallets.create_wallet, body.model_dump()))


@app.get("/api/wallets/charts", response_model=WalletCharts)
def wallets_charts(include_archived: bool = False) -> WalletCharts:
    """WL-151: every wallet day by day on one axis, with results by pair and month."""
    from . import wallets

    return WalletCharts(**wallets.charts(include_archived))


@app.get("/api/wallets/{wallet_id}", response_model=WalletDetail)
def wallets_detail(wallet_id: int) -> WalletDetail:
    from . import wallets

    return WalletDetail(**_wallet_call(wallets.wallet_detail, wallet_id))


@app.patch("/api/wallets/{wallet_id}", response_model=Wallet)
def wallets_update(wallet_id: int, body: WalletUpdate) -> Wallet:
    from . import wallets

    return Wallet(**_wallet_call(wallets.update_wallet, wallet_id, body.model_dump()))


@app.post("/api/wallets/{wallet_id}/archive", response_model=Wallet)
def wallets_archive(wallet_id: int, restore: bool = False) -> Wallet:
    from . import wallets

    return Wallet(**_wallet_call(wallets.archive_wallet, wallet_id, not restore))


@app.post("/api/wallets/{wallet_id}/entries", response_model=WalletEntry)
def wallets_entry(wallet_id: int, body: WalletEntryCreate) -> WalletEntry:
    from . import wallets

    return WalletEntry(**_wallet_call(wallets.add_entry, wallet_id, body.model_dump()))


@app.post("/api/wallets/{wallet_id}/entries/{entry_id}/archive", response_model=WalletEntry)
def wallets_entry_archive(wallet_id: int, entry_id: int) -> WalletEntry:
    from . import wallets

    return WalletEntry(**_wallet_call(wallets.archive_entry, wallet_id, entry_id))


@app.post("/api/wallets/{wallet_id}/trades", response_model=Position)
def wallets_book(wallet_id: int, body: WalletTradeBook) -> Position:
    from . import wallets

    return Position(**_wallet_call(wallets.book_trade, wallet_id, body.model_dump()))


@app.post("/api/wallets/{wallet_id}/trades/{pos_id}/close", response_model=Position)
def wallets_close(wallet_id: int, pos_id: int, body: WalletTradeClose) -> Position:
    from . import wallets

    return Position(**_wallet_call(wallets.close_trade, wallet_id, pos_id, body.model_dump()))


@app.post("/api/wallets/{wallet_id}/trades/{pos_id}/archive", response_model=Position)
def wallets_trade_archive(wallet_id: int, pos_id: int) -> Position:
    from . import wallets

    return Position(**_wallet_call(wallets.archive_trade, wallet_id, pos_id))


# --- hype radar (WL-042) --------------------------------------------------------------------


@app.get("/api/hype", response_model=HypeResponse)
def hype_list(day: str = "") -> HypeResponse:
    from . import hype, tasks

    return HypeResponse(**hype.get_radar(day or None), task=tasks.status("hype"))


@app.post("/api/hype/run", response_model=TaskState)
def hype_start() -> TaskState:
    from . import hype, tasks

    if not tasks.start("hype", hype.build):
        raise HTTPException(409, "the hype radar is already being built")
    return TaskState(**tasks.status("hype"))


# --- financials (WL-046) ----------------------------------------------------------------------


@app.get("/api/financials/{symbol}", response_model=FinancialsResponse)
def financials_get(symbol: str, refresh: bool = False) -> FinancialsResponse:
    from . import financials

    data = financials.get(symbol, force=refresh)
    if not data:
        raise HTTPException(502, "financials could not be built")
    return FinancialsResponse(**data)


# --- token deep dive (WL-083) -----------------------------------------------------------------


@app.get("/api/deepdive/{symbol}", response_model=DeepDiveHistory)
def deepdive_get(symbol: str) -> DeepDiveHistory:
    from . import deepdive

    last = deepdive.latest(symbol)
    return DeepDiveHistory(latest=DeepDiveResponse(**last) if last else None, history=deepdive.history(symbol))


@app.post("/api/deepdive/{symbol}", response_model=DeepDiveResponse)
def deepdive_run(symbol: str) -> DeepDiveResponse:
    from . import deepdive

    try:
        return DeepDiveResponse(**deepdive.run(symbol))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def run() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    run()
