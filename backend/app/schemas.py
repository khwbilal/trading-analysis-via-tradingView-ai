from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., examples=["SOLUSDT", "BTCUSDT", "ETHUSDT"])
    exchange: str = Field(default="BINANCE")
    timeframe: str = Field(default="1h", examples=["15m", "1h", "4h", "1D", "1W", "1M"])
    strategy_id: str = Field(
        default="desk",
        examples=["desk", "smc", "all"],
        description="Analysis pack id, or 'all' to run every multi-analyze pack.",
    )
    optimize_mode: str = Field(
        default="local_score",
        examples=["local_score", "ai_ensemble", "majority_vote"],
        description="Only used when strategy_id is 'all'.",
    )
    guard_mode: str = Field(
        default="enforce",
        examples=["enforce", "ai_only"],
        description="enforce: guards may change bias; ai_only: keep model plan.",
    )
    custom_prompt: str | None = None
    agent: str | None = None  # WL-070: an Arena agent id to think like; None is the current system


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    symbol: str = Field(..., examples=["SOLUSDT"])
    exchange: str = Field(default="BINANCE")
    timeframe: str = Field(default="1h")
    strategy_id: str = Field(default="desk")
    message: str
    history: list[ChatMessage] = Field(default_factory=list)
    agent: str | None = None
    analysis_id: int | None = None  # WL-107: the analysis this chat follows; the turn is stored with it


class TradeLevels(BaseModel):
    bias: Literal["Buy", "Sell", "Neutral"] = "Neutral"
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    support: float | None = None
    resistance: float | None = None
    support_2: float | None = None
    resistance_2: float | None = None
    trend: str | None = None
    trend_line: str | None = None
    ema20: float | None = None
    ema50: float | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    reasoning: str = ""


class AnalyzeResponse(BaseModel):
    symbol: str
    exchange: str
    timeframe: str
    tv_symbol: str
    strategy_id: str = "desk"
    strategy_label: str = "Desk (default)"
    market: dict[str, Any]
    levels: TradeLevels
    analysis: str
    provider: str
    agent: str | None = None
    analysis_id: int | None = None  # WL-107: the stored analysis, for the chat that follows
    guard_mode: str = "enforce"
    optimize_mode: str | None = None
    final_strategy_id: str | None = None
    packs: list[dict[str, Any]] | None = None


class ChatResponse(BaseModel):
    symbol: str
    reply: str
    market_snapshot: dict[str, Any] | None = None
    provider: str
    strategy_id: str = "desk"


class HealthResponse(BaseModel):
    status: str
    app: str
    ai_provider: str
    ai_model: str | None = None
    tradingview_ready: bool


class CalendarEvent(BaseModel):
    id: int
    source: str  # forexfactory | nasdaq | binance
    kind: Literal["macro", "earnings", "crypto", "binance"]
    title: str
    starts_at: str  # ISO 8601 in PKT (+05:00)
    all_day: bool = False
    session: str | None = None  # earnings: before_open | after_close
    impact: Literal["high", "medium", "low"] | None = None
    country: str | None = None
    ticker: str | None = None
    instrument_symbols: list[str] = []  # TradingView symbols Binance lists for the ticker
    forecast: str | None = None
    previous: str | None = None
    actual: str | None = None
    url: str | None = None
    fetched_at: str


class CalendarSource(BaseModel):
    name: str
    available: bool | None = None
    error: str | None = None
    events: int | None = None
    fetched_at: str | None = None


class CalendarResponse(BaseModel):
    events: list[CalendarEvent]
    sources: list[CalendarSource]


class CorrelationStat(BaseModel):
    """Correlation and beta of the symbol's log returns to one benchmark."""

    available: bool
    correlation: float | None = None  # Pearson, -1 to 1
    beta: float | None = None  # cov(symbol, benchmark) / var(benchmark)
    overlap_pct: float | None = None  # share of expected candles present for both
    samples: int | None = None  # consecutive returns used
    error: str | None = None


class CorrelationWindow(BaseModel):
    interval: str  # 1h | 1d
    days: int
    candles: int  # expected closed candles in the window
    btc: CorrelationStat
    eth: CorrelationStat


class CorrelationResponse(BaseModel):
    available: bool
    symbol: str
    market: Literal["spot", "usdm", "spot_or_usdm"] | None = None
    windows: dict[str, CorrelationWindow] = {}  # keys: 30d_1h, 90d_1d
    summary: str | None = None
    error: str | None = None


