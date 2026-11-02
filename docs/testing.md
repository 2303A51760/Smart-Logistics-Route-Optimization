# Testing & Quality Assurance Guide

## 1. Overview of Test Architecture

The testing strategy covers end-to-end regression across all 15 implementation phases:
- **Unit & Algorithmic Tests**: Great-Circle/Haversine distance calculations, Dijkstra shortest paths, A* search, and Google OR-Tools VRP constraints.
- **Service & ML Validation**: Scikit-Learn Gradient Boosting ETA predictor, multi-horizon demand forecasting, delay risk classifier, and order priority scoring.
- **REST API & RBAC Integration**: Role-Based Access Control verification across `ADMIN`, `LOGISTICS_MANAGER`, and `DRIVER` roles.
- **WebSocket Telemetry & Concurrency**: Real-time driver GPS tracking broadcasts and connection handling.
- **Security & Audit Logs**: Verification of immutable logging on authentication, password changes, route optimization, and operational actions.

---

## 2. Test Suite Execution

### Running the Full Test Suite:
```bash
# Run all 139 tests with coverage
pytest tests/ -v --cov=app --cov-report=term
```

### Running Specific Test Modules:
```bash
# Optimization tests
pytest tests/test_optimization.py

# Route Execution & Tracking tests
pytest tests/test_route_execution.py tests/test_tracking.py

# AI & Machine Learning tests
pytest tests/test_ai_priority.py tests/test_ai_dispatch.py tests/test_ai_delay.py tests/test_ai_forecast.py tests/test_ai_reoptimization.py

# Security & RBAC tests
pytest tests/test_rbac.py tests/test_audit_logs.py tests/test_ai_rbac.py

# Database Persistence tests
pytest tests/test_persistence.py

# Phase 13 & Production Hardening tests
pytest tests/test_phase13_production.py
```

---

## 3. Test Coverage Breakdown

| Module | Test File | Test Cases | Scope |
| :--- | :--- | :--- | :--- |
| **Auth & RBAC** | `test_auth.py`, `test_rbac.py` | 15 | JWT issuance, password hashing, role enforcement, isolation |
| **Core Logistics** | `test_customers.py`, `test_orders.py`, `test_drivers.py`, `test_vehicles.py`, `test_warehouses.py` | 16 | CRUD lifecycles, status transitions, validations |
| **Optimization** | `test_optimization.py` | 8 | Google OR-Tools VRPTW, capacity constraints, multi-vehicle routing |
| **Route Execution** | `test_route_execution.py`, `test_tracking.py` | 15 | Stop transitions, WebSocket location streaming, ETA re-calculation |
| **Maintenance & Alerts**| `test_maintenance.py`, `test_notifications.py` | 8 | Maintenance thresholds, alerts generation, WebSocket notifications |
| **AI ETA & Demand** | `test_eta.py`, `test_forecast.py` | 20 | Gradient Boosting regression, multi-horizon demand forecasting |
| **AI Intelligence** | `test_ai_priority.py`, `test_ai_dispatch.py`, `test_ai_delay.py`, `test_ai_forecast.py`, `test_ai_reoptimization.py`, `test_ai_rbac.py` | 15 | Explainable priority scoring, delay risk, dispatch matching, dynamic routing |
| **Audit & Hardening** | `test_audit_logs.py`, `test_health.py`, `test_phase13_production.py` | 17 | Audit event capture, health/ready probes, metrics, secret validation |
| **Persistence Proof**| `test_persistence.py` | 2 | Real database state retention across independent sessions & engine cycles |
| **E2E Integration** | `test_phase11_e2e.py`, `test_phase14_e2e.py`, `test_driver_dashboard_fix.py` | 13 | Complete multi-step dispatch and execution workflows |
| **Total Backend** | **All Test Files** | **139** | **100% Passing** |

---

## 4. Frontend Testing (Vitest & React Testing Library)

```bash
cd frontend
npm test
```
- **Test Suites**:
  - `src/test/tokenRefresh.test.ts`: Verifies automatic 401 token refresh interceptor, parallel call queueing, and safe redirect to login on expired refresh token.
  - `src/test/auth.test.tsx`: Validates login form UI, credentials submission, token storage in `authStorage`, and error messages.
  - `src/test/protectedRoute.test.tsx`: Tests route protection, redirect of unauthenticated users to `/login`, and rejection of unauthorized roles to `/unauthorized`.
  - `src/test/orders.test.tsx`: Tests order listing, table data rendering, priority badges, empty state UI, and live search filtering.
- **Result**: `4 passed (4 suites), 11 passed (11 tests)`

---

## 5. Frontend Typecheck & Production Build Validation

```bash
cd frontend
npm run lint      # tsc --noEmit
npm run build     # vite build
```
- **Typecheck Result**: `0 errors (TypeScript strict mode enabled)`
- **Build Result**: `✓ 2395 modules transformed. 0 errors. All chunks < 500 kB.`
