<div align="center">

# 🛡️ ISAG — iiko Secure API Gateway

**A high-performance, asynchronous reverse proxy that secures integrations with the iiko API.**
Built on a **Zero Trust** model, layered with **Defense in Depth**, and shipped with a modern administration panel.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-RS256-000000?logo=jsonwebtokens&logoColor=white)

</div>

---

## Overview

ISAG (iiko Secure API Gateway) is a high-performance asynchronous reverse proxy designed to secure
integrations with the iiko API. It operates on a **Zero Trust** model — every request is
cryptographically verified and strictly authorized — and applies **Defense-in-Depth** principles
across the request pipeline. It ships with a polished, real-time administration panel.

## ✨ Key Features

- **Zero Trust architecture** — every request is cryptographically verified (JWT RS256) and strictly authorized through an **RBAC** mechanism.
- **Glassmorphism admin panel** — a premium React/Vite dashboard with dynamic animations, smooth transitions, and a responsive, adaptive design.
- **Real-time Threat Feed** — an interactive *Live Event Ticker* surfaces recent security events (token revocations, rate-limit breaches) with instant visual feedback.
- **Audit logging** — comprehensive JSON logging of administrative actions (client creation, secret rotation, status changes) with IP address capture.
- **Secret rotation** — secure, on-demand lifecycle management of client credentials directly from the UI, with zero service interruption.

---

## 🛡️ Security Features

- **Granular access & scopes** — each client is assigned specific API scopes (e.g. `orders:read`), guaranteeing access only to the endpoints it actually needs.
- **Rate limiting** — configurable global and per-client request-rate limits prevent abuse, resource exhaustion, and DoS attacks.
- **Replay protection** — strict JWT ID (JTI) tracking prevents reuse of intercepted tokens.
- **JWT RS256** — asymmetric signing: the gateway verifies tokens with the public key while the private signing key never leaves the auth boundary.

## 🏗️ Architecture

```
Client → [ISAG Gateway (FastAPI)] → iiko API
            │
            ├── JWT RS256 verification + JTI replay protection
            ├── RBAC scope authorization
            ├── Redis-backed rate limiting
            ├── Audit logging (JSON + IP capture)
            └── React/Vite admin panel + live threat feed
```

**Stack:** FastAPI backend · React/Vite frontend (Nginx) · PostgreSQL · Redis · Docker Compose

---

## 🚀 Quick Start (One-Click Launch)

Make sure **Docker** and **Docker Compose** are installed.

**1. Clone and configure**
```bash
git clone https://github.com/sanzhartech/iiko-Secure-API-Gateway--ISAG-.git
cd iiko-Secure-API-Gateway--ISAG-
```

**2. Generate RSA keys** — generate secure keys for JWT signing before launch:
```bash
python scripts/generate_keys.py
```

**3. Launch the stack** — deploy PostgreSQL, the Redis cache, the FastAPI backend, and the React/Nginx frontend:
```bash
docker-compose up -d --build
```

**4. Access the dashboard** — open `http://localhost` and sign in with the default credentials defined in your `docker-compose.yml`.

---

## 🛠️ Live Demo & Attack Simulation

To showcase the gateway's defensive capabilities in real time during a presentation, run `demo_attack.py`:

```bash
# Requires the python requests and colorama libraries
pip install requests colorama
python demo_attack.py
```

The script will:
- Send **valid requests** (displaying the "network heartbeat").
- Trigger an aggressive request burst to fire `RATE_LIMIT_EXCEEDED` (a red glow appears in the dashboard event feed).
- Send **forged tokens** to demonstrate `UNAUTHORIZED` blocking.

Watch the admin panel react to these events live.

---

## 📑 Documentation

For a deep understanding of the system, see:

- **Technical architecture & request lifecycle** — design decisions, security pipeline stages, and core data structures.
- **Deployment & operations guide** — Docker setup, manual launch, Nginx configuration, and deployment procedures.
- **Security mechanisms & specifications** — cryptography, JWT validation, rate limiting, and replay protection in detail.
- **Environment configuration guide** — full specification of environment variables and settings.
- **Troubleshooting guide** — diagnostics, recovery steps, and solutions to common issues.
- **Testing & quality report** — test results, code coverage, load tests, and attack simulations.
- **Mathematical & cryptographic foundations** — RS256 security proofs, RPS limiting algorithms, and audit database schemas.

---

## 📊 Observability

- Real-time security event stream surfaced through the **Live Event Ticker**.
- Structured **JSON audit logs** with IP capture for every administrative action.
- CI pipeline (ISAG Test Suite) validating the build on every push to `main`.

---

**Author:** Sanzhar Karzhaubay
**Status:** 100% Complete · Defended · Fully Documented

## License

MIT
