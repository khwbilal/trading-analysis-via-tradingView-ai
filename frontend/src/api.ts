export type Bias = "Buy" | "Sell" | "Neutral";

export type TradeLevels = {
  bias: Bias;
  entry: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  support: number | null;
  resistance: number | null;
  support_2: number | null;
  resistance_2: number | null;
  trend: string | null;
  trend_line: string | null;
  ema20: number | null;
  ema50: number | null;
  confidence: number | null;
  reasoning: string;
};

export type Confluence = {
  score?: number;
  bias?: Bias;
  confidence?: number;
  components?: Record<string, number>;
  summary?: string;
};

export type Setup = {
  type?: string;
  trade_allowed?: boolean;
  prefer_bias?: Bias | null;
  adx?: number | null;
  mtf_alignment?: string;
  summary?: string;
};

export type MtfFrame = { trend?: string; rsi?: number; macd?: string; adx?: number };

export type Flow = {
  available?: boolean;
  whale_bias?: string;
  whale_long_pct?: number;
  retail_bias?: string;
  retail_long_pct?: number;
  funding_bias?: string;
  funding_apr_est?: number;
  oi_change_pct?: number;
  taker_bias?: string;
  oi_price_signal?: string;
  basis_pct?: number;
  price_change_24h_pct?: number;
  summary?: string;
};

export type LiqPoint = { price?: number; distance_pct?: number; move_pct?: number };

export type Liquidity = {
  available?: boolean;
  bias?: string;
  long_share_pct?: number;
  short_share_pct?: number;
  nearest_long_liq?: LiqPoint;
  nearest_short_liq?: LiqPoint;
  cascade?: { long_cascade_trigger?: LiqPoint; short_squeeze_trigger?: LiqPoint };
  summary?: string;
};

export type OrderBook = { available?: boolean; bias?: string; imbalance?: number };

export type Market = {
  data_source?: string;
  coin_analysis?: { price_data?: { current_price?: number } };
  yahoo_price?: { price?: number; change_pct?: number };
  flow?: Flow;
  orderbook?: OrderBook;
  liquidity?: Liquidity;
  mtf_local?: { alignment?: string; timeframes?: Record<string, MtfFrame> };
  setup?: Setup;
  confluence?: Confluence;
  correlation?: Correlation;
  strategy_fit?: StrategyFit;
  recorded_signal_id?: string;
};

export type OptimizeMode = "local_score" | "ai_ensemble" | "majority_vote";
export type GuardMode = "enforce" | "ai_only";

export type StrategyPackResult = {
  strategy_id: string;
  strategy_label: string;
  timeframe?: string;
  bias?: Bias;
  entry?: number | null;
  stop_loss?: number | null;
  take_profit?: number | null;
  confidence?: number | null;
  reasoning?: string;
  fit_score?: number;
  trade_allowed?: boolean;
  pack_score?: number;
  analysis?: string;
  error?: string;
};

export type MultiAnalysis = {
  optimize_mode?: OptimizeMode | string;
  reason?: string;
  final_strategy_id?: string;
  packs?: StrategyPackResult[];
};

export type AnalysisPack = {
  id: string;
  label: string;
  summary: string;
  primary_tf?: string | null;
  multi_analyze?: boolean;
};

export type AnalyzeResponse = {
  symbol: string;
  exchange: string;
  timeframe: string;
  tv_symbol: string;
  strategy_id?: string;
  strategy_label?: string;
  market: Market;
  levels: TradeLevels;
  analysis: string;
  provider: string;
  agent?: string | null;
  analysis_id?: number | null; // WL-107: the stored analysis, sent with the chat that follows
  guard_mode?: GuardMode | string;
  optimize_mode?: OptimizeMode | string | null;
  final_strategy_id?: string | null;
  packs?: StrategyPackResult[] | null;
};

export type ChatMessage = { role: "user" | "assistant" | "system"; content: string };

export type ChatResponse = { symbol: string; reply: string; provider: string };

export type HealthResponse = {
  status: string;
  app: string;
  ai_provider: string;
  ai_model: string | null;
  tradingview_ready: boolean;
};

export type InstrumentType = "crypto" | "stock" | "etf" | "commodity" | "fx" | "index" | "premarket";

export type SymbolResult = {
  symbol: string;
  exchange: string;
  tv_symbol: string;
  kind: string;
  label: string;
  /** From the instrument catalogue (WL-044); null when only the ticker is known. */
  name?: string | null;
  type?: InstrumentType | string;
  market?: string | null;
  aliases?: string;
};

/** Correlation and beta of the symbol's log returns to one benchmark (WL-036). */
export type CorrelationStat = {
  available: boolean;
  correlation?: number | null;
  beta?: number | null;
  overlap_pct?: number | null;
  samples?: number | null;
  error?: string | null;
};

export type CorrelationWindow = {
  interval: string;
  days: number;
  candles: number;
  btc: CorrelationStat;
  eth: CorrelationStat;
};

export type Correlation = {
  available: boolean;
  symbol?: string;
  market?: string | null;
  /** Keys: 30d_1h, 90d_1d. */
  windows?: Record<string, CorrelationWindow>;
  summary?: string | null;
  error?: string | null;
};

export type PulseTf = "1M" | "1w" | "1d" | "1h" | "15m";

export type PulseCell = {
  tf: PulseTf;
  available: boolean;
  price?: number | null;
  trend?: "up" | "down" | "flat" | null;
  rsi?: number | null;
  ema20?: number | null;
  ema50?: number | null;
  price_vs_ema20?: "above" | "below" | null;
  change_pct?: number | null;
  bias?: Bias | null;
  candle_open?: string | null;
  error?: string | null;
};

export type PulseSymbol = {
  symbol: string;
  available: boolean;
  price?: number | null;
  change_24h_pct?: number | null;
  error?: string | null;
  timeframes: PulseCell[];
};

export type PulseResponse = {
  symbols: PulseSymbol[];
  timeframes: string[];
  rule: string;
  generated_at: string;
};

export type CalendarKind = "macro" | "earnings" | "crypto" | "binance";

export type CalendarEvent = {
  id: number;
  source: string;
  kind: CalendarKind;
  title: string;
  /** ISO 8601 in PKT (+05:00). */
  starts_at: string;
  all_day: boolean;
  /** Earnings: before_open or after_close. */
  session?: string | null;
  impact?: "high" | "medium" | "low" | null;
  country?: string | null;
  ticker?: string | null;
  /** TradingView symbols Binance lists for the ticker, such as BINANCE:METAUSDT.P. */
  instrument_symbols: string[];
  forecast?: string | null;
  previous?: string | null;
  actual?: string | null;
  url?: string | null;
  fetched_at: string;
};

