# ISAG — Future Roadmap & Scaling Vectors

As of 2026-04-14, the iiko Secure API Gateway is 100% completed and production-ready. This document outlines strategic vectors for future scaling and enterprise hardening.

## 1. Enterprise Secret Management
- **HashiCorp Vault Integration**: Transition from local `keys/` storage and `.env` secrets to a centralized secrets engine with automated RSA key rotation via Vault's Transit engine.
- **mTLS (Mutual TLS)**: Implement cryptographically verified communication between the gateway and iiko upstream servers to ensure a strict trust chain.

## 2. Infrastructure & Data Scaling
- **PostgreSQL Migration**: Move the current SQLite client registry to a dedicated **PostgreSQL** cluster for high availability and multi-region scalability.
- **Redis Cluster**: Horizontal scaling of the Redis storage to support thousands of requests per second with high-availability replication.
- **Service Mesh Integration**: Optimization for Istio/Linkerd to handle internal sidecar communication within a Kubernetes cluster.

## 3. Intelligent Security (AIOps)
- **ML Anomaly Detection**: Integration of an asynchronous analyzer to detect behavioral anomalies (e.g., suspicious request patterns, credential stuffing) using machine learning models.
- **Adaptive Rate Limiting**: Dynamically adjusting client limits based on real-time threat scores rather than static per-IP configurations.

## 4. Developer Experience (DX)
- **Advanced Admin UI**: A React-based management console for real-time monitoring of metrics, managing client credentials, and revoking JWTs instantly.
- **Terraform / Helm Modules**: Standardized deployment templates for AWS, GCP, and Azure environments.

---

## ✅ Completed Strategic Milestones
- [x] **Asynchronous Reverse Proxy Core**: Non-buffering streaming implementation.
- [x] **Zero-Trust JWT (RS256)**: Multi-key rotation support and strict claim validation.
- [x] **Stateful Replay Protection**: Redis-backed JTI tracking.
- [x] **Distributed Rate Limiting**: Redis-backed throttling.
- [x] **RBAC Authorization**: Fine-grained permission model.
- [x] **DB-Backed Registry**: SQLAlchemy 2.0 with Bcrypt security.
- [x] **Refresh Token Flow**: Secure rotation and type separation.
- [x] **Full Observability Stack**: Prometheus + Grafana instrumentation.
