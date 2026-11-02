# Security Architecture & Hardening Guide

## 1. Authentication & Session Management

- **Password Hashing**: Uses `passlib` with `bcrypt` (12 rounds) and automatic salts.
- **JWT Architecture**:
  - Stateless JSON Web Tokens signed with HMAC-SHA256 (`HS256`).
  - Short-lived Access Tokens (default: 60 minutes) combined with Refresh Tokens (default: 7 days).
  - Explicit logout and token invalidation via Redis token blacklisting.
- **Role-Based Access Control (RBAC)**:
  - Three distinct roles: `ADMIN`, `LOGISTICS_MANAGER`, `DRIVER`.
  - Enforced at the dependency injection level using `require_admin`, `require_manager`, and `get_current_user`.
  - Strict driver data isolation preventing drivers from viewing or updating records outside their assigned manifest.

---

## 2. API Security & Defense in Depth

- **CORS Protection**: Explicit domain allowlist (`BACKEND_CORS_ORIGINS`) rejecting untrusted origins with credential validation.
- **Security Headers**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- **Rate Limiting**:
  - Sliding-window throttler enforcing requests per IP/endpoint per minute.
  - Automatic graceful degradation from Redis counters to thread-safe in-memory stores.
- **Global Error Sanitization**:
  - Unhandled 500 exceptions sanitize stack traces and sensitive internals, returning a correlated `request_id` (`X-Request-ID`).
- **Input Validation**:
  - All incoming HTTP payloads are validated against strict Pydantic v2 schemas.
  - SQL Injection prevention through SQLAlchemy parameterized queries and ORM query builders.

---

## 3. Enterprise Audit Logging

- **Immutable Audit Trail**: All authentication events, role checks, password changes, route optimization runs, vehicle maintenance updates, and AI decisions are recorded to the `audit_logs` table.
- **PII & Secret Sanitization**:
  - Built-in audit filter redacts passwords, bearer tokens, API secrets, and hashes prior to storage (`[REDACTED]`).
- **Admin Audit Portal**: Dedicated interface (`/audit-logs`) with full-text search, action filtering, date ranges, and CSV export.

---

## 4. Environment & Secrets Management

- **No Hardcoded Secrets**: All keys, passwords, and connection strings are sourced strictly via environment variables (`app/core/config.py`).
- **Git Hygiene**: `.gitignore` comprehensively excludes `.env`, `*.log`, `*.db`, `__pycache__`, `.pytest_cache/`, `node_modules/`, and `dist/`.