class PulseCell(BaseModel):
    """One timeframe of the pulse; the last candle is the live one."""

    tf: Literal["1M", "1w", "1d", "1h", "15m"]
    available: bool
    price: float | None = None  # last close
    trend: Literal["up", "down", "flat"] | None = None
    rsi: float | None = None  # RSI 14
    ema20: float | None = None
    ema50: float | None = None
    price_vs_ema20: Literal["above", "below"] | None = None
    change_pct: float | None = None  # last candle vs the previous close
    bias: Literal["Buy", "Sell", "Neutral"] | None = None
    candle_open: str | None = None  # ISO 8601 UTC open time of the last candle
    error: str | None = None


class PulseSymbol(BaseModel):
    symbol: str
    available: bool  # the 24h ticker; cells carry their own flag
    price: float | None = None
    change_24h_pct: float | None = None
    error: str | None = None
    timeframes: list[PulseCell]


class PulseResponse(BaseModel):
    symbols: list[PulseSymbol]
    timeframes: list[str]
    rule: str  # the trend and bias rule in words
    generated_at: str


class JobStatus(BaseModel):
    job: str
    schedule: str
    started_at: str | None = None
    finished_at: str | None = None
    exit_code: int | None = None
    message: str | None = None
    next_run: str | None = None  # from Task Scheduler; None when not registered


class JobsResponse(BaseModel):
    jobs: list[JobStatus]


class JobRun(BaseModel):
    """One row of job_runs (WL-052). Times are UTC; AI fields are None when no model was called."""

    id: int
    job: str
    trigger: str | None = None  # scheduled | manual; None for runs before WL-052
    started_at: str
    finished_at: str | None = None
    duration_ms: int | None = None
    exit_code: int | None = None
    message: str | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_effort: str | None = None
    ai_calls: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None  # what the provider reports; for the subscription, the CLI's API-price estimate
    status: Literal["running", "success", "failed", "interrupted"]
    progress_done: int | None = None
    progress_total: int | None = None
    progress_note: str | None = None


class JobRunsResponse(BaseModel):
    runs: list[JobRun]


class WatchlistRequest(BaseModel):
    symbols: list[str] | None = None
    timeframe: str = "1h"


# --- watchlists (WL-149) ---


class WatchlistItem(BaseModel):
    id: int
    watchlist_id: int
    symbol: str
    exchange: str
    position: int
    added_at: str
    name: str | None = None  # WL-152: from the instrument catalogue, None when it has no name


class WatchlistList(BaseModel):
    id: int
    name: str
    position: int
    is_open: bool
    created_at: str
    archived_at: str | None = None
    items: list[WatchlistItem]


class WatchlistsResponse(BaseModel):
    watchlists: list[WatchlistList]
    max_lists: int
    max_items: int


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    is_open: bool = False


class WatchlistUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)
    is_open: bool | None = None


class WatchlistOrder(BaseModel):
    ids: list[int]


class WatchlistItemAdd(BaseModel):
    symbol: str = Field(min_length=2, max_length=40)
    exchange: str = "BINANCE"


class WatchlistQuote(BaseModel):
    price: float
    change_pct: float
    quote_volume: float
    market: Literal["spot", "usdm"]
    # WL-152: % change per period (15m, 4h, 24h, 1d, 1w, 1M); None when that candle is not there yet
    changes: dict[str, float | None] = {}


class WatchlistQuotes(BaseModel):
    quotes: dict[str, WatchlistQuote]
    error: str | None = None


class JournalCreate(BaseModel):
    symbol: str
    timeframe: str = "1h"
    side: Literal["Buy", "Sell"] = "Buy"
    setup: str | None = None
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    confluence: float | None = None
    notes: str = ""


class JournalClose(BaseModel):
    status: Literal["win", "loss", "be", "skipped"]
    exit_price: float | None = None


# --- strategies, backtests, picks, paper trades, hype radar, financials (WL-031 to WL-046) ---


class TaskState(BaseModel):
    """A background run started from the portal, or a scheduled one seen in the database (WL-053)."""

    running: bool
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    progress_done: int | None = None
    progress_total: int | None = None
    progress_note: str | None = None


class DiagramMarker(BaseModel):
    x: float
    y: float
    kind: Literal["entry", "stop", "target", "note"]
    label: str


