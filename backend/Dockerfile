# ==============================================================================
# Builder Stage
# ==============================================================================
FROM python:3.12-slim AS builder

# Set environment variables for builder
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt .
RUN pip install -r requirements.txt

# ==============================================================================
# Runner Stage
# ==============================================================================
FROM python:3.12-slim AS runner

# Set environment variables for runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Create a non-root user (gatewayuser) and required directories
RUN groupadd -g 1000 gatewaygroup && \
    useradd -u 1000 -g gatewaygroup -s /bin/bash -m gatewayuser && \
    mkdir -p /app/data /app/keys && \
    chown -R gatewayuser:gatewaygroup /app

# Copy the pre-built virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Copy application code
COPY ./app ./app

# Ensure correct permissions after copying
RUN chown -R gatewayuser:gatewaygroup /app

# Switch to the non-root user
USER gatewayuser

# Expose standard FastAPI port
EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
