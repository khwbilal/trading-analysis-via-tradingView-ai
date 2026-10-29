# User interface

One portal: **React 19 + MUI 9** in `frontend/` (Vite, strict TypeScript), decided in [decision 0008](decisions/0008-react-mui-only.md). FastAPI serves the production build from `frontend/dist` at `/`; `start.ps1` and `start.sh` run `npm run build` before they start the API (WL-047). For development, `npm run dev` serves on `http://localhost:5173` with `/api` proxied to `:8000`. When `frontend/dist` is missing, `/` answers 503 with a line that says to build it.

The old no-build UI (`backend/app/static/`) was removed in WL-047 phase C. A copy is in the session scratchpad backup only.

Its visual language is adapted from the **Unefy portal design system** (Portal Design Guide v2.x): Inter type, a single cool-grey neutral ramp, a separate primary blue for interactive elements, a collapsible rail, a 52px top bar with global search, KPI strips, and widget cards.

## Files

| Path | Holds |
|---|---|
| `src/theme.ts` | The one MUI theme: light and dark palettes, type, radius, component defaults. Every colour lives here. |
| `src/main.tsx`, `src/App.tsx` | Theme provider, hash routing, shared pair and timeframe state |
| `src/lib/nav.ts` | Page keys and labels, timeframes, exchanges, provider labels |
| `src/lib/format.ts` | Number, price, percent, R and date formatters; style and coin group labels |
| `src/lib/useTask.ts` | Loads a page's data and polls while its background task (backtest, picks, hype) runs |
| `src/components/Shell.tsx` | Rail (Drawer), top bar (AppBar), theme menu, Ctrl K |
| `src/components/ui.tsx` | `Na`, `V`, `Num`, `Pill`, `BiasPill`, `StatusPill`, `KpiStrip`, `SectionCard`, `DataTable`, `ActionButton`, `PageHeader`, `EmptyState` |
| `src/components/feedback.tsx` | Toasts and the shared confirm and input dialog (`useFeedback().ask`) |
| `src/components/PairSearch.tsx` | MUI Autocomplete over the instrument catalogue |
| `src/components/DeskCards.tsx` | Desk cards: levels, confluence, setup, flow, liquidity, correlation, strategy fit |
| `src/components/FinancialsCard.tsx` | Last 8 quarters on the desk ([Financials](features/financials.md)) |
| `src/components/StrategyDiagram.tsx` | Draws a strategy's diagram data as SVG with theme colours |
| `src/components/ArenaCharts.tsx`, `AgentMap.tsx` | Arena graphs and agent map: hand-drawn SVG and HTML, theme colours, no chart library |
| `src/components/PulseStrip.tsx`, `JobsStatus.tsx` | BTC and ETH pulse; job health in the rail foot |
| `src/pages/*.tsx` | One file per page |

## Pages

