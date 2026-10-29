# Crypto Chart AI: Claude Code notes

> **Follow [docs/reference/ruleset.md](docs/reference/ruleset.md) for all work** (adapted from the unefy-platform ruleset). **Typing "hi claude" starts it** (ruleset 10.4): confirm the ruleset, start the prompt count, read [docs/project-state.md](docs/project-state.md), report the docs review and the version and security check, fix nothing yet.
>
> Issue first: every change gets a `WL-nnn` row in [docs/work-log.md](docs/work-log.md) before the first edit. **No git** by owner decision ([0004](docs/decisions/0004-no-git-for-now.md)): back up files before risky edits, do not suggest git. Project text: no em dashes, no en dashes, no exclamation marks.

> **Someone asks to "complete the setup" or install the app:** follow [docs/docker.md](docs/docker.md) ("For Claude"), not the ruleset.

FastAPI backend (`backend/app/`) and the React + MUI portal (`frontend/`), whose build `frontend/dist` FastAPI serves at `/` (the start scripts build it). Docs live in `docs/` (index [docs/README.md](docs/README.md)): decisions in `docs/decisions/`, incidents in `docs/incidents/`.

## Run

```bash
cd backend
uv sync --python 3.13
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

`start.ps1` / `start.sh` run `app.choose_provider` (menu: Claude subscription, Claude API, Cursor, OpenAI, none) and write `AI_PROVIDER` plus any key to `backend/.env`. With `AI_PROVIDER=none`, `/api/analyze` runs the whole pipeline and returns `provider: "offline"`: use that for checks, since every other provider spends plan usage or money (ruleset 6.3).

## Where things are

- Providers and prompt: `app/ai.py` (`_claude_generate` API key, `_claude_code_generate` subscription via `claude -p` with tools, MCP and settings off, `_cursor_generate`, `_openai_generate`). Provider choice: `app/config.py:resolve_provider`.
- Prompt snapshot: `app/market.py:context_to_prompt_block`. `setup` and `confluence` must stay first so trimming never removes them ([incident WL-012](docs/incidents/WL-012.md)).
- Guards: `app/main.py` `_apply_confluence_guardrail` and `_apply_reward_risk_guard` decide the bias, not the AI ([decision 0003](docs/decisions/0003-guards-decide-the-bias.md)).
- Market snapshot: `app/market.py:fetch_coin_context`. Every source is optional and records `available: false` / `error` instead of raising.
- Persistence: SQLite `backend/data/app.db` (`app/db.py`, migrations in `app/migrations/`), see [docs/database.md](docs/database.md). Stored data is never deleted ([decision 0010](docs/decisions/0010-never-delete-data.md)): no purges, no keeping only the newest few, removals go through `db.archive_and_delete`; `tests/test_no_data_loss.py` fails on any new delete path. Scheduled jobs: `app/jobs/` plus `scripts/jobs/*.bat`, see [docs/scheduled-jobs.md](docs/scheduled-jobs.md).

## UI rules (see `docs/ui.md` and ruleset 9)

- One UI: React + MUI. Colours come from the theme in `frontend/src/theme.ts`; no hex in components. The primary colour is for interactive elements, the brand colour for the logo only.
- Green and red mean Buy/win and Sell/loss only; every pill carries a glyph as well as a colour.
- Missing data is `na("reason")` / `<Na>` (an em dash with the reason on hover), never `0` or blank.
- Model output never goes in as raw HTML (no `dangerouslySetInnerHTML`).
- An MUI Dialog through the shared confirm helper instead of `window.prompt` / `confirm`. One primary button per view.
