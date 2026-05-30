# ISAG — Final Directory Structure

Below is the directory tree of the **iiko Secure API Gateway (ISAG)** project, illustrating the clean segregation of frontend, backend, infrastructure, and documentation assets.

```text
iiko-Secure-API-Gateway-ISAG/
├── .github/workflows/          # [CI/CD] Automated testing configuration
│   └── ci.yml                  # GitHub Actions workflow (Pytest + Redis)
├── backend/                    # Core gateway application
│   ├── app/                    # Application source code
│   │   ├── api/                # REST endpoints: auth, proxy, admin, protected
│   │   ├── core/               # Shared logic: config, redis, metrics, logging, hashing
│   │   ├── db/                 # Database engine and session lifecycle
│   │   ├── middleware/         # Pipeline layers: secure headers, size validation, rate limiter, metrics, response filter
│   │   ├── models/             # SQLAlchemy schemas: client, audit, user
│   │   ├── schemas/            # Pydantic schemas: token, admin, user
│   │   ├── security/           # RS256 validator, JTI grace check, RBAC rules
│   │   ├── services/           # Async reverse proxy and registry services
│   │   └── main.py             # FastAPI entrypoint and middleware assembly
│   ├── keys/                   # RSA private/public keys volume mount
│   ├── scripts/                # Backend utilities (seeding database)
│   ├── tests/                  # Pytest test suite (70 tests)
│   ├── .env                    # Local environment variables
│   ├── .env.example            # Environment configuration template
│   ├── API_SPEC.md             # API specifications contract
│   ├── CODE_STRUCTURE.md       # Architectural breakdown of components
│   ├── CURRENT_STATE.md        # Current backend verification state
│   ├── FILE_TREE.md            # Directory structure reference
│   ├── PROJECT_CONTEXT.md      # Backend request pipeline context
│   ├── pyproject.toml          # Package manager settings
│   └── requirements.txt        # Backend dependencies list
├── frontend/                   # React/Vite Admin Dashboard
│   ├── src/                    # Component and pages sources
│   ├── Dockerfile              # Docker recipe for frontend container
│   ├── nginx.conf              # Nginx proxy routing configuration
│   └── package.json            # Node.js dependencies
├── infrastructure/             # Prometheus and Grafana setup
│   ├── grafana/                # Provisioned datasources and dashboards
│   └── prometheus.yml          # Prometheus scrape configuration
├── scripts/                    # Root helper scripts
│   ├── generate_keys.py        # Generates RSA key pairs
│   └── stress_test.py          # Traffic archetype stress test engine
├── docker-compose.yml          # Multi-container orchestration stack
├── ARCHITECTURE.md             # High-level architecture and pipeline
├── DEPLOYMENT.md               # Docker and manual deployment guide
├── SECURITY.md                 # Security controls and threat mitigations
├── ENV_CONFIG.md               # Environment variables specification
├── TROUBLESHOOTING.md          # Diagnostics and recovery workflows
├── DEBUG_LOG.md                # Historic bugfix record
├── PROJECT_STATE.md            # High-level project milestones
├── README.md                   # Project landing page and quickstart
├── ROADMAP.md                  # Development roadmap and scaling vectors
├── TESTING_REPORT.md           # Test suite and stress test verification
└── walkthrough.md              # Project finalization overview
```
