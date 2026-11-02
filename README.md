# Smart Logistics & Route Optimization Platform

[![CI/CD Pipeline](https://github.com/2303A51760/Smart-Logistics-Route-Optimization/actions/workflows/ci.yml/badge.svg)](https://github.com/2303A51760/Smart-Logistics-Route-Optimization/actions)
[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-139%20Passed%20%2F%200%20Failed-brightgreen.svg)](https://github.com/2303A51760/Smart-Logistics-Route-Optimization/actions)
[![Frontend Tests](https://img.shields.io/badge/Frontend%20Tests-11%20Passed%20%2F%200%20Failed-brightgreen.svg)](https://github.com/2303A51760/Smart-Logistics-Route-Optimization/actions)
[![TypeScript](https://img.shields.io/badge/TypeScript-Strict%20Zero--Errors-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20TypeScript-61DAFB.svg)](https://reactjs.org/)
[![OR-Tools](https://img.shields.io/badge/Optimization-Google%20OR--Tools-blue.svg)](https://developers.google.com/optimization)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, cloud-native **Intelligent Logistics Dispatch, Dynamic Route Optimization & Real-Time Telemetry Platform**. 

The system solves complex last-mile fleet dispatch challenges by combining deterministic Vehicle Routing Problem (VRP) optimization algorithms with predictive machine learning and explainable AI decision support. Powered by **PostgreSQL 16** persistence via **SQLAlchemy 2.0 async**, **Alembic migrations (001–008)**, **Redis 7** telemetry caching, **Google OR-Tools** solver, and **React 18 + TypeScript** with route-level code splitting.

---

## ⚡ Quick Start

Get the complete platform running locally either using Docker Compose (Option A) or natively with local Python and Node.js (Option B):

### Option A: Docker Compose (Recommended — Under 5 Minutes)

#### 1. Clone & Configure Environment
```bash
git clone https://github.com/2303A51760/Smart-Logistics-Route-Optimization.git
cd "Smart Logistics & Route Optimization"
cp .env.example .env
```

#### 2. Launch Multi-Container Stack
```bash
docker compose up --build -d
```
*This builds and starts PostgreSQL 16, Redis 7, the FastAPI backend (port 8000), and the React Nginx frontend (port 3000). In development mode, the container entrypoint automatically executes database migrations (`alembic upgrade head`) and seeds demo data.*

#### 3. (Optional) Manual Migration & Seeding Verification
```bash
# Verify or re-run database migrations
docker compose exec -w /app/backend backend alembic upgrade head

# Seed initial NYC demo hubs, customers, drivers, vehicles, and orders (idempotent)
docker compose exec backend python scripts/seed_demo_data.py
```

#### 4. Access Applications
- **Frontend Web Application**: [http://localhost:3000](http://localhost:3000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **System Health & Telemetry Probe**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Option B: Local Native Setup (Without Docker)

#### Prerequisites:
- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (running on `localhost:5432`)
- Redis 7 (running on `localhost:6379`)

#### 1. Backend Setup
```bash
# Create & activate virtual environment
python -m venv backend/.venv
# Windows PowerShell:
.\backend\.venv\Scripts\Activate.ps1
# Linux/macOS:
source backend/.venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Apply Alembic database migrations
cd backend
alembic upgrade head
cd ..

# Seed demo data (idempotent)
python scripts/seed_demo_data.py

# Launch FastAPI backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend --reload
```

#### 2. Frontend Setup
```bash
# In a new terminal:
cd frontend
npm install
npm run dev
```
*Frontend will be accessible at [http://localhost:5173](http://localhost:5173).*

---

## 👥 Demo Walkthrough per Role

The database comes pre-seeded with three standard demo accounts matching the platform's RBAC matrix:

| Role | Email | Password | Primary Capabilities & Interfaces |
| :--- | :--- | :--- | :--- |
| **👑 ADMIN** | `admin@example.com` | `Admin@123456` | Full platform governance, user management, immutable audit logs (`/audit-logs`), system health telemetry (`/health`), and global alert configurations. |
| **🚚 LOGISTICS_MANAGER** | `manager@example.com` | `Manager@123456` | Order dispatching, Google OR-Tools multi-vehicle route optimization (`/optimization`), live Leaflet fleet map (`/map`), ML demand forecasts (`/demand`), fleet maintenance (`/maintenance`), and AI dispatch pairing. |
| **📍 DRIVER** | `driver@example.com` | `Driver@123456` | Mobile-responsive driver cockpit (`/driver/dashboard`), assigned route execution (`/driver/routes/:id`), real-time GPS location streaming (`/ws/tracking`), stop status updates, and digital proof-of-delivery. |

### Walkthrough Steps:

1. **Log in as Logistics Manager** (`manager@example.com`):
   - Navigate to **Orders** (`/orders`) to inspect pending consignments.
   - Click **Run Optimization** in the Optimization Console (`/optimization`) to execute the Google OR-Tools VRPTW solver across active orders and vehicles.
   - Inspect the **Live Fleet Map** (`/map`) to view depot hubs, delivery markers, and active vehicle polyline routes.
   - Check **AI Insights** (`/ai-insights`) for explainable order priority rankings and vehicle-driver compatibility match scores.

2. **Log in as Driver** (`driver@example.com`):
   - Open your assigned delivery route in **Driver Routes** (`/driver/routes`).
   - Start your route and transition waypoints from `PENDING` $\rightarrow$ `IN_TRANSIT` $\rightarrow$ `COMPLETED`.
   - Your telemetry is automatically streamed via WebSocket to the central dispatch map.

3. **Log in as Admin** (`admin@example.com`):
   - Navigate to **Audit Logs** (`/audit-logs`) to review immutable, tamper-evident security audit logs capturing every user login, route optimization, order change, and AI dispatch decision with automatic PII redaction.
   - Inspect the live system status, database connection pools, and Redis health.

---

## 🌟 Key Subsystems & Features

- **🔐 Enterprise Authentication & RBAC**: JWT Access/Refresh tokens with `bcrypt` password hashing and role-based access control (`ADMIN`, `LOGISTICS_MANAGER`, `DRIVER`). Transparent 401 token refresh queue.
- **💾 Real Relational Persistence**: PostgreSQL 16 schema powered by SQLAlchemy 2.0 `AsyncSession` with 8 Alembic migrations (`001_create_users_table` through `008_create_delivery_points_table`). Pure database persistence with zero reliance on in-memory dictionary stores.
- **🌱 Idempotent Seeding & Retraining**: Standalone CLI seeder `scripts/seed_demo_data.py` safe to run multiple times, and reproducible ML training pipeline `scripts/train_models.py`.
- **🚀 Deterministic Route Optimization**: Multi-vehicle routing (VRPTW & CVRP) powered by **Google OR-Tools** enforcing vehicle capacities, delivery time windows, shift limits, and maximum distance constraints.
- **📡 Real-Time Telemetry & Tracking**: High-throughput WebSocket server (`/ws/tracking`) broadcasting live driver GPS coordinates with Redis-backed caching and Leaflet map rendering.
- **⏱️ Machine Learning ETA Prediction**: Scikit-Learn Gradient Boosting Regressor predicting delivery ETAs based on traffic index, weather severity, transit distance, and waypoint density.
- **📈 Multi-Horizon Demand Forecasting**: Autoregressive forecasting for 1, 7, 14, and 30-day horizons with confidence intervals and peak load analysis.
- **🛠️ Fleet Maintenance & Intelligent Alerts**: Preventive maintenance tracking with automated alerts for overdue servicing, vehicle overload, and delayed routes.
- **🧠 AI Decision Support & Dispatch Matching**: Explainable order priority scoring (0–100), delivery delay risk classification, automated driver-vehicle dispatch pairings, and dynamic route re-optimization.
- **🛡️ Immutable Security & Audit Logging**: Append-only audit logger capturing security events, route optimizations, and AI decisions with automatic PII redaction. Fails safe in production against default/placeholder secrets.
- **⚡ Frontend Optimization**: React 18 SPA with route-level code splitting (`React.lazy` + `Suspense`) and chunk splitting ensuring every chunk is under 500 kB.

---

## 🏗️ System Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │               React + TypeScript Frontend              │
                    │       (Vite, TailwindCSS, Leaflet Interactive Maps)    │
                    │         • Route-Level Lazy Loading & Code Splitting    │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                HTTP REST /api/v1│   WebSocket /ws/tracking
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │                    FastAPI Gateway                     │
                    │   (Async ASGI, CORS, Security Headers, Rate Limiter)   │
                    └───────┬───────────────────┬───────────────────┬────────┘
                            │                   │                   │
                            ▼                   ▼                   ▼
                 ┌──────────────────┐┌──────────────────┐┌──────────────────┐
                 │  Optimization    ││  ML & AI Engines ││ Core Operations  │
                 │  Google OR-Tools ││  • ETA Predictor ││ • Auth & RBAC    │
                 │  • VRPTW Solver  ││  • Demand Forecast││ • Orders & Fleet │
                 │  • Distance/Time ││  • Delay Risk    ││ • Route Execution│
                 │  • Capacity Check││  • Dispatch Match││ • Audit Logger   │
                 └──────────┬───────┘└──────────┬───────┘└──────────┬───────┘
                            │                   │                   │
                            └───────────────────┼───────────────────┘
                                                │
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │                   Data & Caching Tier                  │
                    │   PostgreSQL 16 (Async Relational DB, Alembic 001-008) │
                    │   Redis 7 (Live GPS Broker, Caching, Token Blacklist)  │
                    └────────────────────────────────────────────────────────┘
```

---

## 💻 Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, TypeScript (Strict), Vite 5, TailwindCSS, Lucide Icons, Leaflet Maps, Recharts |
| **Frontend Testing**| Vitest 2.1, React Testing Library, JSDOM, User Event |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2, Uvicorn |
| **Optimization** | Google OR-Tools (Vehicle Routing Problem with Time Windows & Capacities) |
| **Machine Learning** | Scikit-Learn (Gradient Boosting), NumPy, Pandas, Joblib |
| **Data & Cache** | PostgreSQL 16 (Relational Store), Redis 7 (Pub/Sub & Coordinate Broker) |
| **DevOps & CI/CD** | Docker, Docker Compose, GitHub Actions, Nginx, Ruff Linter |

---

## 📁 Project Structure

```
Smart Logistics & Route Optimization/
├── backend/                  # FastAPI Application Core
│   ├── alembic/              # Database Migrations (Versions 001 - 008)
│   ├── app/
│   │   ├── api/              # REST & WebSocket Endpoints (Auth, Orders, Routes, etc.)
│   │   ├── core/             # Configuration, Database Pool, Redis, Security, Seeder
│   │   ├── ml/               # AI ETA, Demand Forecasting & Delay Risk Models
│   │   ├── models/           # SQLAlchemy 2.0 Relational Models
│   │   ├── schemas/          # Pydantic v2 Validation Schemas
│   │   └── services/         # Business Logic, Optimization & Audit Services
│   └── requirements.txt      # Python Dependencies
├── frontend/                 # React 18 + TypeScript Frontend
│   ├── src/
│   │   ├── components/       # UI Elements, Maps, Navbar, Modal & ProtectedRoute
│   │   ├── context/          # Auth & State Context Providers
│   │   ├── pages/            # Role Dashboards, Fleet Routes, Map & AI Insights
│   │   ├── services/         # Axios API with 401 Refresh Interceptor & WebSockets
│   │   └── test/             # Vitest & React Testing Library Suites
│   ├── vite.config.ts        # Vite Bundler with Route Splitting & Chunking
│   └── package.json          # Node Dependencies & Scripts
├── optimization/             # Core Deterministic Optimization Engine
│   ├── vrp_solver.py         # Google OR-Tools VRP Solver
│   ├── route_optimizer.py    # Multi-Vehicle Dispatch Optimizer
│   └── distance_matrix.py    # Haversine Distance & Time Matrices
├── scripts/                  # Operational Utility Scripts
│   ├── seed_demo_data.py     # Idempotent Database Seeder CLI
│   └── train_models.py       # Scikit-Learn ETA & Demand Model Trainer CLI
├── docker/                   # Multi-Stage Production Dockerfiles
│   ├── Dockerfile.backend    # Python 3.11 Slim Backend
│   ├── Dockerfile.frontend   # Node 20 Build + Nginx 1.27 Alpine Frontend
│   └── nginx.conf            # Nginx Reverse Proxy Configuration
├── docs/                     # Comprehensive Architectural & Technical Documentation
├── tests/                    # 139 Automated Pytest Regression Tests
├── docker-compose.yml        # Production Multi-Container Orchestration
└── .env.example              # Environment Configuration Template
```

---

## 🧪 Testing & Verification

### Backend Automated Test Suite (Pytest)
The backend test suite executes 139 tests covering authentication, database persistence, RBAC isolation, Google OR-Tools constraints, WebSocket tracking, machine learning, and security protections:

```bash
# Run pytest with code coverage
pytest tests/ -v --cov=app --cov-report=term
```

```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
plugins: anyio-4.14.2, asyncio-1.4.0, cov-7.1.0
collected 139 items

tests\test_ai_delay.py ........                                          [  5%]
tests\test_ai_recommendations.py ....                                    [  7%]
tests\test_analytics.py .                                                [  8%]
tests\test_auth.py ...........                                           [ 16%]
tests\test_capacity.py .                                                 [ 17%]
tests\test_customers.py .....                                            [ 20%]
tests\test_dashboard.py .....                                            [ 24%]
tests\test_driver_location.py ...                                        [ 26%]
tests\test_drivers.py .......                                            [ 31%]
tests\test_eta.py ...                                                    [ 33%]
tests\test_forecast.py ......                                            [ 38%]
tests\test_geocoding.py .....                                            [ 41%]
tests\test_load.py .                                                     [ 42%]
tests\test_maintenance.py ........                                       [ 48%]
tests\test_notifications.py .......                                      [ 53%]
tests\test_optimization.py .....                                         [ 56%]
tests\test_orders.py .......                                             [ 61%]
tests\test_persistence.py ..                                             [ 63%]
tests\test_phase13_production.py ...............                          [ 74%]
tests\test_realtime.py ......                                            [ 78%]
tests\test_routes.py ......                                              [ 82%]
tests\test_tracking.py ..........                                        [ 87%]
tests\test_vehicles.py .......                                           [ 92%]
tests\test_warehouses.py ......                                          [ 97%]
tests\test_websockets.py ....                                            [100%]

============================= 139 passed in 136.50s =============================
```

### Frontend Test Suite (Vitest + React Testing Library)
The frontend test suite validates authentication forms, role-gated routes, dynamic search filtering, and the 401 token refresh interceptor:

```bash
cd frontend
npm test
```

```text
 RUN  v2.1.9 frontend

 ✓ src/test/tokenRefresh.test.ts (2 tests)
 ✓ src/test/protectedRoute.test.tsx (3 tests)
 ✓ src/test/orders.test.tsx (3 tests)
 ✓ src/test/auth.test.tsx (3 tests)

 Test Files  4 passed (4)
      Tests  11 passed (11)
```

### Frontend Typecheck & Build
```bash
cd frontend
npm run lint      # tsc --noEmit: 0 errors
npm run build     # vite build: 0 errors, all chunks < 500 kB
```

---

## 🛠️ CLI Operations & Scripts

### Database Seeding
To populate or refresh demo data (NYC warehouses, customers, drivers, vehicles, orders) in PostgreSQL:
```bash
python scripts/seed_demo_data.py
```

### Machine Learning Model Retraining
To re-train the ETA Gradient Boosting Regressor and Demand Forecasting models:
```bash
python scripts/train_models.py
```

---

## 📚 Technical Documentation & Submission Material

Detailed architectural, operational, and presentation documentation is available in the [`docs/`](./docs/) directory:
- 📄 **[Comprehensive Project Report](./docs/PROJECT_REPORT.md)**: Full academic & engineering report covering abstract, problem statement, OR-Tools VRPTW formulation, ML architectures, schema design, security, and real metrics.
- 🎬 **[10-Minute Demo Script & Screenshot Guide](./docs/DEMO_SCRIPT.md)**: Role-by-role live demonstration walkthrough and recommended screenshot catalog.
- 🎓 **[Viva Examination Q&A](./docs/VIVA_QA.md)**: 25 verified technical defense and viva questions with accurate answers based on the code.
- 🏗️ **[System Architecture](./docs/architecture.md)**: Layered architecture, asynchronous data flow, and database schema mappings.
- 🌐 **[REST & WebSocket API Reference](./docs/api.md)**: Detailed API contracts and real-time telemetry protocols.
- 🚀 **[Deployment & Operations Guide](./docs/deployment.md)**: Production containerization, environment secrets, and monitoring.
- 🧪 **[Testing & Quality Assurance](./docs/testing.md)**: Multi-layer test automation, fixtures, and coverage metrics.
- 🔒 **[Security & Hardening](./docs/security.md)**: JWT RBAC, PII redaction, and startup validation.

---

## 🛡️ License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
