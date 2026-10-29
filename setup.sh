#!/usr/bin/env bash
# One-step setup of Crypto Chart AI in Docker on macOS and Linux (WL-087, docs/docker.md).
#
#   ./setup.sh                    install what is missing, start
#   ./setup.sh --port 8010        another port than 8000
#   ./setup.sh --provider none    set AI_PROVIDER in backend/.env
#   ./setup.sh --no-browser       do not open the portal at the end
#
# Installs Docker when it is missing (macOS: Docker Desktop; Linux: Docker Engine from
# get.docker.com), starts it and sets it to start at login or boot, creates backend/.env,
# builds and starts the containers and waits until the portal answers. Installing asks
# for your password once (sudo). Safe to run again: the database volume is reused.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PORT=""
PROVIDER=""
BROWSER=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --provider) PROVIDER="$2"; shift 2 ;;
    --no-browser) BROWSER=0; shift ;;
    *) echo "unknown option $1"; exit 2 ;;
  esac
done

step() { printf '\033[36m==> %s\033[0m\n' "$*"; }
fail() { printf '\033[33mSetup stopped: %s\033[0m\n' "$*"; exit 1; }
OS="$(uname -s)"
DOCKER=(docker)

install_docker_mac() {
  local arch dmg
  arch="$(uname -m)"; [[ "$arch" == "arm64" ]] || arch="amd64"
  dmg="$(mktemp -d)/Docker.dmg"
  step "Downloading Docker Desktop for macOS ($arch)"
  curl -fL --progress-bar -o "$dmg" "https://desktop.docker.com/mac/main/$arch/Docker.dmg"
  step "Installing Docker Desktop (asks for your password)"
  sudo hdiutil attach -quiet -nobrowse -mountpoint /Volumes/Docker "$dmg"
  sudo /Volumes/Docker/Docker.app/Contents/MacOS/install --accept-license --user="$USER"
  sudo hdiutil detach -quiet /Volumes/Docker
  rm -f "$dmg"
}

install_docker_linux() {
  step "Installing Docker Engine from get.docker.com (asks for your password)"
  command -v curl >/dev/null || fail "curl is missing. Install curl, then run ./setup.sh again."
  curl -fsSL https://get.docker.com | sudo sh
}

# 1. Docker
export PATH="/usr/local/bin:/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
if ! command -v docker >/dev/null 2>&1; then
  step "Docker is not installed"
  case "$OS" in
    Darwin) install_docker_mac ;;
    Linux) install_docker_linux ;;
    *) fail "unsupported system $OS. On Windows run setup.ps1." ;;
  esac
fi

# 2. Start Docker at login or boot, so the containers come back after a restart.
if [[ "$OS" == "Darwin" ]]; then
  osascript -e 'tell application "System Events" to if not (exists login item "Docker") then make login item at end with properties {path:"/Applications/Docker.app", hidden:true}' >/dev/null 2>&1 || true
elif command -v systemctl >/dev/null 2>&1; then
  sudo systemctl enable --now docker >/dev/null 2>&1 || true
fi

# 3. The Docker engine
if ! docker info >/dev/null 2>&1; then
  if [[ "$OS" == "Darwin" ]]; then
    step "Starting Docker Desktop"
    open -a Docker
  elif sudo docker info >/dev/null 2>&1; then
    # Just installed: this login is not in the docker group yet, so use sudo this time.
    sudo usermod -aG docker "$USER" || true
    DOCKER=(sudo docker)
  fi
  deadline=$((SECONDS + 300))
  until "${DOCKER[@]}" info >/dev/null 2>&1; do
    (( SECONDS < deadline )) || fail "Docker did not start within 5 minutes. Start Docker, then run ./setup.sh again."
    sleep 5
  done
fi
"${DOCKER[@]}" compose version >/dev/null 2>&1 || fail "the Docker Compose plugin is missing (docker compose)."
step "Docker is running ($("${DOCKER[@]}" --version))"

# 4. Settings: backend/.env (AI provider and keys) and .env (port and time zone for compose)
if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
  step "Created backend/.env from backend/.env.example"
fi
if [[ -n "$PROVIDER" ]]; then
  if grep -q '^AI_PROVIDER=' backend/.env; then
    sed "s/^AI_PROVIDER=.*/AI_PROVIDER=$PROVIDER/" backend/.env > backend/.env.tmp && mv backend/.env.tmp backend/.env
  else
    echo "AI_PROVIDER=$PROVIDER" >> backend/.env
  fi
  step "AI_PROVIDER=$PROVIDER"
fi
touch .env
get_env() { grep -E "^$1=" .env | tail -n 1 | cut -d= -f2- || true; }
[[ -n "$PORT" ]] || PORT="$(get_env PORT)"
PORT="${PORT:-8000}"
TZ_VALUE="$(get_env TZ)"
printf 'PORT=%s\nTZ=%s\n' "$PORT" "${TZ_VALUE:-Asia/Karachi}" > .env

mkdir -p backups
SEED="$(ls -1 backups/*.db 2>/dev/null | sort | tail -n 1 || true)"
if [[ -z "$("${DOCKER[@]}" volume ls -q --filter name='^crypto-chart-ai-data$')" ]]; then
  if [[ -n "$SEED" ]]; then step "New database volume: it is filled from $SEED"
  else step "New database volume: no backup in backups/, starting empty"; fi
else
  step "Keeping the existing database volume crypto-chart-ai-data"
fi

# 5. Build and start
# app first: on a new volume it copies the seed backup, which can take minutes. Waiting
# here instead of in compose's depends_on avoids its long health poll.
step "Building and starting (the first build takes a few minutes)"
"${DOCKER[@]}" compose up -d --build app

step "Waiting for the portal to answer (the first start copies the database)"
URL="http://127.0.0.1:$PORT"
deadline=$((SECONDS + 900))
until curl -fsS "$URL/api/health" >/dev/null 2>&1; do
  (( SECONDS < deadline )) || fail "the app did not answer within 15 minutes. Run: docker compose logs app"
  sleep 5
done

step "Starting the scheduled jobs"
"${DOCKER[@]}" compose up -d

step "Crypto Chart AI is running at $URL"
echo "    It starts again by itself after a restart of Docker or of this computer."
echo "    AI provider and keys: backend/.env (see docs/docker.md). Logs: docker compose logs -f"
if (( BROWSER )); then
  if [[ "$OS" == "Darwin" ]]; then open "$URL"; else xdg-open "$URL" >/dev/null 2>&1 || true; fi
fi
