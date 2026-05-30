# ISAG — Future Roadmap & Scaling Vectors

This document outlines the finished features and future enterprise scalability paths for the **iiko Secure API Gateway (ISAG)** as of **May 2026**.

---

## 1. Enterprise Secrets Management
*   **HashiCorp Vault Integration**: Transition the current local `.pem` files key storage to a centralized Vault secrets engine. This will automate key rotation, audit key access, and store client secrets in hardware-backed storage.
*   **Mutual TLS (mTLS)**: Enforce mTLS between the gateway and upstream iiko API nodes, adding another cryptographic verification layer to prevent man-in-the-middle attacks on the backend network.

## 2. Infrastructure Scaling
*   **Horizontal Redis Clustering**: Migrate the single-node Redis cache to a Redis Sentinel or Cluster topology to sustain higher request volumes for rate limiting and JTI replay checks.
*   **PostgreSQL High Availability**: Scale the PostgreSQL instance to a master-replica configuration with automated failover (e.g. pgpool-II) to ensure 99.99% database uptime for client records and audit logs.
*   **Kubernetes Ingress Controller**: Wrap the gateway as a custom Kubernetes Ingress controller, auto-scaling backend pods dynamically based on incoming CPU/traffic thresholds.

## 3. Intelligent Security & Threat Intelligence
*   **ML Anomaly Detection**: Process the Postgres request logs asynchronously through a Machine Learning engine (e.g., isolation forest) to spot anomalous API patterns, indicating potential data scraping or brute force.
*   **Adaptive Rate Limits**: Adjust rate limit limits dynamically for specific client IDs based on their real-time anomaly scores.

---

## ✅ Completed Strategic Milestones

The following milestones are 100% completed, hardened, and verified:
- [x] **Asynchronous reverse proxy engine**: Zero-buffering streaming proxy with path-traversal safeguards.
- [x] **Asymmetric JWT Verification**: Cryptographic RS256 validator with dynamic key rotation support.
- [x] **Token Type Separation**: Complete decoupling of Access and Refresh tokens at validation.
- [x] **Stateful Replay Protection**: Atomic Redis-backed JTI tracking with a 2-second grace period.
- [x] **Distributed Rate Limiting**: SlowAPI and Redis-backed IP/client rate limits.
- [x] **DB-Backed Partner Registry**: Async SQLAlchemy database with Bcrypt and timing-attack guards.
- [x] **Database Audit Trail**: Full historic logs of admin actions and requests.
- [x] **Observability Instrumentation**: Prometheus metrics exporter and Grafana dashboard provisioning.
- [x] **Admin Management UI**: React dashboard featuring live attack visualization, client onboarding wizard, analytics, and global Kill-Switch.
- [x] **Docker Stack**: Full docker-compose file orchestrating Postgres, Redis, backend, frontend, Prometheus, and Grafana.