class DiagramLine(BaseModel):
    label: str
    kind: Literal["fast", "slow", "level"]
    points: list[list[float]]


class DiagramZone(BaseModel):
    x0: float
    x1: float
    y0: float
    y1: float
    label: str


class StrategyDiagram(BaseModel):
    """Price path and markers on a 0..100 grid, y up is price up; the portal draws it as SVG."""

    path: list[list[float]]
    markers: list[DiagramMarker]
    lines: list[DiagramLine] = []
    zones: list[DiagramZone] = []
    caption: str


class Strategy(BaseModel):
    id: str
    name: str
    family: str
    styles: list[Literal["scalp", "day", "swing"]]
    setups: list[str]
    summary: str
    entry: str
    stop: str
    exit: str
    works_when: str
    fails_when: str
    example: str
    diagram: StrategyDiagram
    backtestable: bool
    backtest_note: str | None = None
    stop_atr: float
    target_r: float


class StrategiesResponse(BaseModel):
    strategies: list[Strategy]
    note_counts: dict[str, int]


class StrategyNote(BaseModel):
    id: int
    strategy_id: str
    body: str
    created_at: str
    updated_at: str


class StrategyNoteBody(BaseModel):
    body: str


class StrategyNotesResponse(BaseModel):
    notes: list[StrategyNote]


class BacktestResult(BaseModel):
    strategy_id: str
    style: str
    coin_group: str  # major | large | meme | lowcap | all
    trades: int
    wins: int
    losses: int
    expired: int
    win_rate: float | None = None  # % of all trades that hit the target
    avg_r: float | None = None
    profit_factor: float | None = None  # None when there are no losing trades
    max_drawdown_r: float | None = None
    total_r: float | None = None


class BacktestRun(BaseModel):
    id: int
    started_at: str
    finished_at: str | None = None
    status: str
    message: str | None = None
    params: dict[str, Any] | None = None


class BacktestRunState(BaseModel):
    """One kept backtest run with its state and progress (WL-053)."""

    id: int
    started_at: str
    finished_at: str | None = None
    status: str  # as stored: running | done | failed
    state: Literal["running", "success", "failed", "interrupted"]
    message: str | None = None
    progress_done: int | None = None
    progress_total: int | None = None
    progress_note: str | None = None
    options: dict[str, Any] | None = None  # what the run replayed (WL-055); None for runs before it


class BacktestOptions(BaseModel):
    """A run set up in the wizard (WL-055, WL-057). Empty lists mean all."""

    strategies: list[str] = []
    styles: list[Literal["scalp", "day", "swing", "position", "hold"]] = []
    groups: list[str] = []
    depth: Literal["quick", "deep"] = "quick"
    bars: int | None = Field(None, ge=1000, le=20000)
    any_style: bool | None = None  # None: on for deep, off for quick
    coins: Literal["fixed", "random", "custom"] = "fixed"  # custom: only `symbols`
    random_count: int | None = Field(None, ge=1, le=10)
    seed: int | None = None
    symbols: list[str] = []  # WL-074: your own coins or stock perps, added as group "custom"
    agents: list[str] = []  # WL-074: Arena runs only; empty is every agent


class BacktestChoices(BaseModel):
    """What the wizard can offer (WL-055)."""

    styles: dict[str, dict[str, Any]]  # style -> interval, horizon
    groups: dict[str, list[str]]  # fixed coin lists; lowcap is picked at run time
    tiers: list[str]  # random-coin tiers
    depths: dict[str, dict[str, Any]]
    max_bars: int
    max_random_per_tier: int


class BacktestPooled(BaseModel):
    """What "All runs combined" holds (WL-065)."""

    runs: int
    trades: int


class BacktestResponse(BaseModel):
    run: BacktestRun | None
    runs: list[BacktestRunState]
    results: list[BacktestResult]
    pooled: BacktestPooled | None = None  # set when the results are every finished run combined
    failures: dict[str, dict[str, int]]  # strategy id -> failure tag -> losing trades
    task: TaskState
    min_trades: int
    choices: BacktestChoices


class BacktestTrade(BaseModel):
    id: int
    strategy_id: str
    style: str
    coin_group: str
    symbol: str
    side: Literal["Buy", "Sell"]
    entry_time: int  # ms UTC
    entry: float
    stop: float
    target: float
    exit_time: int | None = None
    exit: float | None = None
    outcome: Literal["win", "loss", "expired"]
    r_multiple: float
    failure_tag: str | None = None