export type CalendarSource = {
  name: string;
  available?: boolean | null;
  error?: string | null;
  events?: number | null;
  fetched_at?: string | null;
};

export type CalendarResponse = { events: CalendarEvent[]; sources: CalendarSource[] };

export type JobStatus = {
  job: string;
  schedule: string;
  started_at?: string | null;
  finished_at?: string | null;
  exit_code?: number | null;
  message?: string | null;
  next_run?: string | null;
};

export type JobsResponse = { jobs: JobStatus[] };

/** One row of job_runs (WL-052). Times are UTC; AI fields are null when the run called no model. */
export type JobRun = {
  id: number;
  job: string;
  trigger?: "scheduled" | "manual" | null;
  started_at: string;
  finished_at?: string | null;
  duration_ms?: number | null;
  exit_code?: number | null;
  message?: string | null;
  ai_provider?: string | null;
  ai_model?: string | null;
  ai_effort?: string | null;
  ai_calls?: number | null;
  tokens_in?: number | null;
  tokens_out?: number | null;
  cost_usd?: number | null;
  status: "running" | "success" | "failed" | "interrupted";
  progress_done?: number | null;
  progress_total?: number | null;
  progress_note?: string | null;
};

export type WatchlistRow = {
  symbol: string;
  quality?: number;
  bias?: Bias;
  confluence?: number;
  setup?: string;
  trade_allowed?: boolean;
  mtf_alignment?: string;
  book_bias?: string | null;
  liq_bias?: string | null;
  price?: number;
  error?: string;
};

export type WatchlistResponse = {
  timeframe: string;
  count: number;
  actionable_count: number;
  rows: WatchlistRow[];
};

/** WL-149: up to 4 stored watchlists of up to 40 pairs, in the order dragged. */
export type WatchlistItem = { id: number; watchlist_id: number; symbol: string; exchange: string; position: number; added_at: string; name?: string | null };
export type WatchlistList = {
  id: number;
  name: string;
  position: number;
  is_open: boolean;
  created_at: string;
  archived_at?: string | null;
  items: WatchlistItem[];
};
export type WatchlistsResponse = { watchlists: WatchlistList[]; max_lists: number; max_items: number };
/** WL-152: 24h is the rolling ticker; the others count from the open of the current candle (UTC); null when there is none yet. */
export type WatchPeriod = "15m" | "4h" | "24h" | "1d" | "1w" | "1M";

export type WatchlistQuote = {
  price: number;
  change_pct: number;
  quote_volume: number;
  market: "spot" | "usdm";
  changes?: Partial<Record<WatchPeriod, number | null>>;
};

export type Stats = {
  total?: number;
  open?: number;
  closed?: number;
  wins?: number;
  losses?: number;
  breakeven?: number;
  expired?: number;
  hit_rate?: number | null;
  avg_r?: number | null;
};

export type JournalEntry = {
  id: string;
  created_at: string;
  symbol: string;
  timeframe?: string;
  side: "Buy" | "Sell";
  setup?: string | null;
  entry?: number | null;
  stop_loss?: number | null;
  take_profit?: number | null;
  status: string;
  r_multiple?: number | null;
};

export type LevelAdviceItem = {
  action?: string;
  price?: number | null;
  reason?: string;
};

export type DecisionLevel = { kind: string; label: string; price: number };

export type SignalReview = {
  at: string;
  price?: number | null;
  unrealized_r?: number | null;
  dist_to_stop_r?: number | null;
  dist_to_target_r?: number | null;
  stance?: string | null;
  ai_stance?: string | null;
  ai_stance_reason?: string | null;
  ai_reasoning?: string | null;
  ai_provider?: string | null;
  ai_status?: string | null;
  ai_error?: string | null;
  summary?: string | null;
  entry_status?: string | null;
  revised_entry?: number | null;
  revised_stop_loss?: number | null;
  revised_take_profit?: number | null;
  levels_changed?: boolean;
  revise_reason?: string | null;
  level_advice?: {
    entry?: LevelAdviceItem;
    stop?: LevelAdviceItem;
    target?: LevelAdviceItem;
  } | null;
  pressure?: { available?: boolean; side?: string | null; score?: number | null; summary?: string | null } | null;
  micro_tape?: {
    available?: boolean;
    summary?: string | null;
    timeframes?: Record<string, { trend?: string | null; rsi?: number | null; score?: number | null }>;
  } | null;
};

export type Signal = {
  id: string;
  created_at: string;
  symbol: string;
  timeframe?: string;
  bias: Bias;
  setup?: string | null;
  entry?: number;
  stop_loss?: number;
  take_profit?: number;
  confluence?: number | null;
  status: string;
  outcome?: string | null;
  r_multiple?: number | null;
  price_at_signal?: number | null;
  hit_price?: number | null;
  hit_at?: string | null;
  notes?: string | null;
  analysis_id?: number | null; // WL-107
  paper?: SignalPaper | null; // WL-108, WL-109
  wallet_id?: number | null; // WL-150: the paper wallet it counts in
  strategy_id?: string | null;
  live_review_json?: SignalReview[] | null;
  multi_analysis_json?: MultiAnalysis | null;
  market_context_json?: Record<string, unknown> | null;
};

export type MarginMode = "isolated" | "cross";

/** One price outcome of a paper futures trade, USDT after fees (WL-109). */
export type PaperResult = { fees: number; pnl: number; move: number; roe: number };

/** A signal as a paper futures trade (WL-108, WL-109): size, liquidation, results, and the live state while it runs. */
export type SignalPaper = {
  margin: number;
  leverage: number;
  margin_mode: MarginMode;
  notional: number;
  qty: number;
  liquidation: number | null;
  liquidated_before_stop: boolean;
  at_target: PaperResult;
  at_stop: PaperResult;
  cross_balance: number | null;
  live?: PaperResult & { price: number; r: number; progress: number | null; towards: "target" | "stop"; liquidated: boolean };
  closed?: PaperResult;
};

/** wallet_id (WL-150): the paper wallet new signals count in, 0 for none. */
export type PaperSettings = { margin: number; leverage: number; margin_mode: MarginMode; cross_balance: number; wallet_id: number };

/** WL-107: a stored analysis; `analysis` is cut to 240 characters in lists. */
export type StoredAnalysis = {
  id: number;
  created_at: string;
  symbol: string;
  exchange: string;
  timeframe: string;
  agent?: string | null;
  provider: string;
  bias?: Bias | null;
  levels: TradeLevels;
  analysis: string;
  price?: number | null;
  confluence?: number | null;
  setup?: string | null;
  signal_id?: string | null;
  chats?: number;
  chat?: { id: number; created_at: string; role: "user" | "assistant"; content: string; provider?: string | null }[];
};

