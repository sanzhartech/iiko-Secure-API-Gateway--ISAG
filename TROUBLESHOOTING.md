# ISAG — Troubleshooting Manual

This guide lists common operational issues, diagnostics workflows, and recovery steps for the **iiko Secure API Gateway (ISAG)**.

---

## 1. Startup Failures

### A. FileNotFoundError: private.pem or public_keys.json
*   **Symptom**: The backend container crashes on startup with a stack trace ending in `FileNotFoundError: [Errno 2] No such file or directory: 'keys/private.pem'`.
*   **Root Cause**: The RSA key generator has not been run, or the `keys` folder was not successfully mounted.
*   **Remediation**:
    1.  Ensure you have run the key generator:
        ```bash
        python scripts/generate_keys.py
        ```
    2.  Check that the files exist in the `backend/keys` directory.
    3.  In Docker environment, ensure the keys volume mount is mapped as read-only:
        ```yaml
        volumes:
          - ./backend/keys:/app/keys:ro
        ```

### B. ValidationError: IIKO_API_KEY and GATEWAY_CLIENT_SECRET must be different
*   **Symptom**: The backend container fails to start with:
    `ValueError: IIKO_API_KEY and GATEWAY_CLIENT_SECRET must be different secrets.`
*   **Root Cause**: You copied the iiko API key value into the gateway client secret field in your `.env` or `docker-compose.yml` file.
*   **Remediation**: Generate a separate 32-character token for the gateway client secret:
    ```bash
    python -c "import secrets; print(secrets.token_urlsafe(32))"
    ```
    Paste this value into `GATEWAY_CLIENT_SECRET` in your configuration, keeping it distinct from `IIKO_API_KEY`.

---

## 2. Integration & Runtime Issues

### A. Redis Connection Errors
*   **Symptom**: Backend requests fail with `redis.exceptions.ConnectionError: Error connecting to localhost:6379`.
*   **Root Cause**: The gateway is attempting to reach Redis but the server is down or the URL is misconfigured.
*   **Remediation**:
    *   **Docker Deployment**: Verify that the `REDIS_URL` in `docker-compose.yml` points to the container name: `redis://redis:6379/0` (not `localhost`).
    *   **Manual Deployment**: Ensure the local Redis service is active:
        ```bash
        # Windows Powershell check
        Get-Service -Name *redis*
        # Start if stopped
        Start-Service -Name redis
        ```

### B. SQLite Database Locking Errors
*   **Symptom**: Logs show `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) database is locked`.
*   **Root Cause**: SQLite lacks high concurrency write capability. When multiple processes write to `gateway.db` concurrently, lockouts occur.
*   **Remediation**:
    1.  In development, reduce write loads or delete `gateway.db` and reload the server to recreate a clean state.
    2.  For production, transition to PostgreSQL by setting the `DATABASE_URL` environment variable:
        ```env
        DATABASE_URL=postgresql+asyncpg://isag_admin:isag_secure_password@db:5432/isag_db
        ```

### C. Persistent 401 Unauthorized for Valid Tokens
*   **Symptom**: Client requests return `HTTP 401 Unauthorized` even though the token signature is mathematically valid.
*   **Root Cause 1: Expired Token**: The token's `exp` timestamp is in the past. Remember access tokens expire in 15 minutes.
*   **Root Cause 2: Clock Skew**: The server clock and client clock differ by more than `60` seconds. Check server time drift.
*   **Root Cause 3: KID mismatch**: The token JOSE header carries a `kid` that does not match any entry in the public keys JSON registry.
*   **Remediation**:
    1.  Check the token details using a debugger (e.g. `jwt.io`) to verify expiration, issuer, audience, and type claims.
    2.  Synchronize host clocks using NTP.
    3.  Verify that `keys/public_keys.json` contains the `kid` specified in the token header.

---

## 3. Observability & Telemetry Problems

### A. Prometheus displays 0 metrics or is missing labels
*   **Symptom**: Prometheus scraper page shows `server returned HTTP status 404` or the metrics are empty.
*   **Root Cause**: The metrics middleware is bypassed or Prometheus cannot reach the `/metrics` route.
*   **Remediation**:
    1.  Verify `/metrics` responds locally:
        ```bash
        curl http://localhost:8000/metrics
        ```
    2.  Verify the Prometheus scrape config matches the container name and port:
        ```yaml
        scrape_configs:
          - job_name: 'isag-gateway'
            metrics_path: '/metrics'
            static_configs:
              - targets: ['backend:8000']
        ```

### B. Grafana dashboards fail to load or show no data
*   **Symptom**: Grafana opens but panels show "No Data" or errors.
*   **Root Cause**: The Prometheus data source is configured incorrectly or Grafana dashboard json is missing.
*   **Remediation**:
    1.  Navigate to **Connections -> Data Sources** in Grafana and test the Prometheus connection. It should point to `http://prometheus:9090`.
    2.  Ensure files in `./infrastructure/grafana/provisioning/` are properly mounted into the container.
