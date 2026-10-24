FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.23 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY engine ./engine
RUN uv sync --frozen --no-dev
RUN useradd --create-home app && mkdir -p /app/.local && chown app:app /app/.local
USER app
EXPOSE 8787
CMD ["sh", "-c", "exec /app/.venv/bin/uvicorn engine.api.app:app --host 0.0.0.0 --port ${PORT:-8787} --proxy-headers --forwarded-allow-ips='*'"]
