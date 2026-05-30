# ISAG — Deployment & Operations Guide

This guide provides step-by-step instructions for deploying and running the **iiko Secure API Gateway (ISAG)** in both production and development environments.

---

## 1. Prerequisites & System Requirements

Before beginning, ensure your target machine meets the following requirements:
*   **Docker & Docker Compose**: Recommended for production. Supports Compose file version `3.8`.
*   **Python**: Version `3.12` (if deploying manually).
*   **Node.js**: Version `18+` or `20+` with `npm` (if running frontend manually).
*   **RAM**: At least `1 GB` of free RAM for the full stack.

---

## 2. Standard Production Deployment (Docker Compose)

ISAG runs as a fully containerized orchestration stack composed of **6 microservices**:
1.  **`db`**: PostgreSQL 15 database for client registries and audit trails.
2.  **`redis`**: Redis 7 cache for distributed rate limits and JTI replay protection.
3.  **`backend`**: FastAPI application executing the security pipeline.
4.  **`frontend`**: React dashboard served via Nginx (port 80).
5.  **`prometheus`**: Scrapes backend metrics.
6.  **`grafana`**: Visualizes security alerts and request logs (port 3000).

### Step 1: Clone the Repository
```bash
git clone https://github.com/sanzhartech/iiko-Secure-API-Gateway--ISAG-.git
cd iiko-Secure-API-Gateway--ISAG-
```

### Step 2: Generate Cryptographic RSA Keys
The gateway uses RS256. You must generate a matching pair of RSA keys before starting the backend:
```bash
# This script creates keys/private.pem and keys/public.pem,
# and bootstraps keys/public_keys.json with the active Key ID (KID)
python scripts/generate_keys.py
```

### Step 3: Run the Stack
Start all services in detached mode:
```bash
docker-compose up -d --build
```
This command compiles the frontend and backend, migrates the database, seeds the administrator credentials, and mounts the telemetry metrics pipelines.

### Step 4: Verify Service Health
Ensure all containers are running and healthy:
```bash
docker-compose ps
```

---

## 3. Nginx Reverse Proxy Configuration

In Docker mode, the **`frontend`** container runs Nginx which acts as the primary reverse proxy, serving the static dashboard and routing API requests to the backend:

```nginx
server {
    listen 80;
    server_name localhost;

    # Serve compiled React SPA
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Route API request proxies to FastAPI backend
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    # Route Auth and Admin request proxies
    location /auth/ {
        proxy_pass http://backend:8000/auth/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /admin/ {
        proxy_pass http://backend:8000/admin/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 4. Redis Configuration Guidelines

To prevent out-of-memory crashes due to JTI accumulation or rate-limiter keys, the Redis service is configured as a transient LRU cache:
```yaml
command: redis-server --save "" --appendonly no --maxmemory 128mb --maxmemory-policy allkeys-lru
```
*   `--save ""` and `--appendonly no`: Disables disk snapshotting (persistence is not needed since JTIs expire and rate limits reset on reload).
*   `--maxmemory 128mb`: Restricts maximum RAM usage to 128MB.
*   `--maxmemory-policy allkeys-lru`: Evicts least-recently-used keys when the memory limit is reached, protecting the host system from exhaustion.

---

## 5. Development Startup (Manual Execution)

If you need to run the application components directly on your host machine without Docker:

### A. Run Redis
Make sure Redis is running locally on port `6379`.

### B. Run Backend manually
1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure your environment:
    ```bash
    copy .env.example .env
    # Edit the .env file with your local credentials and paths
    ```
4.  Generate keys locally:
    ```bash
    python ../scripts/generate_keys.py
    ```
5.  Launch the FastAPI server:
    ```bash
    python app/main.py
    # or: uvicorn app.main:app --reload --port 8000
    ```

### C. Run Frontend manually
1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install packages:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```
4.  Open `http://localhost:5173` in your browser.
