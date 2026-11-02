# Smart Logistics & Route Optimization Platform — Project Report

## 1. Abstract
The **Smart Logistics & Route Optimization Platform** is an enterprise-grade, cloud-native dispatch, vehicle routing, and fleet telematics platform designed to optimize last-mile supply chain operations. The platform integrates deterministic operations research—specifically the Capacitated Vehicle Routing Problem with Time Windows (VRPTW) solved via Google OR-Tools—with machine learning for journey duration prediction (ETA), autoregressive demand forecasting, and explainable AI-driven dispatch decision support. 

Built with a high-performance **FastAPI** backend, **SQLAlchemy 2.0 async** persistence on **PostgreSQL 16**, **Redis 7** telemetry caching, and a responsive **React 18 + TypeScript** Single-Page Application (SPA) with route-level code splitting, the system enforces strict Role-Based Access Control (RBAC), end-to-end data integrity across 8 database revisions, and tamper-evident audit logging with automatic PII redaction.

---

## 2. Problem Statement
Modern logistics networks face compounding operational challenges in last-mile delivery:
1. **Inefficient Route Topology**: Manual or greedy nearest-neighbor route planning causes excessive mileage, fuel waste, driver overtime, and frequent SLA window breaches.
2. **Inflexible Vehicle Allocation**: Dispatchers struggle to balance heterogeneous vehicle payload capacities, driver shift constraints, and urgent priority consignments in real time.
3. **Black-Box ETAs**: Static speed-over-distance heuristics fail to account for waypoint density, time of day, weather, or real-time road conditions, resulting in poor customer visibility.
4. **Data Fragmentation & Security Risks**: Lack of unified, role-governed platforms leads to operational blind spots, unmonitored driver tracking, and vulnerabilities from default credential deployments.

---

## 3. Objectives
- **Algorithmic Fleet Optimization**: Automate multi-vehicle route planning using Google OR-Tools, reducing transit mileage and honoring customer delivery windows and payload capacities.
- **Data Persistence & Architectural Rigor**: Transition entirely away from in-memory mock stores to pure PostgreSQL 16 persistence using asynchronous SQLAlchemy 2.0 ORM and Alembic migrations.
- **Predictive Intelligence**: Deploy machine learning models for Gradient-Boosted ETA prediction and multi-horizon demand forecasting with analytical fallback resilience.
- **Real-Time Telemetry**: Provide a bi-directional WebSocket tracking infrastructure for streaming driver GPS coordinates, backed by Redis and rendered on an interactive Leaflet fleet map.
- **Hardened Security & Compliance**: Enforce strict JWT-based RBAC (`ADMIN`, `LOGISTICS_MANAGER`, `DRIVER`), fail-safe production secret checks, rate limiting, and an immutable security audit trail with PII redaction.
- **Production-Grade Verification**: Achieve zero TypeScript errors, 100% test passing rates across unit, integration, and containerized smoke test suites, and sub-500 kB frontend bundle sizes.

---

## 4. System Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │               React 18 + TypeScript SPA                │
                    │       (Vite, TailwindCSS, Leaflet Interactive Maps)    │
                    │         • Route-Level Lazy Loading & Code Splitting    │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                HTTP REST /api/v1│   WebSocket /ws/tracking
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │                    FastAPI Gateway                     │
                    │   (Async ASGI, CORS, Security Headers, Rate Limiter)   │
                    │   • JWT Auth / RBAC Dependencies (Admin/Manager/Driver) │
                    └───────┬───────────────────┬───────────────────┬────────┘
                            │                   │                   │
                            ▼                   ▼                   ▼
                 ┌──────────────────┐┌──────────────────┐┌──────────────────┐
                 │  Optimization    ││  ML & AI Engines ││ Core Operations  │
                 │  Google OR-Tools ││  • ETA Regressor ││ • Order Lifecycle│
                 │  • VRPTW Solver  ││  • Demand Forecast││ • Fleet & Hubs  │
                 │  • Haversine Dist││  • Delay Risk    ││ • Driver Cockpit │
                 │  • Capacity Check││  • Dispatch Match││ • Audit Logger   │
                 └─────────┬────────┘└─────────┬────────┘└─────────┬────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                 ┌───────────────────────────────────────────────────────────┐
                 │                    Data Persistence                       │
                 │   • PostgreSQL 16 (SQLAlchemy 2.0 AsyncSession, Alembic)  │
                 │   • Redis 7 (Telemetry Caching, Live Driver Positions)    │
                 └───────────────────────────────────────────────────────────┘
