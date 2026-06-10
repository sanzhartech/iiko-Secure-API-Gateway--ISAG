# syntax=docker/dockerfile:1

# ── Builder stage: compile wheels with build tools ────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# build-essential is needed only to build any sdist-only deps; it stays in the
# builder stage and never reaches the runtime image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Runtime stage: slim, non-root ─────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy installed packages from the builder (no compilers in final image).
COPY --from=builder /install /usr/local

# Create an unprivileged user to run the app.
RUN useradd --create-home --uid 10001 appuser

# Copy application code and hand ownership to the non-root user.
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# [C4] Multiple workers + access log disabled (audit middleware already logs).
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "4", "--no-access-log"]
