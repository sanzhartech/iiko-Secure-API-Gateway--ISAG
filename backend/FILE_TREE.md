# ISAG — Final Directory Structure

```text
iiko-Secure-API-Gateway-ISAG/
├── .github/workflows/          # [CI/CD] Automated Testing Pipeline
│   └── ci.yml                  # GitHub Actions: Pytest + Redis
├── backend/                    # Core Gateway Application
│   ├── app/                    # Main Application Logic
│   │   ├── api/                # [REST] Controllers: auth, proxy, admin, protected
│   │   ├── core/               # [Shared] Config, Redis, Metrics, Logging, Hashing, Network
│   │   ├── db/                 # [DB] Engine & Session Logic (SQLAlchemy)
│   │   ├── middleware/         # [Pipeline] Security, Observation, RateLimit
│   │   ├── models/             # [Entity] Client, User, Audit, Admin (DB Schemas)
│   │   ├── schemas/            # [DTO] Token, Admin, Request/Response schemas
│   │   ├── security/           # [Auth] JWT (RS256), JTI (Redis), RBAC, Audit
│   │   ├── services/           # [Logic] Iiko Upstream Client, Client Service
│   │   ├── static/             # [Assets] Static files if served
│   │   └── main.py             # App Factory & Middleware Orchestration
│   ├── keys/                   # [Security] RSA Private/Public Key Registry
│   ├── scripts/                # [Utility] Generation & Stress-test scripts
│   ├── tests/                  # [QA] Comprehensive 70-Test Suite
│   ├── .env                    # Environment Configuration
│   ├── CODE_STRUCTURE.md       # Technical module breakdown
│   ├── API_SPEC.md             # Interface Contract
│   ├── CURRENT_STATE.md        # Real-time implementation status
│   └── requirements.txt        # Production dependencies
├── frontend/                   # Admin Dashboard (Vite + React + TS)
│   ├── src/
│   │   ├── pages/              # Dashboard, Clients, AuditLogs, etc.
│   │   └── components/         # UI Components (Charts, Tables, etc.)
│   ├── Dockerfile              # Frontend containerization
│   └── package.json            # React dependencies
├── infrastructure/             # Orchestration & Monitoring Config
│   ├── grafana/                # Grafana Dashboards & Provisioning
│   └── prometheus/             # Prometheus Scrapers & Data Sources
├── scripts/                    # Root Utility Scripts
│   ├── stress_test.py          # Attack Simulation Engine
│   └── generate_keys.py        # RS256 Key Pair Generator
├── docker-compose.yml          # Full-Stack Orchestration (Gateway+Redis+Monitoring+Frontend)
├── ARCHITECTURE.md             # Deep Technical Analysis
├── DEBUG_LOG.md                # Bug fix and implementation history
├── PROJECT_STATE.md            # High-level project status
├── README.md                   # Project Showcase & Quickstart
├── ROADMAP.md                  # Future Development & Scaling Vectors
└── TESTING_REPORT.md           # Verification & Metric Proof
```