class BacktestTradesResponse(BaseModel):
    trades: list[BacktestTrade]


class PickPaper(BaseModel):
    status: str  # open | win | loss | expired
    r_multiple: float | None = None
    exit: float | None = None
    opened_at: str | None = None
    closed_at: str | None = None


class Pick(BaseModel):
    day: str
    style: Literal["scalp", "day", "swing"]
    rank: int
    symbol: str
    market: str
    type: str
    coin_group: str
    side: Literal["Buy", "Sell"]
    entry: float
    stop: float
    target: float
    rr: float
    score: float
    setup: str | None = None
    strategy_id: str | None = None
    strategy_name: str | None = None
    strategy_firing: bool
    strategy_win_rate: float | None = None  # None under 20 backtest trades
    strategy_trades: int | None = None
    corr_btc: float | None = None
    beta_btc: float | None = None
    corr_eth: float | None = None
    beta_eth: float | None = None
    volume_usd: float | None = None
    details: dict[str, Any] | None = None
    created_at: str
    paper: PickPaper | None = None  # the paper trade opened from this pick (WL-059)


class PicksDay(BaseModel):
    """One stored day of picks and how its paper trades did (WL-059)."""

    day: str
    picks: int
    traded: int
    open: int | None = None
    won: int | None = None
    lost: int | None = None
    expired: int | None = None
    total_r: float | None = None


class PicksResponse(BaseModel):
    day: str | None
    styles: dict[str, list[Pick]]
    generated_at: str | None = None
    lowcap_max: int | None = None
    days: list[PicksDay] = []
    task: TaskState


class PickHistoryRow(BaseModel):
    day: str
    style: Literal["scalp", "day", "swing"]
    rank: int
    symbol: str
    side: Literal["Buy", "Sell"]
    entry: float
    stop: float
    target: float
    rr: float
    score: float
    setup: str | None = None
    strategy_id: str | None = None
    strategy_name: str | None = None
    paper_status: str | None = None
    paper_r: float | None = None
    paper_exit: float | None = None
    paper_closed_at: str | None = None


class PickHistoryResponse(BaseModel):
    symbol: str
    rows: list[PickHistoryRow]


class AgentPick(BaseModel):
    """One pick on an Arena agent's own Top 10 (WL-128)."""

    day: str
    agent_id: str
    style: Literal["scalp", "day", "swing", "position"]
    rank: int
    symbol: str
    market: str
    type: str
    coin_group: str
    side: Literal["Buy", "Sell"]
    entry: float
    stop: float
    target: float | None = None  # None: a trailing exit
    rr: float | None = None
    trail: int | None = None
    strategy: str | None = None
    note: str | None = None
    bars_ago: int
    agent_trades: int | None = None
    agent_win_rate: float | None = None
    agent_avg_r: float | None = None
    volume_usd: float | None = None
    created_at: str


class AgentStanding(BaseModel):
    trades: int
    wins: int
    win_rate: float | None = None
    total_r: float
    avg_r: float | None = None
    points: int


class AgentPicksAgent(BaseModel):
    id: str
    name: str
    person: str
    stance: str
    summary: str
    rules: list[str]
    styles: list[str]  # the pick styles this agent trades
    standing: dict[str, AgentStanding]  # style -> Arena figures (position includes hold)
    picks: dict[str, list[AgentPick]]  # style -> its Top 10


class AgentPicksResponse(BaseModel):
    day: str | None
    days: list[str] = []
    generated_at: str | None = None
    styles: list[str]
    agents: list[AgentPicksAgent]


class PaperTrade(BaseModel):
    id: int
    pick_day: str
    style: str
    symbol: str
    market: str
    coin_group: str
    side: Literal["Buy", "Sell"]
    strategy_id: str | None = None
    entry: float
    stop: float
    target: float
    opened_at: str
    expires_at: str
    status: Literal["open", "win", "loss", "expired"]
    exit: float | None = None
    closed_at: str | None = None
    r_multiple: float | None = None
    last_checked: str | None = None


class PaperStats(BaseModel):
    total: int
    open: int
    won: int
    lost: int
    expired: int
    win_rate: float | None = None
    total_r: float | None = None


class PaperResponse(BaseModel):
    trades: list[PaperTrade]
    stats: PaperStats
    by_style: dict[str, PaperStats]
    by_strategy: dict[str, PaperStats]


