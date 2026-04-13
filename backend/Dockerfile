# ── Stage 1: Builder (Build Environment) ───────────────────────────────────────
FROM python:3.12-slim AS builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies to a local directory
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime (Hardened Production Image) ─────────────────────────────
FROM python:3.12-slim AS runtime

# Security: Never run the gateway as root
# Create a dedicated non-privileged user and group
RUN groupadd --gid 1001 gatewaygroup \
    && useradd --uid 1001 --gid gatewaygroup --no-create-home gatewayuser

WORKDIR /app

# Copy only the installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy the application source code
# We only copy the app directory to keep the image clean
COPY app ./app

# Prepare necessary directories with correct permissions
RUN mkdir -p /app/data /app/keys \
    && chown -R gatewayuser:gatewaygroup /app/data /app/keys

# Security: Switch to the non-root user
USER gatewayuser

# Metadata
EXPOSE 8000
LABEL maintainer="ISAG Security Team"
LABEL version="1.1.2"

# Stage 1-2 Healthcheck: Verify the gateway is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Entry point: Use uvicorn with production-hardened flags
# - No access logs (Audit logging is handled at Stage 8 in middleware)
# - No reload
# - Limited workers to match resource constraints
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log"]