/** [open time ms, open, high, low, close, volume] */
export type Bar = [number, number, number, number, number, number];
export type ChartData = {
  bars: Bar[];
  called_at: number;
  source: string;
  live?: boolean;
  decision_levels?: DecisionLevel[];
};

export type Style = "scalp" | "day" | "swing" | "position" | "hold";

export type TaskState = {
  running: boolean;
  started_at?: string | null;
  finished_at?: string | null;
  error?: string | null;
  progress_done?: number | null;
  progress_total?: number | null;
  progress_note?: string | null;
};

export type DiagramMarker = { x: number; y: number; kind: "entry" | "stop" | "target" | "note"; label: string };
export type DiagramLine = { label: string; kind: "fast" | "slow" | "level"; points: number[][] };
export type DiagramZone = { x0: number; x1: number; y0: number; y1: number; label: string };
export type StrategyDiagram = {
  path: number[][];
  markers: DiagramMarker[];
  lines: DiagramLine[];
  zones: DiagramZone[];
  caption: string;
};

/** A library strategy (WL-031); the diagram is drawn as SVG from these points. */
export type Strategy = {
  id: string;
  name: string;
  family: string;
  styles: Style[];
  setups: string[];
  summary: string;
  entry: string;
  stop: string;
  exit: string;
  works_when: string;
  fails_when: string;
  example: string;
  diagram: StrategyDiagram;
  backtestable: boolean;
  backtest_note?: string | null;
  stop_atr: number;
  target_r: number;
};

export type StrategyNote = { id: number; strategy_id: string; body: string; created_at: string; updated_at: string };

export type BacktestResult = {
  strategy_id: string;
  style: Style;
  coin_group: string;
  trades: number;
  wins: number;
  losses: number;
  expired: number;
  win_rate?: number | null;
  avg_r?: number | null;
  profit_factor?: number | null;
  max_drawdown_r?: number | null;
  total_r?: number | null;
};

export type BacktestRun = {
  id: number;
  started_at: string;
  finished_at?: string | null;
  status: string;
  message?: string | null;
  params?: {
    groups?: Record<string, string[]>;
    fee_per_side?: number;
    slippage_per_side?: number;
    options?: BacktestOptions;
  } | null;
};

/** A backtest set up in the wizard (WL-055, WL-057); empty lists mean all. */
export type BacktestOptions = {
  strategies?: string[];
  styles?: Style[];
  groups?: string[];
  depth?: "quick" | "deep";
  bars?: number | null;
  any_style?: boolean | null;
  coins?: "fixed" | "random" | "custom";
  random_count?: number | null;
  seed?: number | null;
  symbols?: string[];
  agents?: string[];
};

/** The Arena (WL-069): trading agents compete per day. */
export type ArenaStyle = "all" | Style;

export type ArenaAgent = {
  id: string;
  name: string;
  person: string;
  stance: "bull" | "bear" | "both" | "meta";
  summary: string;
  rules: string[];
  total_r?: number | null; // WL-131: Arena total R over every style, from /api/agents
  points?: number | null;
  trades?: number | null;
};

export type ArenaFigures = {
  points: number;
  days_won: number;
  days_traded: number;
  trades: number;
  wins: number;
  win_rate?: number | null;
  total_r?: number | null;
  avg_r?: number | null;
  profit_factor?: number | null;
  avg_daily_r?: number | null;
};

/** WL-076: an agent's figures per bucket (major coins, major stocks, shit coins, your coins). */
export type ArenaGroupRow = ArenaFigures & { bucket: string; label: string };

/** WL-148: an agent's result at 50 USDT isolated margin at one leverage. */
export type ArenaSized = { leverage: number; margin: number; trades: number; pnl_usdt?: number | null; liquidated: number };

export type ArenaStanding = ArenaAgent & {
  groups: ArenaGroupRow[];
  sized?: ArenaSized[];
  place?: number | null;
  points: number;
  days_won: number;
  days_traded: number;
  trades: number;
  wins: number;
  win_rate?: number | null;
  total_r?: number | null;
  avg_r?: number | null;
  profit_factor?: number | null;
  avg_daily_r?: number | null;
};

export type ArenaCell = { trades: number; wins: number; win_rate?: number | null; total_r: number; rank: number; points: number };

export type ArenaDay = { day: string; agents: Record<string, ArenaCell>; winner?: string | null };

export type ArenaRun = {
  id: number;
  started_at: string;
  finished_at?: string | null;
  status: "running" | "done" | "failed";
  message?: string | null;
  progress_done?: number | null;
  progress_total?: number | null;
  progress_note?: string | null;
  options?: string | null;
};

export type ArenaOverview = {
  agents: ArenaAgent[];
  buckets: Record<string, string>;
  history: { first?: string | null; last?: string | null; days: number };
  leaderboard: ArenaStanding[];
  daily: ArenaDay[];
  latest_run?: ArenaRun | null;
  task: TaskState;
};

export type ArenaTrade = {
  id: number;
  agent_id: string;
  style: Style;
  coin_group: string;
  symbol: string;
  side: "Buy" | "Sell";
  entry_time: number;
  entry: number;
  stop: number;
  target?: number | null;
  exit_time: number;
  exit: number;
  exit_reason: "target" | "stop" | "trail" | "expired" | "ladder" | "signal" | "liquidated";
  r_multiple: number;
  leverage?: number | null; // WL-148: the page shows the 10x trades, 50 USDT margin
  pnl_usdt?: number | null;
  entry_day: string;
  exit_day: string;
  score?: number | null;
  note?: string | null;
  strategy?: string | null;
  bucket?: string | null;
  retro?: string | null;
  failure_tag?: string | null;
  mfe_r?: number | null;
  mae_r?: number | null;
  bars?: number | null;
  htf_trend?: "with" | "against" | "flat" | null;
};

export type ArenaSlice = { key: string; trades: number; win_rate: number; total_r: number; avg_r: number };

/** WL-078: why an agent wins and loses, and what it should change. */
export type ArenaReview = {
  agent: string;
  trades: number;
  win_rate?: number;
  total_r?: number;
  gave_back?: number;
  suggestions: string[];
  slices: {
    style?: ArenaSlice[];
    bucket?: ArenaSlice[];
    side?: ArenaSlice[];
    htf_trend?: ArenaSlice[];
    hour?: ArenaSlice[];
    failure_tag?: { key: string; losses: number; lost_r: number }[];
  };
};