class PositionOpen(BaseModel):
    """Open a leveraged paper position at the live price (WL-061)."""

    symbol: str
    market: Literal["spot", "usdm"] = "usdm"
    side: Literal["Buy", "Sell"]
    stop: float | None = None
    target: float | None = None
    margin: float = Field(gt=0)
    leverage: float = Field(ge=1, le=125)
    fee_rate: float = Field(default=0.0005, ge=0, lt=0.01)
    mmr: float = Field(default=0.005, ge=0, lt=0.5)
    pick_day: str | None = None
    style: str | None = None
    notes: str | None = None
    margin_mode: Literal["isolated", "cross"] = "isolated"  # WL-110
    cross_balance: float | None = Field(default=None, gt=0)
    wallet_id: int | None = None  # WL-150: a paper wallet, or none


class PositionClose(BaseModel):
    price: float | None = Field(default=None, gt=0)  # None: the live price


class PositionResult(BaseModel):
    fees: float
    pnl: float
    roe: float


class Position(BaseModel):
    id: int
    account: str
    wallet_id: int | None = None
    symbol: str
    market: str
    side: Literal["Buy", "Sell"]
    entry: float
    stop: float | None = None
    target: float | None = None
    margin: float
    leverage: float
    fee_rate: float
    mmr: float
    qty: float
    liquidation: float
    pick_day: str | None = None
    style: str | None = None
    opened_at: str
    status: Literal["open", "win", "loss", "liquidated", "closed"]
    exit: float | None = None
    closed_at: str | None = None
    fees: float | None = None
    pnl: float | None = None
    roe: float | None = None
    last_checked: str | None = None
    notes: str | None = None
    open_fee: float | None = None  # wallet trades (WL-063): fee paid at the open, USDT
    archived_at: str | None = None
    live_price: float | None = None
    unrealized: PositionResult | None = None
    margin_mode: Literal["isolated", "cross"] | None = None  # WL-110; None on rows from before it
    cross_balance: float | None = None
    signal_id: str | None = None  # WL-150: account 'signal', a signal's paper trade in a paper wallet


class PositionStats(BaseModel):
    total: int
    open: int
    won: int
    lost: int
    liquidated: int
    win_rate: float | None = None
    realized_pnl: float | None = None
    fees: float | None = None
    unrealized_pnl: float | None = None


class PositionsResponse(BaseModel):
    positions: list[Position]
    stats: PositionStats
    price_error: str | None = None


# --- wallets (WL-063) --------------------------------------------------------------------------

Amount = Annotated[float, Field(ge=0)]


class WalletCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    exchange: str = "Binance"
    kind: Literal["futures", "spot", "paper"] = "futures"  # WL-150: paper is simulated
    currency: str = "USDT"
    starting_balance: Amount = 0
    notes: str | None = None


class WalletUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    notes: str | None = None


class WalletEntryCreate(BaseModel):
    kind: Literal["deposit", "withdrawal"]
    amount: float = Field(gt=0)
    at: str | None = None  # ISO; empty: now
    notes: str | None = None


class WalletEntry(BaseModel):
    id: int
    wallet_id: int
    kind: Literal["deposit", "withdrawal"]
    amount: float
    at: str
    archived_at: str | None = None
    notes: str | None = None


class WalletTradeBook(BaseModel):
    """A trade opened on Binance by hand. Give qty, or margin (with leverage)."""

    symbol: str = Field(min_length=2, max_length=30)
    side: Literal["Buy", "Sell"]
    entry: float = Field(gt=0)
    qty: float | None = Field(default=None, gt=0)
    margin: float | None = Field(default=None, gt=0)
    leverage: float = Field(default=1, ge=1, le=125)
    mmr: float = Field(default=0.005, ge=0, lt=0.5)
    open_fee: Amount = 0
    stop: float | None = Field(default=None, gt=0)
    target: float | None = Field(default=None, gt=0)
    opened_at: str | None = None
    pick_day: str | None = None
    style: str | None = None
    notes: str | None = None


class WalletTradeClose(BaseModel):
    exit: float | None = Field(default=None, gt=0)  # required unless liquidated
    close_fee: Amount = 0
    closed_at: str | None = None
    liquidated: bool = False


