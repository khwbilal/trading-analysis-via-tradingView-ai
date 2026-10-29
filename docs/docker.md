# Docker: setup on any computer

Crypto Chart AI runs in Docker on Windows, macOS and Linux (WL-087). One script installs Docker when it is missing, builds the app, fills the database from the newest backup and starts everything. The data survives restarts of the containers, of Docker and of the computer.

## For Claude: "complete the setup"

When someone opens this folder in Claude Code and asks to complete the setup or installation, do this and nothing else:

1. Run the setup script from the folder root and wait for it (the first run takes 5 to 15 minutes):
   - Windows: `powershell -ExecutionPolicy Bypass -File setup.ps1`
   - macOS and Linux: `bash setup.sh`
2. If port 8000 is taken, run it again with `-Port 8010` (Windows) or `--port 8010`.
3. If the script stops with "Restart Windows once", ask them to restart, then run it again.
4. If Docker has to be installed and the step asks for a password (sudo on macOS and Linux) or a Windows permission prompt, tell them to approve it or to run the same command in their own terminal.
5. Done when the script prints `Crypto Chart AI is running at http://127.0.0.1:<port>`. Give them that link.
6. Then ask which AI to use, and set it in `backend/.env` (no restart needed):
   - `none` (the default if they have nothing): market data and the deterministic plan, free.
   - `claude_code`, their Claude subscription: they run `claude setup-token` in their own terminal and paste the token as `CLAUDE_CODE_OAUTH_TOKEN`. Inside Docker the token is needed; the login of their own Claude Code does not reach the container.
   - `claude`, `openai` or `cursor`: their API key in `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` or `CURSOR_API_KEY`.

   Never print the key values back to them or into a log.

Do not run `docker compose down -v`, `docker volume rm` or `docker system prune --volumes`: they delete the database.

## What runs

| Part | What it does |
|---|---|
| `Dockerfile` | Builds the portal (Node 24), installs the backend with uv on Python 3.13, adds the Claude Code CLI for the subscription provider. Runs as user `app` (uid 1000). |
| `docker-compose.yml` | Two containers from the same image: `app` (the portal and API on `127.0.0.1:8000`) and `jobs` (the daily jobs). Both `restart: unless-stopped`. |
| `docker/entrypoint.sh` | On an empty data volume, copies the newest `backups/*.db` in as the database after `PRAGMA integrity_check`. An existing database is never touched. |
| `docker/scheduler.py` | Runs the jobs at the times in `scripts/jobs/register.ps1` (keep the two in step), in the time zone `TZ`, default `Asia/Karachi`. |
| `setup.ps1`, `setup.sh` | Install Docker when it is missing, make it start at sign-in or boot, create `backend/.env`, write `.env` (port, time zone), build, start, wait for `/api/health`, open the browser. |
| `scripts/share/package.ps1` | Builds `share/crypto-chart-ai-<date>.zip` to send to someone. |

## Where the data lives

| Data | Where | Kept |
|---|---|---|
| Database `app.db` and `backend/data` | Docker volume `crypto-chart-ai-data` | Across restarts, rebuilds and `docker compose down`. Removed only by `down -v` or `docker volume rm`. |
| Seed backup | `backups/*.db` in this folder (bind mount), or `BACKUP_HOST_DIR` from the root `.env` (WL-136) | Read once, when the volume is empty. |
| Daily backups | `backups/docker/` in this folder (or in `BACKUP_HOST_DIR`) | As files on the computer. The `backup` job writes one at 20:00. To move this install to another computer, copy the newest one into that computer's `backups/`. |
| Arena lessons and reports | `docs/arena/` in this folder (bind mount) | As files. |
| AI provider and keys | `backend/.env` in this folder (bind mount) | As a file, re-read on every request. |

The container comes back by itself after a restart: Docker Desktop is set to start at sign-in (Windows: the `Docker Desktop` Run key; macOS: a login item), Docker Engine on Linux is enabled in systemd, and both containers have `restart: unless-stopped`. A container stopped by hand with `docker compose stop` stays stopped until `docker compose start`.

A newer backup dropped into `backups/` later is not loaded by itself: the seed only fills an empty volume, so an install never loses its own data (decision 0010).

## Everyday commands

From the folder root:

```bash
docker compose ps                 # both containers, app shows (healthy)
docker compose logs -f app        # server log
docker compose logs -f jobs       # job start and exit lines
docker compose up -d --build      # after updating the code
docker compose exec app python -m app.jobs picks   # run one job by hand
```

## Sharing it with someone

```powershell
powershell -ExecutionPolicy Bypass -File scripts\share\package.ps1          # newest backup in backups\
powershell -ExecutionPolicy Bypass -File scripts\share\package.ps1 -Fresh   # a fresh copy of the live database
```

The zip holds the code, the docs and one database backup. It never holds `.env` files, `backend/data` or the other backups; the script checks the finished zip and refuses it otherwise. The recipient unzips it, opens the folder in Claude Code and says "complete the setup".

## Gotchas

- **Size:** the database is about 0.9 GB, so the zip and the first start take a while. The first start copies and checks it before the portal answers (the health check allows 10 minutes).
- **Linux file owner:** the container user is uid 1000. If the host user has another uid, the `backup` job cannot write to `backups/`; run `sudo chown -R 1000 backups docs/arena`.
- **Windows needs WSL 2** and virtualisation turned on in the BIOS. `setup.ps1` turns WSL on; the BIOS setting is up to the owner.
- **No live Binance trading** in Docker either: the app never places orders.
- **Port binding:** the API has no login, so it listens on `127.0.0.1` only. Do not change the port line to `0.0.0.0`.
- **Docker and the start scripts on one folder:** they use separate databases (the volume versus `backend/data`) and separate backup folders, but share `docs/arena/` and `backend/.env`. Running both at once means two sets of daily jobs, and the Arena lesson files get entries from both. Run one of them; stop the other (`docker compose stop`, which keeps the data).
- **Missed jobs:** a job time that passes while the computer is off is not caught up (Task Scheduler on Sheryar's machine does catch up).
