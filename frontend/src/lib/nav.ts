/** Routes, timeframes and labels shared by the shell, the search and the pages. */
export const PAGES = {
  desk: "Desk",
  watchlist: "Watchlists",
  calendar: "Calendar",
  picks: "Top 10 picks",
  hype: "Hype radar",
  strategies: "Strategies",
  backtests: "Backtests",
  arena: "Arena",
  journal: "Journal",
  signals: "Signals",
  paper: "Paper trades",
  wallets: "Wallets",
  jobruns: "Job runs",
} as const;
export type PageKey = keyof typeof PAGES;

export const TIMEFRAMES = ["15m", "1h", "4h", "1D", "1W", "1M"] as const; // 1W and 1M: WL-113
export const EXCHANGES = ["BINANCE", "KUCOIN", "BYBIT", "MEXC"] as const;

export const PROVIDER_LABEL: Record<string, string> = {
  claude: "Claude API",
  claude_code: "Claude subscription",
  cursor: "Cursor",
  openai: "OpenAI",
  offline: "No AI",
  none: "No AI",
};
