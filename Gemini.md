Gemini.md — AI Operating & Security Architecture Guide (Hardened Edition)

Project: iiko Secure API Gateway (ISAG)
Author: Karzhaubayev Sanzhar
Security Level: Production-Oriented

1. Architectural Philosophy

The system MUST follow:

Secure-by-Design

Defense-in-Depth

Zero-Trust Model

Fail-Closed Principle

Least Privilege Principle

All external traffic is considered hostile by default.

2. Fixed Security Pipeline (Non-Negotiable)

All incoming requests MUST follow this order:

TLS Termination
→ Request Size Validation
→ Rate Limiting
→ JWT Validation
→ Replay Protection
→ RBAC Authorization
→ Secure Proxy Forwarding
→ Audit Logging
→ Response Filtering

No stage may be bypassed.

3. Cryptography & Key Management (CRITICAL)
JWT Requirements

Algorithm: RS256 (asymmetric only)

Signature verification is mandatory

Validate:

exp

nbf

iss

aud

sub

Key Management Rules

Private keys MUST NOT be hardcoded

Keys must be loaded from secure environment or mounted secret

Support key rotation

Support multiple public keys (kid header)

Validate JWT header alg

Reject tokens with unexpected algorithms

Time Handling

Allow configurable clock skew (≤ 60s)

Reject expired tokens strictly

4. Replay Protection

Gateway MUST mitigate replay attacks:

Require jti

Optional nonce tracking (in-memory or Redis)

Expire replay cache aligned with token expiration

5. Input Validation & Injection Protection

Strict Pydantic schemas

extra = "forbid"

Maximum body size limit

Content-Type validation

Reject malformed JSON

Validate query parameters explicitly

Prevent:

SQL injection

Header injection

CRLF injection

Path traversal

JSON injection

6. Rate Limiting & Abuse Protection

Must implement:

Per-IP rate limits

Per-user rate limits

Burst + sustained model

Return HTTP 429

Memory-safe implementation

No unbounded dictionaries

Optional:

Sliding window algorithm

Redis-backed limiter (production mode)

7. Secure Proxy Hardening

Proxy layer MUST:

Strip hop-by-hop headers

Remove client-supplied X-Forwarded-* headers

Reconstruct forwarding headers internally

Enforce upstream timeout

Limit max response size

Disable automatic redirects

Prevent SSRF (whitelist upstream hosts)

Use connection pooling

8. Transport & Headers Security

Gateway MUST enforce:

HTTPS only

HSTS

X-Frame-Options: DENY

X-Content-Type-Options: nosniff

Strict CSP

Referrer-Policy

Minimal CORS policy (explicit origin allowlist)

Never use:

CORS "*"

Credentials with wildcard origins

9. Configuration Security

Use pydantic-settings

Fail startup if required env variables missing

Validate configuration types

No default insecure fallback values

Separate dev and prod configs

Required config validation:

JWT issuer

JWT audience

Public key path

Rate limits

Upstream base URL

10. Error Handling Model

Gateway MUST:

Never expose stack traces

Never expose internal file paths

Use unified error schema

Log detailed internal error

Return sanitized client response

Example structure:

{
  "error": "unauthorized",
  "message": "Invalid token",
  "request_id": "uuid"
}
11. Logging & Observability

Logging MUST be:

Structured (JSON preferred)

With request_id

With user_id (if available)

Without secrets

Without full JWT tokens

Mask:

Authorization headers

Tokens

API keys

Observability Requirements:

/health endpoint

/ready endpoint

Metrics-compatible structure

Correlation ID propagation

12. DoS & Resource Protection

Gateway MUST implement:

Max request body size

Upstream timeout

Connection timeout

Idle connection timeout

Concurrency limits

Protection against large payload attacks

Fail fast under overload.

13. Threat Awareness Model

AI-generated code must consider:

JWT forgery

Key confusion attack

Replay attack

Brute force

Rate abuse

Header spoofing

SSRF

Injection attacks

Misconfigured CORS

Resource exhaustion

Insecure defaults

Security must fail closed.

14. Code Quality Standards

All generated code MUST:

Follow PEP 8

Include type hints

Include docstrings

Use dependency injection

Avoid global mutable state

Use structured logging

Include security comments where relevant

No pseudocode allowed.

15. Testing Requirements (Mandatory)

For every feature generate:

Unit tests (pytest)

Negative tests

Expired token test

Invalid signature test

Missing claim test

Rate limit exceed test

Permission denied test

Tests must be runnable and realistic.

16. Production Hardening Expectations

Gateway must assume:

Hostile traffic

Automated scanning

Brute-force attempts

Credential stuffing attempts

Misconfigured clients

Malformed requests

Security logic must be deterministic and strict.

17. Definition of High-Quality

Code is high-quality only if:

Secure

Modular

Testable

Observability-ready

Production-realistic

Follows layered architecture

Enforces security pipeline strictly

18. AI Operational Rule

If uncertain:

State assumptions

Ask clarifying questions

Default to safest configuration

Never relax security silently.