/** WL-081: a mock test session and its paper trades. */
export type MockTrade = {
  id: number;
  session_id: number;
  style: Style;
  symbol: string;
  side: "Buy" | "Sell";
  signal_time: number;
  entry?: number | null;
  stop?: number | null;
  target?: number | null;
  opened_at: string;
  status: string;
  exit?: number | null;
  closed_at?: string | null;
  exit_reason?: string | null;
  r_multiple?: number | null;
  retro?: string | null;
};

export type MockSession = {
  id: number;
  created_at: string;
  kind: "strategy" | "agent";
  ref: string;
  mode: "backtest" | "paper";
  styles: Style[];
  symbols: string[];
  ends_at?: string | null;
  status: string;
  run_ref?: number | null;
  message?: string | null;
  stats: { trades: number; open: number; closed: number; win_rate?: number | null; total_r?: number | null };
  trades: MockTrade[];
};

/** WL-079: a professional backtest report. */
export type ProFigures = {
  name: string;
  available: number;
  trades: number;
  win_rate?: number;
  win_rate_ci?: [number, number] | null;
  avg_r?: number;
  avg_r_ci?: [number, number] | null;
  total_r?: number;
  profit_factor?: number | null;
  payoff?: number | null;
  max_dd_r?: number;
  mc_dd95_r?: number | null;
  in_sample?: { trades: number; win_rate?: number; avg_r?: number };
  out_of_sample?: { trades: number; win_rate?: number; avg_r?: number };
  walk_forward?: { positive: number; folds: { trades: number; win_rate?: number; avg_r?: number }[] };
};

export type ProReport = { id: number; created_at: string; run_id?: number | null; params: { sample: number; seed: number }; agents: Record<string, ProFigures> };

/** WL-094, WL-095: the Arena graphs and agent map. */
export type ArenaFigureSet = { trades: number; wins: number; win_rate?: number | null; total_r: number; avg_r?: number | null };
export type ArenaCharts = {
  series: { days: string[]; r: Record<string, (number | null)[]> };
  /** WL-100: per agent and style, [day, trades, wins, R] for each close day, oldest first. */
  styles: Record<string, Partial<Record<Style, [string, number, number, number][]>>>;
  matrix: (ArenaFigureSet & { agent_id: string; style: Style })[];
  strategies: Record<string, (ArenaFigureSet & { key: string })[]>;
  filters: Record<string, number>;
};

/** WL-075, WL-077: Arena filters; dates are PKT close days, YYYY-MM-DD. */
export type ArenaFilters = {
  agents?: string[];
  date_from?: string;
  date_to?: string;
  style?: ArenaStyle;
  bucket?: string;
  symbol?: string;
  strategy?: string;
  side?: "Buy" | "Sell" | "";
  outcome?: "win" | "loss" | "";
};

function arenaQuery(f: ArenaFilters): string {
  const q = new URLSearchParams();
  if (f.agents?.length) q.set("agents", f.agents.join(","));
  for (const k of ["date_from", "date_to", "style", "bucket", "symbol", "strategy", "side", "outcome"] as const) {
    const v = f[k];
    if (v) q.set(k, v);
  }
  return q.toString();
}

export type BacktestChoices = {
  styles: Record<string, { interval: string; horizon: number }>;
  groups: Record<string, string[]>;
  tiers: string[];
  depths: Record<string, { bars: number; per_group: number | null }>;
  max_bars: number;
  max_random_per_tier: number;
};

/** A kept backtest run with its state and progress (WL-053). */
export type BacktestRunState = {
  id: number;
  started_at: string;
  finished_at?: string | null;
  status: string;
  state: "running" | "success" | "failed" | "interrupted";
  message?: string | null;
  progress_done?: number | null;
  progress_total?: number | null;
  progress_note?: string | null;
  options?: BacktestOptions | null;
};

export type BacktestResponse = {
  run: BacktestRun | null;
  runs: BacktestRunState[];
  results: BacktestResult[];
  failures: Record<string, Record<string, number>>;
  /** Set when the results are every finished run combined (WL-065). */
  pooled?: { runs: number; trades: number } | null;
  task: TaskState;
  min_trades: number;
  choices: BacktestChoices;
};

export type BacktestTrade = {
  id: number;
  strategy_id: string;
  style: Style;
  coin_group: string;
  symbol: string;
  side: "Buy" | "Sell";
  entry_time: number;
  entry: number;
  stop: number;
  target: number;
  exit_time?: number | null;
  exit?: number | null;
  outcome: "win" | "loss" | "expired";
  r_multiple: number;
  failure_tag?: string | null;
};

/** Best-fitting strategies for the analysed pair (WL-034), in market.strategy_fit. */
export type StrategyFitItem = {
  id: string;
  name: string;
  fit: number;
  firing: boolean;
  side?: "Buy" | "Sell" | null;
  win_rate?: number | null;
  win_rate_reason?: string | null;
  trades: number;
  avg_r?: number | null;
  coin_group?: string | null;
  why: string;
};

export type StrategyFit = {
  available?: boolean;
  style?: Style;
  coin_group?: string;
  backtested?: boolean;
  /** Desk ranking list; absent when market.strategy_fit is a pack-fit blob. */
  strategies?: StrategyFitItem[];
  error?: string | null;
  /** Pack-fit fields (multi-analyze / named packs). */
  score?: number;
  bias?: string;
  confidence?: number;
  trade_allowed?: boolean;
  summary?: string;
};

export type Pick = {
  day: string;
  style: Style;
  rank: number;
  symbol: string;
  market: string;
  type: string;
  coin_group: string;
  side: "Buy" | "Sell";
  entry: number;
  stop: number;
  target: number;
  rr: number;
  score: number;
  setup?: string | null;
  strategy_id?: string | null;
  strategy_name?: string | null;
  strategy_firing: boolean;
  strategy_win_rate?: number | null;
  strategy_trades?: number | null;
  corr_btc?: number | null;
  beta_btc?: number | null;
  corr_eth?: number | null;
  beta_eth?: number | null;
  volume_usd?: number | null;
  created_at: string;
  /** Score parts (trend, momentum, strength, volume, strategy) and RSI, ADX. */
  details?: { parts?: Record<string, number>; rsi?: number; adx?: number; firing?: string[] } | null;
  paper?: PickPaper | null;
};

/** The paper trade opened from a pick (WL-059). */
export type PickPaper = {
  status: "open" | "win" | "loss" | "expired";
  r_multiple?: number | null;
  exit?: number | null;
  opened_at?: string | null;
  closed_at?: string | null;
};

/** One stored day of picks and how its paper trades did (WL-059). */
export type PicksDay = {
  day: string;
  picks: number;
  traded: number;
  open?: number | null;
  won?: number | null;
  lost?: number | null;
  expired?: number | null;
  total_r?: number | null;
};