class WalletHistoryPoint(BaseModel):
    at: str
    kind: Literal["start", "deposit", "withdrawal", "trade"]
    amount: float | None = None
    balance: float
    ref: int | None = None
    symbol: str | None = None
    source: Literal["wallet", "paper", "signal"] | None = None  # WL-150: what kind of trade closed


class WalletSummary(PositionStats):
    starting_balance: float
    deposits: float
    withdrawals: float
    balance: float
    equity: float | None = None


class Wallet(BaseModel):
    id: int
    name: str
    exchange: str
    kind: Literal["futures", "spot", "paper"]
    currency: str
    starting_balance: float
    created_at: str
    archived_at: str | None = None
    notes: str | None = None
    summary: WalletSummary | None = None


class WalletsResponse(BaseModel):
    wallets: list[Wallet]
    price_error: str | None = None


class WalletPairResult(BaseModel):
    symbol: str
    trades: int
    won: int
    lost: int
    pnl: float
    fees: float


class WalletMonth(BaseModel):
    month: str  # YYYY-MM
    trades: int
    won: int
    lost: int
    pnl: float
    deposits: float  # the starting balance counts as money in
    withdrawals: float
    end_balance: float


class WalletSeries(BaseModel):
    """One wallet on the shared day axis (WL-151); balance is None before the wallet starts."""

    id: int
    name: str
    kind: Literal["futures", "spot", "paper"]
    currency: str
    archived_at: str | None = None
    balance: list[float | None]
    pnl: list[float]
    deposits: list[float]
    withdrawals: list[float]
    trades: list[int]
    won: list[int]
    by_pair: list[WalletPairResult]
    by_month: list[WalletMonth]


class WalletCharts(BaseModel):
    days: list[str]
    wallets: list[WalletSeries]


class WalletDetail(BaseModel):
    wallet: Wallet
    trades: list[Position]
    entries: list[WalletEntry]
    history: list[WalletHistoryPoint]
    price_error: str | None = None


class HypeSourceMention(BaseModel):
    source: str
    rank: int | None = None
    detail: str | None = None


class HypeEntry(BaseModel):
    day: str
    rank: int
    symbol: str
    base: str
    name: str | None = None
    on_binance: bool
    hype_score: float
    sources: list[HypeSourceMention]
    mentions: int | None = None
    volume_usd: float | None = None
    volume_change_pct: float | None = None
    oi_change_pct: float | None = None
    price_change_pct: float | None = None
    market_cap_rank: int | None = None
    coin_group: str | None = None
    confluence: float | None = None
    side: str | None = None
    rank_yesterday: int | None = None
    score_change: float | None = None


class HypeSource(BaseModel):
    name: str
    available: bool | None = None
    error: str | None = None
    items: int | None = None
    fetched_at: str | None = None


class HypeResponse(BaseModel):
    day: str | None
    entries: list[HypeEntry]
    sources: list[HypeSource]
    task: TaskState


class FinancialQuarter(BaseModel):
    quarter: str  # 2026-Q3
    partial: bool  # the current, unfinished quarter
    revenue: float | None = None
    net_income: float | None = None
    eps_diluted: float | None = None
    cash: float | None = None
    return_pct: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    quote_volume: float | None = None
    fees: float | None = None
    protocol_revenue: float | None = None
    sources: list[str]
    qoq: dict[str, float | None]  # % change versus the quarter before


class FinancialsResponse(BaseModel):
    symbol: str
    kind: Literal["stock", "etf", "crypto", "other"]
    ticker: str | None = None
    protocol: str | None = None
    fetched_at: str
    sources: dict[str, dict[str, Any]]  # source -> {available, error}
    quarters: list[FinancialQuarter]


class DeepDiveResponse(BaseModel):
    """A token deep dive (WL-083): walls per venue and together, changes since the last dive, token data."""

    id: int
    created_at: str
    symbol: str
    base: str
    mid: float | None = None
    venues: dict[str, dict[str, Any]]  # venue -> {label, available, error, mid, bid_usd, ask_usd, walls}
    walls: dict[str, list[dict[str, Any]]]  # sell | buy -> [{price, usd, qty, distance_pct, x_median}]
    changes: list[dict[str, Any]]
    previous_at: str | None = None
    token: dict[str, Any]
    derivatives: dict[str, Any]
    holders: dict[str, Any]
    unlocks: dict[str, Any]
    settings: dict[str, Any]


class DeepDiveHistory(BaseModel):
    latest: DeepDiveResponse | None = None
    history: list[dict[str, Any]]
