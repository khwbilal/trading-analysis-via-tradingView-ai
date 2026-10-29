# Crypto Chart AI in one image (WL-087). Built and started by setup.ps1 / setup.sh
# through docker-compose.yml; see docs/docker.md.

# 1. The React + MUI portal, built to frontend/dist (FastAPI serves it at /).
FROM node:24-slim AS portal
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# 2. The Claude Code CLI for AI_PROVIDER=claude_code. The npm package installs a
#    native binary for this platform, so the final image needs no Node.
FROM node:24-slim AS claude
ARG CLAUDE_CODE_VERSION=2.1.308
RUN npm install -g --no-audit --no-fund "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
 && cp "$(readlink -f "$(npm root -g)/@anthropic-ai/claude-code/bin/claude.exe")" /claude \
 && /claude --version

# 3. The backend.
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/backend/.venv/bin:${PATH}"

# uv installs everything; pip and its vendored urllib3, msgpack and setuptools are unused.
RUN python -m pip uninstall -y -q pip \
 && useradd --create-home --uid 1000 app
WORKDIR /app/backend

# Dependencies first so a code change does not reinstall them.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/app ./app
RUN uv sync --frozen --no-dev
COPY --from=portal /src/frontend/dist /app/frontend/dist
COPY --from=claude /claude /usr/local/bin/claude
COPY docs/arena /app/docs/arena
COPY docker/entrypoint.sh docker/scheduler.py /app/docker/

# The mount points exist and belong to app, so new named volumes start writable.
RUN mkdir -p /app/backend/data /app/backups \
 && touch /app/backend/.env \
 && chmod +x /app/docker/entrypoint.sh \
 && chown -R app:app /app/backend/data /app/backups /app/docs /app/backend/.env

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)"

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