export type PicksResponse = {
  day: string | null;
  styles: Partial<Record<Style, Pick[]>>;
  generated_at?: string | null;
  lowcap_max?: number | null;
  days: PicksDay[];
  task: TaskState;
};

/** WL-128: the styles the Arena agents' own lists cover (position is the daily chart, hold included). */
export type AgentPickStyle = "scalp" | "day" | "swing" | "position";

/** One pick on an Arena agent's own Top 10 (WL-128). */
export type AgentPick = {
  day: string;
  agent_id: string;
  style: AgentPickStyle;
  rank: number;
  symbol: string;
  market: string;
  type: string;
  coin_group: string;
  side: "Buy" | "Sell";
  entry: number;
  stop: number;
  target?: number | null; // null: a trailing exit
  rr?: number | null;
  trail?: number | null;
  strategy?: string | null;
  note?: string | null;
  bars_ago: number;
  agent_trades?: number | null;
  agent_win_rate?: number | null; // 0 to 1
  agent_avg_r?: number | null;
  volume_usd?: number | null;
  created_at: string;
};

export type AgentStanding = { trades: number; wins: number; win_rate?: number | null; total_r: number; avg_r?: number | null; points: number };

export type AgentPicksAgent = {
  id: string;
  name: string;
  person: string;
  stance: "bull" | "bear" | "both" | "meta";
  summary: string;
  rules: string[];
  styles: AgentPickStyle[];
  standing: Partial<Record<AgentPickStyle, AgentStanding>>;
  picks: Partial<Record<AgentPickStyle, AgentPick[]>>;
};

export type AgentPicksResponse = {
  day: string | null;
  days: string[];
  generated_at?: string | null;
  styles: AgentPickStyle[];
  agents: AgentPicksAgent[];
};

export type PickHistoryRow = {
  day: string;
  style: Style;
  rank: number;
  symbol: string;
  side: "Buy" | "Sell";
  entry: number;
  stop: number;
  target: number;
  rr: number;
  score: number;
  setup?: string | null;
  strategy_name?: string | null;
  paper_status?: PickPaper["status"] | null;
  paper_r?: number | null;
  paper_exit?: number | null;
  paper_closed_at?: string | null;
};

export type PaperTrade = {
  id: number;
  pick_day: string;
  style: Style;
  symbol: string;
  market: string;
  coin_group: string;
  side: "Buy" | "Sell";
  strategy_id?: string | null;
  entry: number;
  stop: number;
  target: number;
  opened_at: string;
  expires_at: string;
  status: "open" | "win" | "loss" | "expired";
  exit?: number | null;
  closed_at?: string | null;
  r_multiple?: number | null;
  last_checked?: string | null;
};

/** A leveraged paper position (WL-061). */
export type Position = {
  id: number;
  account: string;
  wallet_id?: number | null;
  symbol: string;
  market: string;
  side: "Buy" | "Sell";
  entry: number;
  stop?: number | null;
  target?: number | null;
  margin: number;
  leverage: number;
  fee_rate: number;
  mmr: number;
  qty: number;
  liquidation: number;
  pick_day?: string | null;
  style?: string | null;
  opened_at: string;
  status: "open" | "win" | "loss" | "liquidated" | "closed";
  exit?: number | null;
  closed_at?: string | null;
  fees?: number | null;
  pnl?: number | null;
  roe?: number | null;
  last_checked?: string | null;
  notes?: string | null;
  open_fee?: number | null;
  archived_at?: string | null;
  live_price?: number | null;
  unrealized?: { fees: number; pnl: number; roe: number } | null;
  margin_mode?: MarginMode; // WL-110
  cross_balance?: number | null;
  signal_id?: string | null; // WL-150: account "signal", a signal's paper trade in a paper wallet
};

/** Wallets for trades opened on Binance by hand and booked here (WL-063). */
/** paper (WL-150): simulated; takes paper positions and signal paper trades, no hand bookings. */
export type WalletKind = "futures" | "spot" | "paper";

export type WalletSummary = PositionsResponse["stats"] & {
  starting_balance: number;
  deposits: number;
  withdrawals: number;
  balance: number;
  equity?: number | null;
};

export type Wallet = {
  id: number;
  name: string;
  exchange: string;
  kind: WalletKind;
  currency: string;
  starting_balance: number;
  created_at: string;
  archived_at?: string | null;
  notes?: string | null;
  summary?: WalletSummary | null;
};

export type WalletEntry = {
  id: number;
  wallet_id: number;
  kind: "deposit" | "withdrawal";
  amount: number;
  at: string;
  archived_at?: string | null;
  notes?: string | null;
};

export type WalletHistoryPoint = {
  at: string;
  kind: "start" | "deposit" | "withdrawal" | "trade";
  amount?: number | null;
  balance: number;
  ref?: number | null;
  symbol?: string | null;
  source?: "wallet" | "paper" | "signal" | null; // WL-150
};

/** WL-151: every wallet day by day on one shared axis; balance is null before the wallet starts. */
export type WalletPairResult = { symbol: string; trades: number; won: number; lost: number; pnl: number; fees: number };
export type WalletMonth = { month: string; trades: number; won: number; lost: number; pnl: number; deposits: number; withdrawals: number; end_balance: number };
export type WalletSeries = {
  id: number;
  name: string;
  kind: WalletKind;
  currency: string;
  archived_at?: string | null;
  balance: (number | null)[];
  pnl: number[];
  deposits: number[];
  withdrawals: number[];
  trades: number[];
  won: number[];
  by_pair: WalletPairResult[];
  by_month: WalletMonth[];
};
export type WalletCharts = { days: string[]; wallets: WalletSeries[] };

export type WalletDetail = {
  wallet: Wallet;
  trades: Position[];
  entries: WalletEntry[];
  history: WalletHistoryPoint[];
  price_error?: string | null;
};

export type WalletTradeBook = {
  symbol: string;
  side: "Buy" | "Sell";
  entry: number;
  qty?: number | null;
  margin?: number | null;
  leverage: number;
  mmr?: number;
  open_fee: number;
  stop?: number | null;
  target?: number | null;
  opened_at?: string | null;
  pick_day?: string | null;
  style?: string | null;
  notes?: string | null;
};

export type PositionOpen = {
  symbol: string;
  market: string;
  side: "Buy" | "Sell";
  stop?: number | null;
  target?: number | null;
  margin: number;
  leverage: number;
  fee_rate: number;
  mmr: number;
  pick_day?: string | null;
  style?: string | null;
  margin_mode?: MarginMode; // WL-110
  cross_balance?: number | null;
  wallet_id?: number | null; // WL-150: a paper wallet
};

