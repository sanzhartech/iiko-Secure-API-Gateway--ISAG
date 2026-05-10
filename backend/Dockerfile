FROM python:3.12.3-slim-bookworm

# Create a non-root user and group
RUN groupadd -r isaggroup && useradd -r -g isaggroup isaguser

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
# Add asyncpg for PostgreSQL support requested in Docker compose
RUN echo "asyncpg==0.29.0" >> requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure the /app/keys directory exists
RUN mkdir -p /app/keys

# Chown everything to the non-root user
RUN chown -R isaguser:isaggroup /app

# Switch to non-root user
USER isaguser

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
