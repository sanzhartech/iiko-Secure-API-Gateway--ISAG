# ISAG — Environment Configuration Guide

The iiko Secure API Gateway loads and validates all configurations at startup from environment variables or a local `.env` file using Pydantic's `BaseSettings`.

If any required variable is missing or has an invalid type, the application refuses to start, ensuring a **fail-secure** deployment.

---

## 1. Environment Variable Reference

Below is the complete list of environment variables defined in the configuration schema:

| Variable Name | Data Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| **`APP_ENV`** | `development` \| `production` | `development` | Setting to `production` enforces HTTPS for upstream, disables Swagger UI debug modes, and requires explicit CORS. |
| **`APP_DEBUG`** | `boolean` | `false` | Enables debug level stack tracing (must be `false` in production). |
| **`APP_HOST`** | `string` | `0.0.0.0` | IP interface bind address for the FastAPI server. |
| **`APP_PORT`** | `integer` | `8000` | Port on which the gateway listens. |
| **`DATABASE_URL`** | `string` | `sqlite+aiosqlite:///./gateway.db` | SQLAlchemy database URL. In production, use `postgresql+asyncpg://...`. |
| **`REDIS_URL`** | `string` | `""` | Redis connection URL (e.g. `redis://redis:6379/0`). Required for rate limiting and JTI replay protection. |
| **`JWT_PRIVATE_KEY_PATH`** | `string` (Path) | `./keys/private.pem` | Path to the RSA private key used to sign tokens. |
| **`JWT_PUBLIC_KEY_PATH`** | `string` (Path) | `./keys/public.pem` | Path to the default RSA public key used to verify tokens. |
| **`JWT_PUBLIC_KEYS_PATH`** | `string` (Path) | `./keys/public_keys.json` | Path to the multi-key registry mapping Key IDs (KID) to PEMs. |
| **`JWT_ACTIVE_KID`** | `string` | `default` | The active Key ID written to issued token headers. |
| **`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`** | `integer` | `60` | Lifespan of access tokens (recommended: `15`). |
| **`JWT_REFRESH_TOKEN_EXPIRE_DAYS`** | `integer` | `7` | Lifespan of refresh tokens. |
| **`JWT_CLOCK_SKEW_SECONDS`** | `integer` | `60` | Max tolerance for system clock divergence (hard-capped at `300`). |
| **`IIKO_API_BASE_URL`** | `string` | `http://localhost:8000` | Upstream iiko API base URL (must start with `https://` in production). |
| **`IIKO_API_KEY`** | `string` | **Required** | The API secret key used to authenticate the gateway with the iiko API. |
| **`GATEWAY_CLIENT_SECRET`** | `string` | **Required** | The secret salt used to verify client credentials during token exchange. |
| **`RATE_LIMIT_PER_IP`** | `string` | `100/minute` | Default request rate limit for unauthenticated IPs. |
| **`RATE_LIMIT_PER_USER`** | `string` | `50/minute` | Default request rate limit for authenticated clients. |
| **`RATE_LIMIT_AUTH_ENDPOINT`** | `string` | `10/minute` | Rate limit on token request and refresh routes. |
| **`CORS_ALLOWED_ORIGINS`** | `string` (CSV) | `http://localhost:3000...` | Comma-separated list of origins allowed to cross-communicate with the gateway. |
| **`CORS_ALLOW_CREDENTIALS`** | `boolean` | `true` | Allows browser requests to send auth cookies and headers. |
| **`TRUSTED_PROXY_CIDRS`** | `string` (CSV) | `""` | Comma-separated CIDR block of trusted reverse proxies (e.g. `172.16.0.0/12`). |
| **`LOG_LEVEL`** | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` | `INFO` | Logging output verbosity. |
| **`LOG_FORMAT`** | `json` \| `console` | `json` | Structured JSON log production format. |
| **`ADMIN_USERNAME`** | `string` | `None` | If set, seeds an administrator client account with this ID on startup. |
| **`ADMIN_PASSWORD`** | `string` | `None` | The password associated with the seeded admin account. |

---

## 2. Decoupling of secrets: Upstream vs Gateway Client Secret

A critical security fix is the separation of **`IIKO_API_KEY`** and **`GATEWAY_CLIENT_SECRET`**:
*   **`IIKO_API_KEY`**: This is the private key provided by the iiko ERP platform. It authenticates the gateway itself when proxying calls upstream.
*   **`GATEWAY_CLIENT_SECRET`**: This is a distinct secret key used by the gateway to verify the authenticity of third-party clients requesting JWT tokens from the gateway.

**Why they must not be reused**:
Reusing the upstream iiko API key as the gateway client secret coupling creates a single point of failure. If a third-party client learns the secret they use to talk to the gateway, they would immediately obtain direct administrative credentials to the upstream iiko API, bypassing all of ISAG's rate limits, audit logs, and access controls. Pydantic constraints enforce that these two values must be different at startup.