export type PositionsResponse = {
  positions: Position[];
  stats: {
    total: number;
    open: number;
    won: number;
    lost: number;
    liquidated: number;
    win_rate?: number | null;
    realized_pnl?: number | null;
    fees?: number | null;
    unrealized_pnl?: number | null;
  };
  price_error?: string | null;
};

export type PaperStats = {
  total: number;
  open: number;
  won: number;
  lost: number;
  expired: number;
  win_rate?: number | null;
  total_r?: number | null;
};

export type PaperResponse = {
  trades: PaperTrade[];
  stats: PaperStats;
  by_style: Record<string, PaperStats>;
  by_strategy: Record<string, PaperStats>;
};

export type HypeEntry = {
  day: string;
  rank: number;
  symbol: string;
  base: string;
  name?: string | null;
  on_binance: boolean;
  hype_score: number;
  sources: { source: string; rank?: number | null; detail?: string | null }[];
  mentions?: number | null;
  volume_usd?: number | null;
  volume_change_pct?: number | null;
  oi_change_pct?: number | null;
  price_change_pct?: number | null;
  market_cap_rank?: number | null;
  coin_group?: string | null;
  confluence?: number | null;
  side?: string | null;
  rank_yesterday?: number | null;
  score_change?: number | null;
};

export type HypeSource = { name: string; available?: boolean | null; error?: string | null; items?: number | null; fetched_at?: string | null };

export type HypeResponse = { day: string | null; entries: HypeEntry[]; sources: HypeSource[]; task: TaskState };

export type FinancialQuarter = {
  quarter: string;
  partial: boolean;
  revenue?: number | null;
  net_income?: number | null;
  eps_diluted?: number | null;
  cash?: number | null;
  return_pct?: number | null;
  high?: number | null;
  low?: number | null;
  close?: number | null;
  quote_volume?: number | null;
  fees?: number | null;
  protocol_revenue?: number | null;
  sources: string[];
  qoq: Record<string, number | null>;
};

export type Wall = { price: number; usd: number; qty: number; distance_pct: number; x_median?: number | null };
export type Walls = { sell: Wall[]; buy: Wall[] };
export type DeepDiveVenue = {
  label: string;
  available: boolean;
  error?: string | null;
  mid?: number | null;
  bid_usd?: number | null;
  ask_usd?: number | null;
  walls?: Walls;
};
export type WallChange = { side: "sell" | "buy"; price: number; change: "new" | "gone" | "grown" | "shrunk"; usd?: number; usd_before?: number; pct?: number };
export type SourceState = { available?: boolean; error?: string | null };
export type DeepDive = {
  id: number;
  created_at: string;
  symbol: string;
  base: string;
  mid?: number | null;
  venues: Record<string, DeepDiveVenue>;
  walls: Walls;
  changes: WallChange[];
  previous_at?: string | null;
  token: SourceState & {
    id?: string;
    name?: string | null;
    rank?: number | null;
    market_cap?: number | null;
    fdv?: number | null;
    volume_24h?: number | null;
    circulating_supply?: number | null;
    total_supply?: number | null;
    max_supply?: number | null;
    ath_change_pct?: number | null;
    change_7d_pct?: number | null;
    change_30d_pct?: number | null;
    categories?: string[];
    sentiment_up_pct?: number | null;
  };
  derivatives: SourceState & { funding_pct?: number | null; open_interest_usd?: number | null; top_long_short?: number | null };
  holders: SourceState;
  unlocks: SourceState;
  settings: { window_pct: number; bin_pct: number; wall_x: number };
};
export type DeepDiveHistory = {
  latest: DeepDive | null;
  history: { id: number; created_at: string; mid?: number | null; sell_usd: number; buy_usd: number }[];
};

export type FinancialsResponse = {
  symbol: string;
  kind: "stock" | "etf" | "crypto" | "other";
  ticker?: string | null;
  protocol?: string | null;
  fetched_at: string;
  sources: Record<string, { available?: boolean; error?: string }>;
  quarters: FinancialQuarter[];
};

function apiError(body: string): string {
  try {
    const j = JSON.parse(body) as { detail?: unknown };
    if (typeof j.detail === "string") return j.detail;
    if (Array.isArray(j.detail)) return j.detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join("; ");
  } catch {
    /* not JSON */
  }
  return body;
}

async function request<T>(path: string, init?: { method?: string; body?: unknown }): Promise<T> {
  const res = await fetch(path, {
    method: init?.method ?? "GET",
    headers: init?.body === undefined ? undefined : { "Content-Type": "application/json" },
    body: init?.body === undefined ? undefined : JSON.stringify(init.body),
  });
  const text = await res.text();
  if (!res.ok) throw new Error(apiError(text) || res.statusText);
  return (text ? JSON.parse(text) : null) as T;
}

type Pair = { symbol: string; exchange: string; timeframe: string };

