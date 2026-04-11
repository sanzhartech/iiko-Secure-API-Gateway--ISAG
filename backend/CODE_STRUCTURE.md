# Code Structure

The project follows a modular layout common to robust FastAPI applications.

```text
backend/
├── app/
│   ├── api/                # API Routers
│   │   ├── auth.py         # /auth/token endpoint
│   │   └── proxy.py        # /api/{path} streaming proxy endpoints
│   ├── core/               # Application-wide settings and core utilities
│   │   ├── config.py       # Pydantic BaseSettings, central config, key loading
│   │   └── logging.py      # Structlog json/console configuration
│   ├── middleware/         # FastAPI middlewares
│   │   ├── rate_limiter.py # slowapi state config and decorators
│   │   └── secure_headers.py # Helmet-like security headers
│   ├── models/             # Database ORM models (currently minimal/stubbed)
│   │   └── user.py
│   ├── schemas/            # Pydantic validation schemas (Input/Output API models)
│   │   └── token.py        # TokenRequest, TokenResponse, TokenClaims
│   ├── security/           # Auth and Security domain logic
│   │   ├── audit.py        # Request audit log middleware
│   │   ├── jwt_validator.py# JWT parsing, verification, and clock skew handling
│   │   └── rbac.py         # Role-Based Access Control logic and permissions
│   └── services/           # External service integration
│       └── iiko_client.py  # Asynchronous httpx client for the iiko API upstream
├── keys/                   # Folder containing RSA PEM files (private.pem, public.pem, public_keys.json)
├── tests/                  # Pytest test suites (conftest.py, test_proxy, test_auth)
├── main.py                 # FastAPI application factory and exception handlers
├── pyproject.toml / requirements.txt # Python dependencies
└── .env                    # Environment configuration
```

### Key Modules Explanation
- **`app/main.py`**: The application entry point. Defines `create_app()` utilizing the async lifespan hook to initialize and gracefully teardown the `IikoClient`. Attaches global middlewares and exception handlers.
- **`app/core/config.py`**: The strictest part of the app. Fails fast if `.env` varies from constraints. Caches RSA keys into memory on startup via `model_post_init` to prevent disk bottlenecks.
- **`app/services/iiko_client.py`**: The engine of the proxy. Exposes `proxy_request_stream`, directly piping bytes using `httpx.stream()` to ensure low memory footprint during proxy calls. Strips sensitive `hop-by-hop` headers.
- **`app/api/proxy.py`**: Defers all requests mapping to `/api/` to `IikoClient`. Leverages `AsyncExitStack` to guarantee upstream connections are cleanly closed upon disconnects or exceptions.
- **`app/api/auth.py`**: Issues tokens, mocking the DB lookup currently. Checks credentials using constant-time evaluation to prevent timing attacks.
