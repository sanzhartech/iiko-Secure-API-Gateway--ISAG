# Next Tasks for Continuing Development

This ordered task list outlines the immediate next steps to bring the application strictly to production readiness.

### Phase 1: Authentication Completeness
1. **Implement `/auth/refresh` Endpoint**:
   - The `.env` currently contains settings for refresh tokens, but the endpoint does not exist.
   - Implement the logic to accept a refresh token, validate its integrity, and issue a new access token (minimizing `POST /auth/token` logins).
2. **Implement DB-Backed Client Registry**:
   - Strip the hardcoded `_get_client_registry()` out of `app/api/auth.py`.
   - Implement an async database (e.g., PostgreSQL with SQLAlchemy or SQLite for simpler setup).
   - Create a `GatewayClient` table with hashed secrets (bcrypt or argon2).

### Phase 2: DevOps and Containerization
3. **Create `Dockerfile`**:
   - Make a multi-stage Docker build to keep images slim.
   - Run `uvicorn app.main:app` as a non-root user.
4. **Create `docker-compose.yml`**:
   - Prepare a compose file combining the backend alongside any necessary infrastructure (e.g., the PostgreSQL DB and a Redis cache for rate limiting).

### Phase 3: Reliability & Scaling
5. **Rate Limiting Backend Update**:
   - Move the `SlowAPI` backend from simple in-memory mode to a centralized Redis storage to ensure rate limits persist across multiple Docker worker instances or horizontal scaling.
6. **Audit Log Persistence**:
   - Current `AuditLogMiddleware` logs via `.info()` standard out. Add an asynchronous task queue or direct DB integration to sink these critical audit events into a persistent long-term storage table rather than merely unstructured application logs.

### Phase 4: Final Validation
7. **Full Integration Testing**:
   - Final review and execution of the `pytest` suite ensuring 100% pass rates. Validate proxy connection tear-downs strictly behave as expected under heavy load.