export const api = {
  health: () => request<HealthResponse>("/api/health"),
  analyze: (
    p: Pair & {
      agent?: string | null;
      strategy_id?: string;
      optimize_mode?: OptimizeMode | string;
      guard_mode?: GuardMode | string;
      custom_prompt?: string | null;
    },
  ) => request<AnalyzeResponse>("/api/analyze", { method: "POST", body: p }),
  packs: () => request<{ packs: AnalysisPack[]; multi_ids: string[]; default: string }>("/api/packs"),
  agents: () => request<{ agents: ArenaAgent[]; default: string }>("/api/agents"),
  chat: (p: Pair & { message: string; history: ChatMessage[]; agent?: string | null; analysis_id?: number | null }) =>
    request<ChatResponse>("/api/chat", { method: "POST", body: p }),
  searchSymbols: (q: string, exchange: string) =>
    request<{ results: SymbolResult[] }>(
      `/api/symbols/search?q=${encodeURIComponent(q)}&exchange=${encodeURIComponent(exchange)}&limit=20`,
    ),
  /** WL-097: every trading instrument of one catalogue type (perps first), for the search's empty state. */
  symbolsByType: (type: InstrumentType) =>
    request<{ results: SymbolResult[] }>(`/api/symbols/search?type=${encodeURIComponent(type)}&limit=40`),
  pulse: () => request<PulseResponse>("/api/pulse"),
  calendar: (days: number, kind: CalendarKind | "") =>
    request<CalendarResponse>(`/api/calendar?days=${String(days)}&kind=${encodeURIComponent(kind)}`),
  jobs: () => request<JobsResponse>("/api/jobs"),
  jobRuns: (job = "") => request<{ runs: JobRun[] }>(`/api/jobs/runs?limit=200&job=${encodeURIComponent(job)}`),
  scoreWatchlist: (timeframe: string, symbols: string[] = []) =>
    request<WatchlistResponse>(`/api/watchlist/score?timeframe=${encodeURIComponent(timeframe)}&symbols=${encodeURIComponent(symbols.join(","))}`),
  watchlists: (includeArchived = false) => request<WatchlistsResponse>(`/api/watchlists${includeArchived ? "?include_archived=true" : ""}`),
  createWatchlist: (name: string, isOpen = false) => request<WatchlistList>("/api/watchlists", { method: "POST", body: { name, is_open: isOpen } }),
  updateWatchlist: (id: number, body: { name?: string; is_open?: boolean }) => request<WatchlistList>(`/api/watchlists/${String(id)}`, { method: "PATCH", body }),
  archiveWatchlist: (id: number, restore = false) =>
    request<WatchlistList>(`/api/watchlists/${String(id)}/archive${restore ? "?restore=true" : ""}`, { method: "POST" }),
  orderWatchlists: (ids: number[]) => request<WatchlistsResponse>("/api/watchlists/order", { method: "PUT", body: { ids } }),
  addWatchItem: (id: number, symbol: string, exchange = "BINANCE") =>
    request<WatchlistList>(`/api/watchlists/${String(id)}/items`, { method: "POST", body: { symbol, exchange } }),
  removeWatchItem: (id: number, itemId: number) => request<WatchlistList>(`/api/watchlists/${String(id)}/items/${String(itemId)}/archive`, { method: "POST" }),
  orderWatchItems: (id: number, ids: number[]) => request<WatchlistList>(`/api/watchlists/${String(id)}/order`, { method: "PUT", body: { ids } }),
  watchQuotes: (symbols: string[]) =>
    request<{ quotes: Record<string, WatchlistQuote>; error?: string | null }>(`/api/watchlists/quotes?symbols=${encodeURIComponent(symbols.join(","))}`),
  journal: () => request<{ entries: JournalEntry[]; stats: Stats }>("/api/journal?limit=100"),
  addJournal: (body: Record<string, unknown>) => request<JournalEntry>("/api/journal", { method: "POST", body }),
  closeJournal: (id: string, status: string, exit_price: number | null) =>
    request<JournalEntry>(`/api/journal/${encodeURIComponent(id)}/close`, { method: "POST", body: { status, exit_price } }),
  deleteJournal: (id: string) => request<{ ok: boolean }>(`/api/journal/${encodeURIComponent(id)}`, { method: "DELETE" }),
  signals: (opts?: { kind?: string; strategy_id?: string; symbol?: string; limit?: number }) => {
    const q = new URLSearchParams();
    q.set("limit", String(opts?.limit ?? 100));
    if (opts?.kind) q.set("kind", opts.kind);
    if (opts?.strategy_id) q.set("strategy_id", opts.strategy_id);
    if (opts?.symbol) q.set("symbol", opts.symbol);
    return request<{ signals: Signal[]; stats: Stats; price_error?: string | null }>(`/api/signals?${q.toString()}`);
  },
  signal: (id: string) => request<{ signal: Signal }>(`/api/signals/${encodeURIComponent(id)}`),
  deleteSignal: (id: string) => request<{ ok: boolean }>(`/api/signals/${encodeURIComponent(id)}`, { method: "DELETE" }),
  reviewSignal: (id: string) =>
    request<{ signal: Signal; review: SignalReview | null; stats: Stats }>(`/api/signals/${encodeURIComponent(id)}/review`, {
      method: "POST",
    }),
  reviewOpenSignals: () =>
    request<{ reviewed: number; open: number; errors: string[]; stats: Stats }>("/api/signals/review", { method: "POST" }),
  signalsDashboard: () => request<Record<string, unknown>>("/api/signals/dashboard"),
  /** WL-109: change one signal's paper margin, leverage or margin mode. */
  updateSignal: (id: string, body: { margin?: number; leverage?: number; margin_mode?: MarginMode; wallet_id?: number }) =>
    request<{ signal: Signal }>(`/api/signals/${encodeURIComponent(id)}`, { method: "PATCH", body }),
  signalChart: (id: string) => request<ChartData>(`/api/signals/${encodeURIComponent(id)}/chart`),
  paperSettings: () => request<PaperSettings>("/api/paper-settings"),
  savePaperSettings: (body: Partial<PaperSettings>) => request<PaperSettings>("/api/paper-settings", { method: "PUT", body }),
  /** WL-107: stored analyses and their chats. */
  analyses: (limit: number, offset: number, symbol = "", kind: "all" | "watch" = "all") =>
    request<{ analyses: StoredAnalysis[]; total: number }>(
      `/api/analyses?limit=${String(limit)}&offset=${String(offset)}&symbol=${encodeURIComponent(symbol)}&kind=${kind}`,
    ),
  analysis: (id: number) => request<StoredAnalysis>(`/api/analyses/${String(id)}`),
  analysisChart: (id: number) => request<ChartData>(`/api/analyses/${String(id)}/chart`),
  verifySignals: () =>
    request<{ checked: number; updated: number; stats: Stats }>("/api/signals/verify?only_open=true&limit=50", {
      method: "POST",
    }),
  verifySignal: (id: string) =>
    request<{ signal: Signal; stats: Stats }>(`/api/signals/${encodeURIComponent(id)}/verify`, { method: "POST" }),
  strategies: () => request<{ strategies: Strategy[]; note_counts: Record<string, number> }>("/api/strategies"),
  notes: (strategyId: string) =>
    request<{ notes: StrategyNote[] }>(`/api/strategies/${encodeURIComponent(strategyId)}/notes`),
  addNote: (strategyId: string, body: string) =>
    request<StrategyNote>(`/api/strategies/${encodeURIComponent(strategyId)}/notes`, { method: "POST", body: { body } }),
  updateNote: (id: number, body: string) => request<StrategyNote>(`/api/notes/${String(id)}`, { method: "PUT", body: { body } }),
  deleteNote: (id: number) => request<{ ok: boolean }>(`/api/notes/${String(id)}`, { method: "DELETE" }),
  backtests: (runId?: number | null, pooled = false) =>
    request<BacktestResponse>(pooled ? "/api/backtests?pooled=true" : runId ? `/api/backtests?run_id=${String(runId)}` : "/api/backtests"),
  backtestTrades: (strategy: string, style: string, group: string, runId?: number | null, pooled = false) =>
    request<{ trades: BacktestTrade[] }>(
      `/api/backtests/trades?strategy=${encodeURIComponent(strategy)}&style=${encodeURIComponent(style)}&group=${encodeURIComponent(group)}&limit=500${pooled ? "&pooled=true" : runId ? `&run_id=${String(runId)}` : ""}`,
    ),
  runBacktest: (options?: BacktestOptions) => request<TaskState>("/api/backtests/run", { method: "POST", body: options ?? {} }),
  picks: (includeStocks: boolean, day?: string | null) =>
    request<PicksResponse>(`/api/picks?include_stocks=${String(includeStocks)}${day ? `&day=${encodeURIComponent(day)}` : ""}`),
  pickHistory: (symbol: string) =>
    request<{ symbol: string; rows: PickHistoryRow[] }>(`/api/picks/history?symbol=${encodeURIComponent(symbol)}`),
  agentPicks: (day?: string | null) => request<AgentPicksResponse>(`/api/picks/agents${day ? `?day=${encodeURIComponent(day)}` : ""}`),
  runPicks: () => request<TaskState>("/api/picks/run", { method: "POST" }),
  paper: () => request<PaperResponse>("/api/paper"),
  checkPaper: () =>
    request<{ checked: number; closed: number; errors: number; positions?: { checked: number; closed: number; errors: number } }>("/api/paper/check", {
      method: "POST",
    }),
  positions: () => request<PositionsResponse>("/api/positions"),
  openPosition: (body: PositionOpen) => request<Position>("/api/positions", { method: "POST", body }),
  closePosition: (id: number, price?: number) => request<Position>(`/api/positions/${String(id)}/close`, { method: "POST", body: { price: price ?? null } }),
  wallets: (includeArchived = false) => request<{ wallets: Wallet[]; price_error?: string | null }>(`/api/wallets${includeArchived ? "?include_archived=true" : ""}`),
  wallet: (id: number) => request<WalletDetail>(`/api/wallets/${String(id)}`),
  walletCharts: (includeArchived = false) => request<WalletCharts>(`/api/wallets/charts?include_archived=${String(includeArchived)}`),
  createWallet: (body: { name: string; kind: WalletKind; exchange?: string; starting_balance: number; notes?: string | null }) =>
    request<Wallet>("/api/wallets", { method: "POST", body }),
  updateWallet: (id: number, body: { name?: string; notes?: string | null }) => request<Wallet>(`/api/wallets/${String(id)}`, { method: "PATCH", body }),
  archiveWallet: (id: number, restore = false) => request<Wallet>(`/api/wallets/${String(id)}/archive${restore ? "?restore=true" : ""}`, { method: "POST" }),
  addWalletEntry: (id: number, body: { kind: WalletEntry["kind"]; amount: number; at?: string | null; notes?: string | null }) =>
    request<WalletEntry>(`/api/wallets/${String(id)}/entries`, { method: "POST", body }),
  archiveWalletEntry: (id: number, entryId: number) => request<WalletEntry>(`/api/wallets/${String(id)}/entries/${String(entryId)}/archive`, { method: "POST" }),
  bookTrade: (id: number, body: WalletTradeBook) => request<Position>(`/api/wallets/${String(id)}/trades`, { method: "POST", body }),
  closeWalletTrade: (id: number, posId: number, body: { exit?: number | null; close_fee: number; closed_at?: string | null; liquidated: boolean }) =>
    request<Position>(`/api/wallets/${String(id)}/trades/${String(posId)}/close`, { method: "POST", body }),
  archiveWalletTrade: (id: number, posId: number) => request<Position>(`/api/wallets/${String(id)}/trades/${String(posId)}/archive`, { method: "POST" }),
  hype: () => request<HypeResponse>("/api/hype"),
  arena: (style: ArenaStyle = "all", days = 30, f: ArenaFilters = {}) =>
    request<ArenaOverview>(`/api/arena?${arenaQuery({ ...f, style })}&days=${String(days)}`),
  arenaCharts: (style: ArenaStyle = "all", f: ArenaFilters = {}) => request<ArenaCharts>(`/api/arena/charts?${arenaQuery({ ...f, style })}`),
  arenaSearch: (f: ArenaFilters, limit = 100, offset = 0, sort: { key: string; dir: "asc" | "desc" } | null = null) =>
    request<{ trades: ArenaTrade[]; total: number; limit: number; offset: number }>(
      `/api/arena/trades?${arenaQuery(f)}&limit=${String(limit)}&offset=${String(offset)}${sort ? `&sort=${encodeURIComponent(sort.key)}&order=${sort.dir}` : ""}`,
    ),
  backtestSearch: (f: Record<string, string>, limit = 50, offset = 0) => {
    const q = new URLSearchParams(Object.entries(f).filter(([, v]) => v));
    q.set("limit", String(limit));
    q.set("offset", String(offset));
    return request<{ trades: BacktestTrade[]; total: number }>(`/api/backtests/search?${q.toString()}`);
  },
  arenaReview: (agent: string, f: ArenaFilters = {}) =>
    request<ArenaReview>(`/api/arena/review?${arenaQuery({ ...f, agents: [] })}&agent=${encodeURIComponent(agent)}`),
  startMock: (body: Record<string, unknown>) => request<MockSession>("/api/mock", { method: "POST", body }),
  mocks: () => request<{ sessions: MockSession[] }>("/api/mock"),
  checkMocks: () => request<{ scan: { opened: number }; check: { closed: number } }>("/api/mock/check", { method: "POST" }),
  stopMock: (id: number) => request<MockSession>(`/api/mock/${String(id)}/stop`, { method: "POST" }),
  proReports: () => request<{ reports: ProReport[] }>("/api/arena/reports"),
  runPro: (target = 30000, maxCoins = 150) => request<TaskState>(`/api/arena/pro?target=${String(target)}&max_coins=${String(maxCoins)}`, { method: "POST" }),
  arenaLessons: () =>
    request<{ lessons: { id: number; created_at: string; agent_id: string; kind: string; text: string }[]; filters: { agent_id: string; text: string; active: number }[]; digest: string }>(
      "/api/arena/lessons?limit=200",
    ),
  arenaTrades: (agent: string, style: ArenaStyle = "all") =>
    request<{ trades: ArenaTrade[] }>(`/api/arena/trades?agent=${encodeURIComponent(agent)}&style=${style}&limit=100`),
  runArena: (options?: BacktestOptions) => request<TaskState>("/api/arena/run", { method: "POST", body: options ?? {} }),
  runHype: () => request<TaskState>("/api/hype/run", { method: "POST" }),
  financials: (symbol: string, refresh = false) =>
    request<FinancialsResponse>(`/api/financials/${encodeURIComponent(symbol)}?refresh=${String(refresh)}`),
  deepDive: (symbol: string) => request<DeepDiveHistory>(`/api/deepdive/${encodeURIComponent(symbol)}`),
  runDeepDive: (symbol: string) => request<DeepDive>(`/api/deepdive/${encodeURIComponent(symbol)}`, { method: "POST" }),
};