| Page | Route | Contents |
|---|---|---|
| Desk | `#/desk` | Pulse strip, KPI strip, chart with structure levels, insight cards, best strategies, correlation, financials, Analyst chat |
| Watchlist | `#/watchlist` | Scored table ([feature](features/watchlist.md)) |
| Calendar | `#/calendar` | Events for 7 days in PKT ([feature](features/calendar.md)) |
| Top 10 picks | `#/picks` | Three tabs (scalping, day, swing), stocks toggle ([feature](features/picks-and-paper-trades.md)) |
| Hype radar | `#/hype` | Ranked coins with sources and confluence ([feature](features/hype-radar.md)) |
| Strategies | `#/strategies` | Library cards; a dialog with diagram, rules, backtest and notes ([feature](features/strategies-and-backtests.md)) |
| Backtests | `#/backtests` | Results per strategy, style and coin group; trades per row; New backtest wizard and older runs (WL-055) ([feature](features/strategies-and-backtests.md)) |
| Journal | `#/journal` | Trades with Win, Loss, BE, Skip, Delete ([feature](features/journal.md)) |
| Signals | `#/signals` | Archived signals with Verify ([feature](features/signals.md)) |
| Paper trades | `#/paper` | Simulated trades from the picks with start, end and duration (WL-056), stats by style and strategy ([feature](features/picks-and-paper-trades.md)) |
| Job runs | `#/jobruns` | Every scheduled job run: UTC times, trigger, duration, result and AI usage ([scheduled jobs](scheduled-jobs.md#seeing-runs)) |

Pages stay mounted after their first visit, so the desk keeps its plan and chat while you browse. The rail groups them: Desk, Watchlist, Calendar; **Daily** (picks, hype radar); **Research** (strategies, backtests); **Track record** (journal, signals, paper trades); **Reports** (job runs). It folds from 224px to 64px icons; below 900px it is a drawer opened by the menu button. The rail foot shows job health (WL-048) and the AI provider.

## Keyboard

| Keys | Action |
|---|---|
| Ctrl K / Cmd K | Focus the pair search (or open it on a small screen) |
| Up, Down, Enter, Esc | Move, open, close in the search |
| Enter / Shift+Enter | Send / new line in the chat |
| Esc | Close a dialog |

## Theme

- `theme.ts` uses `createTheme` with CSS variables and two colour schemes; the mode (system, light, dark) is stored by MUI under `cca_theme`, and `index.html` applies it before first paint.
- Custom palette keys: `brand` (logo only), `surface.*` (tinted backgrounds), `levels.*` (resistance, target, entry, EMA 20, EMA 50, support, stop), `series.s1` to `series.s8` (chart lines, WL-094: the dataviz reference palette, checked for colour blindness on the light and dark paper; use the slots in order, never cycle, at most 6 lines a chart, and label lines directly because three light slots are under 3:1).
- **Never write hex in a component.** Use theme keys in `sx`, or `theme.vars.palette` for SVG attributes (see `StrategyDiagram.tsx`). Discuss a palette change first (ruleset 9.2).

## Conventions

- **Green and red are for direction only**: Buy or win, Sell or loss, and since WL-152 a price change up or down (the watchlists). Pills always carry a glyph as well as a colour (▲ ▼ ● ✓ ✕ ○). Impact, job failure and source errors use the warning tone, never red (WL-048 resolved this way to keep ruleset 9.3).
- **Missing data** is `<Na reason="...">` (an em dash with the reason on hover), never `0` or blank. A win rate over fewer than 20 backtest trades shows `na("too few trades")`.
- **One primary button per view** (a dialog is its own view).
- **KPI strips** have a note under each value and scroll sideways on a phone.
- **Wide tables** use `DataTable`: they scroll inside their card with a sticky header, so the page never scrolls sideways.
- **Confirmations** use `useFeedback().ask`, an MUI Dialog, never `window.confirm` or `prompt`.
- **Model output and notes** are plain React text, escaped; no `dangerouslySetInnerHTML`.
- **Mobile (<600px):** body text 16px, buttons and icon buttons 48px.

## Build

- `npm run build` runs `tsc -b` and `vite build`. Vendor code is split into `react` and `vendor` chunks (`vite.config.ts`), so no file trips Vite's 500 kB warning.
- Ruleset 6.1 still says to delete `frontend/dist` after the gate's build. Since phase C FastAPI serves that folder, so deleting it leaves `/` at 503 until the next `start.ps1`. A ruleset change to keep `dist` is proposed to Sheryar (2026-10-22); until he answers, `dist` is left in place after a build.

## Browser storage

`localStorage` keys (all optional, wrapped in try/catch):

| Key | Holds |
|---|---|
| `cca_theme`, `cca_color_scheme` | MUI colour mode |
| `cca_rail_folded` | `1` / `0` |
| `cca_tf` | Last timeframe |
| `cca_recent` | Last 6 pairs |
| `cca_page`, `cca_arena_section` | Page and Arena section used last (a bare URL or `#/arena` opens them) |
| `cca_arena_*`, `cca_map_*`, `cca_bt_*`, `cca_jobs_*`, `cca_picks_*`, `cca_calendar_kind`, `cca_strategies_style` | Tabs, filters, searches, folds, chart choices and page offsets per page (WL-101) |

Every tab, filter, search box and page offset is kept per browser with `usePref` (`lib/storage.ts`), so a reload or a page switch comes back to the same view. The global pair search is the one exception: it always opens empty. Dialog forms are not kept.