```

### Architecture Highlights:
- **Asynchronous I/O**: The backend uses Python `asyncio` with `asyncpg` connection pooling (`AsyncAdaptedQueuePool`), allowing non-blocking database operations under high concurrent dispatch loads.
- **Decoupled Client Architecture**: The frontend communicates via typed REST endpoints for operational queries and resilient WebSockets for telemetry streaming with auto-reconnect.
- **Containerization**: Multi-stage Docker builds (`docker/Dockerfile.backend` with Python 3.11-slim and `docker/Dockerfile.frontend` with Node 20 / Nginx 1.27) orchestrated through Docker Compose.

---

## 5. Technology Stack

| Layer | Technologies | Purpose |
|---|---|---|
| **Backend Framework** | Python 3.11 / 3.13, FastAPI 0.110+, Starlette, Pydantic v2 | High-performance async API gateway, schema validation, dependency injection. |
| **Database & ORM** | PostgreSQL 16, SQLAlchemy 2.0 (asyncio), asyncpg, Alembic | ACID relational persistence, migration management, relational integrity. |
| **Caching & Messaging** | Redis 7, redis-py (async) | Real-time driver location buffer, rate-limit state tracking. |
| **Optimization Engine** | Google OR-Tools 9.9+ | Mixed-Integer Programming & metaheuristics for multi-vehicle VRPTW. |
| **Machine Learning** | Scikit-Learn 1.4+, NumPy, Pandas, Joblib | Gradient Boosting, Random Forest, Feature pipelines for ETA & Demand. |
| **Authentication & Security** | PyJWT, Cryptography, Passlib, Bcrypt | JWT access/refresh lifecycle, bcrypt salt hashing, PII masking. |
| **Frontend Framework** | React 18, TypeScript 5 (Strict), Vite 5 | Reactive SPA, strict static typing, route code-splitting. |
| **UI & Mapping** | TailwindCSS, Lucide Icons, Leaflet, React-Leaflet, Recharts | Modern dashboard UI, interactive fleet mapping, analytical charting. |
| **Testing & Quality** | Pytest, Pytest-Asyncio, Ruff, Vitest, Testing Library | Multi-layer test automation, static linting, component testing. |
| **Deployment** | Docker, Docker Compose, Nginx (Alpine) | Multi-container production virtualization and reverse proxying. |

---

## 6. Functional Modules & Capabilities

1. **Authentication & RBAC (`/api/v1/auth`)**:
   - Issue JWT Access (15-min expiry) and Refresh (7-day expiry) tokens.
   - Transparent frontend token refresh on HTTP 401 with replay queue.
   - Three distinct roles: `ADMIN`, `LOGISTICS_MANAGER`, and `DRIVER`.
2. **Order Management (`/api/v1/orders`)**:
   - Order creation, consignment tracking, pickup/delivery coordinates, package dimensions, weights, priority tiers (`LOW`, `MEDIUM`, `HIGH`, `URGENT`), and lifecycle status (`PENDING`, `ASSIGNED`, `IN_TRANSIT`, `DELIVERED`, `CANCELLED`).
3. **Depot & Customer Registry (`/api/v1/warehouses`, `/api/v1/customers`)**:
   - Geocoded depot locations, operating capacities, customer profiles, and service delivery history.
4. **Fleet & Driver Management (`/api/v1/vehicles`, `/api/v1/drivers`)**:
   - Vehicle registration, capacity bounds (kg), fuel type, odometer, and driver license verification. Drivers can view only their own assigned vehicle and routes.
5. **Route Execution Cockpit (`/api/v1/routes`, `/driver/*`)**:
   - Dynamic route generation, sequenced `RouteStop` checkpoints, waypoint arrival/departure timestamps, and proof-of-delivery logging.
6. **OR-Tools Optimization Console (`/api/v1/optimization`)**:
   - On-demand multi-vehicle route optimization factoring depot locations, consignment demands, vehicle capacities, and time windows.
7. **Real-Time GPS Tracking (`/api/v1/tracking`, `/ws/tracking`)**:
   - High-frequency WebSocket streaming endpoint for mobile drivers with Redis coordinate caching and Leaflet live vehicle marker animation.
8. **Predictive ETA Analytics (`/api/v1/eta`)**:
   - Scikit-Learn inference predicting travel time in minutes based on distance, stop order, time of day, traffic index, and weather index, with analytical fallback.
9. **Demand Forecasting (`/api/v1/forecast`)**:
   - Time-series demand forecasting across 1, 7, 14, and 30 days, calculating fleet capacity gaps and driver utilization recommendations.
10. **Fleet Maintenance & Alerts (`/api/v1/maintenance`, `/api/v1/notifications`)**:
    - Maintenance schedule tracking (`SCHEDULED`, `IN_PROGRESS`, `COMPLETED`), maintenance cost logging, and automated alerts for overdue servicing.
11. **AI Operations Support (`/api/v1/ai`)**:
    - Explainable order priority scoring (0–100), delivery delay risk assessment, intelligent driver-vehicle dispatch ranking, and dynamic route re-optimization.
12. **Tamper-Evident Audit Logging (`/api/v1/audit-logs`)**:
    - Immutable security audit records capturing user logins, order mutations, route dispatching, and system events with automatic PII masking (passwords, emails, tokens).

---

## 7. Algorithms & Operations Research

### A. Vehicle Routing Problem with Time Windows (VRPTW)
The optimization engine formulates fleet dispatch as a Capacitated Vehicle Routing Problem with Time Windows (VRPTW) using **Google OR-Tools**:
- **Objective Function**: Minimize total travel distance across all deployed vehicles:
  $$\min \sum_{k \in V} \sum_{i \in N} \sum_{j \in N} c_{ij} \cdot x_{ijk}$$
  where $c_{ij}$ is the Haversine distance between waypoints $i$ and $j$, and $x_{ijk} \in \{0, 1\}$ indicates whether vehicle $k$ traverses arc $(i, j)$.
- **Constraints**:
  1. *Subtour Elimination*: Standard flow conservation ensures all routes start and end at the depot warehouse.
  2. *Capacity Constraint*: Cumulative package weight on vehicle $k$ cannot exceed vehicle maximum capacity:
     $$\sum_{i \in N} q_i \cdot y_{ik} \le Q_k, \quad \forall k \in V$$
  3. *Time Window Constraints*: Arrival time at waypoint $i$ must satisfy $e_i \le t_i \le l_i$. Vehicle waiting time is allowed if arrival precedes $e_i$.
- **Heuristics**:
  - *First Solution Strategy*: `PARALLEL_CHEAPEST_INSERTION` builds routes simultaneously to avoid greedy starvation of distant stops.
  - *Local Search Metaheuristic*: `GUIDED_LOCAL_SEARCH` escapes local minima by penalizing frequently traversed arcs.

### B. Machine Learning ETA Prediction
- **Model Architecture**: Scikit-Learn `GradientBoostingRegressor` and `RandomForestRegressor` ensemble.
- **Features**: `distance_km`, `stop_sequence`, `hour_of_day`, `day_of_week`, `traffic_congestion_index` (1.0–3.0), `weather_severity` (0.0–1.0), `package_weight_kg`.
- **Performance**: Real training output yields Mean Absolute Error (MAE) of **1.09 minutes** across validation sets.
- **Analytical Fallback**: If model artifacts are missing, the system uses a calibrated analytical model ($v_{\text{urban}} = 28\text{ km/h} + 4.5\text{ min/stop}$) ensuring uninterrupted service.

### C. Autoregressive Demand Forecasting
- **Feature Pipeline**: Autoregressive lag features (lag-1, lag-7, lag-14, 7-day rolling mean, rolling standard deviation) combined with calendar features (day of week, month, weekend indicator).
- **Inference**: Recursive multi-step forecasting across 1, 7, 14, and 30-day horizons.
- **Capacity Gap Analysis**: Compares predicted order demand against active vehicle fleet payload capacity to flag `OVER_CAPACITY`, `HIGH_UTILIZATION`, or `UNDER_UTILIZED` operating regimes.

### D. Multi-Factor Explainable Order Priority Scoring
- **Formulation**: Computes a continuous priority score $S \in [0, 100]$:
  $$S = w_1 \cdot \text{WeightFactor} + w_2 \cdot \text{SLABreachFactor} + w_3 \cdot \text{CustomerTier} + w_4 \cdot \text{DistanceFactor}$$
- **Output**: Classifies orders into `LOW` (<40), `MEDIUM` (40–69), `HIGH` (70–89), or `CRITICAL` ($\ge$90) with human-readable reasoning explanations for dispatchers.

---

## 8. Database Schema & Migration History

The relational database is versioned through 8 sequential Alembic migrations:
1. `001_initial_schema`: `users`, `warehouses`, `customers`, `drivers`, `vehicles`, `orders` tables with foreign keys and enum constraints.
2. `002_add_indexes`: B-tree composite indexes on `orders(status, customer_id)`, `orders(delivery_window_start)`, and spatial coordinate indexes.
3. `003_create_route_execution_tables`: `routes` and `route_stops` tracking driver assignments, actual vs planned travel time, and stop sequences.
4. `004_create_maintenance_and_health_tables`: `vehicle_maintenance` records, schedules, and costs.
5. `005_create_notifications_table`: `notifications` table for dispatch and system alerts.
6. `006_create_audit_logs_table`: Append-only `audit_logs` table for tracking security and operational actions.
7. `007_create_ai_recommendations_table`: `ai_recommendations` table storing dispatch rankings and confidence scores.
8. `008_create_delivery_points_table`: `delivery_points` table supporting arbitrary multi-stop routing topologies.

---

## 9. Security & Governance Design

- **JWT Token Architecture**: Short-lived access tokens signed with HMAC-SHA256, paired with refresh tokens. The frontend API client queues 401-intercepted requests, performs automatic token exchange, and replays pending calls seamlessly.
- **Password Protection**: Passwords are salted and hashed using `bcrypt` (work factor 12).
- **Production Startup Hardening**: Settings validation halts application startup if default secrets or passwords (`dev-insecure-...`, `secret`, `changethis`) are detected when `ENVIRONMENT=production`.
- **Rate Limiting**: Sliding-window rate limiters protect authentication endpoints (5 req/min) and computationally heavy AI/Optimization endpoints (30 req/min).
- **Audit Logging with PII Redaction**: The audit logging engine sanitizes request bodies, stripping passwords, tokens, API keys, and sensitive contact information before committing to PostgreSQL.

---

## 10. Verification Results & Quality Metrics

All metrics represent real, verified command execution on the finalized codebase:

| Verification Metric | Target Benchmark | Actual Measured Result | Status |
|---|---|---|---|
| **Backend Test Suite** | 100% Pass | **139 passed**, 0 failed in 151.05s | **PASSED** |
| **Mock Store Elimination** | 0 references | **0 occurrences** of `logistics_store` | **PASSED** |
| **Backend Code Linting** | Zero errors | **0 errors** (`ruff check backend/app tests/`) | **PASSED** |
| **Frontend Strict Typecheck** | Zero errors | **0 errors** (`tsc --noEmit` in strict mode) | **PASSED** |
| **Frontend Automated Tests** | 100% Pass | **4 suites passed, 11 passed (11)** in 24.03s | **PASSED** |
| **Frontend Bundle Splitting** | < 500 kB/chunk | **All chunks < 500 kB** (Largest: 410 kB vendor-recharts) | **PASSED** |
| **Docker Compose Stack** | All healthy | **4/4 containers healthy** (`postgres`, `redis`, `backend`, `frontend`) | **PASSED** |
| **Container Smoke Tests** | 100% Pass | **8/8 operational steps passed** on real PostgreSQL | **PASSED** |
| **Cold Restart Persistence** | Data preserved | **Order retrieved intact after container restart** | **PASSED** |

---

## 11. Limitations & Future Work

### Current Limitations:
1. **Haversine Distance Approximation**: Route optimization calculates distances using great-circle Haversine formulas rather than real-world road network distance matrices (e.g., OpenStreetMap / OSRM API).
2. **Synchronous VRP Solving**: Large optimization jobs with hundreds of waypoints block the HTTP request thread up to the 30-second timeout; very large instances would benefit from a Celery/RabbitMQ asynchronous job queue.
3. **Single-Region Telemetry**: Telemetry streaming is optimized for single-region Redis clusters; global fleets would require distributed Redis replication.

### Recommended Future Work:
- **OSRM / Valhalla Integration**: Replace Haversine distance calculations with real-world turn-by-turn routing profiles factoring one-way streets, truck height limits, and bridge tolls.
- **Dynamic In-Route Re-Dispatch**: Implement live VRP insertion where new on-demand customer orders are injected dynamically into active vehicle routes without restarting the entire schedule.
- **IoT Fleet OBD-II Telematics**: Connect vehicle on-board diagnostics (fuel consumption, engine temperature, tire pressure) directly to the maintenance alert engine via MQTT.

