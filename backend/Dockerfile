# ─── Build Stage ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY pyproject.toml .
COPY app/ ./app/
RUN pip install --no-cache-dir --prefix=/install .

# ─── Runtime Stage ────────────────────────────────────────────
FROM python:3.12-slim AS runtime

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

# Create necessary directories
RUN mkdir -p /app/keys /tmp/exports && \
    chown -R appuser:appuser /app /tmp/exports

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
