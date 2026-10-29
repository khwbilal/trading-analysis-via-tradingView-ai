# Wallets

Item WL-063. Sheryar opens trades on Binance by hand and books them here for bookkeeping, in one or more wallets. Nothing is sent to Binance and no API key is stored ([WL-064 and WL-067 closed](../work-log.md), 2026-10-22): every number is what was entered. Live Binance prices are read only to show the result of open trades. No AI call, so no plan usage.

## File map

| File | Role |
|---|---|
| `backend/app/wallets.py` | Create, rename, archive and restore wallets; deposits and withdrawals; book, close and archive trades; `summarize` (balance, equity, results, history), `list_wallets`, `wallet_detail` |
| `backend/app/migrations/013_wallets.sql` | `wallets`, `wallet_entries`; `open_fee` and `archived_at` on `positions` |
| `backend/tests/test_wallets.py` | Booking, closing, balance and history maths, archive rules, API round trip |
| `frontend/src/pages/Wallets.tsx` | The Wallets page (Track record section of the rail) |
| `frontend/src/components/WalletDialogs.tsx` | New wallet, deposit or withdrawal, book a trade, close a trade |
| `frontend/src/components/PositionDialog.tsx` | "Book in a wallet" in the Top 10 calculator, prefilled from it; the paper wallet picker for Open paper position (WL-150) |
| `frontend/src/components/WalletCharts.tsx` | WL-151: balance over time (every wallet), result per day, drawdown, money in and out, by month, by pair |
| `backend/app/migrations/026_paper_wallets.sql` | WL-150: `signals.wallet_id` |

## How it works

- **Wallets** have a name, exchange (default Binance), kind (USD-M futures or spot), currency (USDT) and a starting balance. Several wallets show side by side as cards; click one to open it below.
- **Booked trades** are rows in `positions` with `account = 'wallet'` and a `wallet_id`, so the paper job and the Paper page never see them. Give the quantity or the margin (cost for spot) and the other follows from the entry and leverage. Fees are amounts in USDT as the exchange shows them: `open_fee` at booking, the close fee when closing; `fees` holds both once closed. Opened and closed times may be backdated.
- **Spot wallets** book buys only, at 1x, with no liquidation.
- **No caps** on size or leverage beyond Binance's own 1 to 125x. A booking records a trade that already happened, so an estimated liquidation before the stop is a warning, not a block (paper positions still block it).
- **Closing:** enter the exit and the fee paid. Status becomes `win` (profit above zero) or `loss`. For a futures trade, tick "It was liquidated": the margin is lost, the exit defaults to the estimated liquidation price.
- **Nothing is deleted** ([decision 0010](../decisions/0010-never-delete-data.md)). A wallet, a deposit or withdrawal, or a booked trade made by mistake is archived (`archived_at`): it stops counting and stays stored and listed (greyed). An archived wallet is hidden unless "Show archived wallets" is on, takes no bookings and can be restored.

## Paper wallets (WL-150)

A wallet of kind **paper** is simulated. It takes no hand bookings (400); its trades are:

- **Paper positions** opened on Picks with "Paper position counts in" set to it (`positions.account = 'paper'`, `wallet_id`). They close by the paper check as before; the open result uses the position's own fee rate (`positions.settle`).
- **Signal paper trades** whose signal points at it (`signals.wallet_id`), counted only **once the entry filled** (not while `waiting_for_entry`, never for `entry_not_reached` or `invalid`). Open ones show the live result, closed ones the paper result at the hit price; an expiry at the horizon shows as `closed`. New signals take the default from the Signals paper defaults ("New signals count in", setting `paper_wallet_id`, 0 for none; an archived wallet is ignored). Each signal's paper card can move it to another paper wallet or none.

Rows from before WL-150 keep no wallet. A signal trade has `account = 'signal'` and its `signal_id`; its `id` is the signal's `seq`, so the page keys rows by account and id.

## Charts (WL-151)

`GET /api/wallets/charts?include_archived=false` gives every wallet on one day axis (`days`, from the first wallet's start to today): `balance` (end of day, null before the wallet starts), `pnl`, `deposits` (the starting balance counts as money in), `withdrawals` (negative), `trades`, `won`, plus `by_pair` and `by_month`. Closed trades only, so no live price is fetched. The page draws the balances compared (a box hides a line, range 30 d, 90 d, 1 y, All, kept per browser), and for the selected wallet the result per day (green up, red down), the drawdown of the summed trade result from its high (money in and out left out), money in and out, and the month and pair tables.

## The maths

- Profit or loss = direction x quantity x (exit - entry) - open fee - close fee. For futures the price part never loses more than the margin (isolated). Return on margin = profit or loss / margin.
- Liquidated: profit or loss = - margin - fees.
- **Balance** = starting balance + deposits - withdrawals + realized profit or loss of closed trades.
- **Unrealized** = open trades at the live price, after the open fee. **Equity** = balance + unrealized; shown only when every open trade has a live price.
- **Balance over time:** the starting balance first, then every deposit, withdrawal and closed trade in time order with the running balance.
- Amounts are rounded to 6 decimals on the server; the forms take at most 6 decimals (WL-062).

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/wallets?include_archived=false` | Every wallet with its summary |
| `POST` | `/api/wallets` | Create a wallet |
| `GET` | `/api/wallets/{id}` | One wallet: summary, trades (with live price and unrealized result), entries, history |
| `PATCH` | `/api/wallets/{id}` | Rename or change the notes |
| `POST` | `/api/wallets/{id}/archive?restore=false` | Archive, or restore with `restore=true` |
| `POST` | `/api/wallets/{id}/entries` | Book a deposit or withdrawal |
| `POST` | `/api/wallets/{id}/entries/{entry_id}/archive` | Archive an entry |
| `POST` | `/api/wallets/{id}/trades` | Book a trade |
| `POST` | `/api/wallets/{id}/trades/{pos_id}/close` | Close it at an exit, or as liquidated |
| `POST` | `/api/wallets/{id}/trades/{pos_id}/archive` | Archive a booking |
| `GET` | `/api/wallets/charts?include_archived=false` | WL-151: day series and breakdowns for every wallet |

Paper wallets (WL-150): `POST /api/wallets` takes `kind: "paper"`; `POST /api/positions` takes `wallet_id`; `PATCH /api/signals/{id}` takes `wallet_id` (0 for none); `PUT /api/paper-settings` takes `wallet_id`.

Errors: 404 for an unknown wallet, entry or trade; 400 for a rule (archived wallet, wrong side stop, close before open, trade not open); 422 for a bad field.

## Gotchas

- The liquidation price is an estimate (first maintenance tier, MMR 0.5%); Binance's can differ slightly.
- The wallet's `created_at` is when it was made here. A trade booked earlier still counts; the history keeps the starting balance first.
- There is no edit of a booking: archive it and book it again.
