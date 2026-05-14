# ISAG — Future Roadmap & Scaling Vectors

As of 2026-05-14, the iiko Secure API Gateway is 100% completed, hardened, and includes a full-featured Admin Dashboard. This document outlines strategic vectors for future scaling and enterprise hardening.

## 1. Enterprise Secret Management
- **HashiCorp Vault Integration**: Transition from local `keys/` storage and `.env` secrets to a centralized secrets engine with automated RSA key rotation.
- **mTLS (Mutual TLS)**: Implement cryptographically verified communication between the gateway and iiko upstream servers.

## 2. Infrastructure & Data Scaling
- **PostgreSQL Migration**: Move the current SQLite client registry to a dedicated **PostgreSQL** cluster for high availability.
- **Redis Cluster**: Horizontal scaling of the Redis storage to support thousands of requests per second.
- **Service Mesh Integration**: Optimization for Istio/Linkerd within a Kubernetes cluster.

## 3. Intelligent Security (AIOps)
- **ML Anomaly Detection**: Integration of an asynchronous analyzer to detect behavioral anomalies (e.g., credential stuffing) using machine learning.
- **Adaptive Rate Limiting**: Dynamically adjusting client limits based on real-time threat scores.

## 4. Operational Hardening
- **SAST/DAST Integration**: Full automation of Static and Dynamic Application Security Testing in the CI/CD pipeline.
- **Multi-Region Deployment**: Global distribution of gateway nodes with latency-based routing.

---

## ✅ Completed Strategic Milestones
- [x] **Asynchronous Reverse Proxy Core**: Non-buffering streaming implementation.
- [x] **Zero-Trust JWT (RS256)**: Multi-key rotation support and strict claim validation.
- [x] **Stateful Replay Protection**: Redis-backed JTI tracking.
- [x] **Distributed Rate Limiting**: Redis-backed throttling.
- [x] **Advanced Admin Dashboard**: React-based console for real-time monitoring and management.
- [x] **Partner Hub**: Onboarding wizard and client credential management.
- [x] **Full Observability Stack**: Prometheus + Grafana instrumentation.
- [x] **Audit Trail**: DB-backed logging of all administrative and security events.
- [x] **Frontend Stability**: Robust interceptors for session and token management.
- [x] **Dockerized Cluster**: Full orchestration of 6 integrated services.
