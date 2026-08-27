# Smart Logistics & Route Optimization Platform 🚚⚡

A modern, high-performance platform for fleet tracking, capacitated vehicle routing (VRP), demand forecasting, real-time telemetry, and role-based access control.

---

## 🏗️ Architecture Overview

The system is structured as a clean, production-ready monorepo:

```
smart-logistics/
├── frontend/             # React + Vite + TypeScript + Tailwind CSS + Leaflet
├── backend/              # Python + FastAPI + SQLAlchemy + Alembic + Redis + WebSockets + JWT/RBAC
├── optimization/         # Google OR-Tools routing engine & distance matrix algorithms
├── ml/                   # Machine learning travel time (ETA) & demand forecasting
├── tests/                # Pytest async integration & API verification suite
├── docker/               # Dockerfiles for frontend (Nginx) and backend (FastAPI)
├── docker-compose.yml     # Complete local stack (Postgres, Redis, API, UI)
├── .env.example          # Environment variable template
└── README.md             # Documentation & getting started guide
```

---

## 🔐 Phase 1: Authentication & Role-Based Access Control (RBAC)

The platform supports secure JWT authentication with bcrypt password hashing and 3 discrete user roles:

### 🎭 Role Hierarchy & Permissions

| Role | Access Level | Available Views & Capabilities |
| :--- | :--- | :--- |
| **`ADMIN`** | Full System Access | User management, RBAC directory, infrastructure logs, route management, optimization |
| **`LOGISTICS_MANAGER`** | Operations & Dispatch | Fleet tracking, Leaflet map, delivery queue, OR-Tools VRP optimization solver |
| **`DRIVER`** | Field Operations | Assigned route manifest, live telemetry broadcasting, delivery stop check-in |

### 🔑 Demo Role Accounts

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@example.com` | `Admin@123456` |
| **Logistics Manager** | `manager@example.com` | `Manager@123456` |
| **Driver** | `driver@example.com` | `Driver@123456` |

---

## 🚀 Tech Stack

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Leaflet (OpenStreetMap), React Router v6, Lucide Icons
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, PyJWT, Bcrypt
- **Database & ORM**: PostgreSQL 16, SQLAlchemy 2.0 (AsyncIO), Alembic
- **Caching & Brokers**: Redis 7, aioredis
- **Real-Time Streaming**: Native WebSockets (`/ws/tracking`)
- **Optimization**: Google OR-Tools (Capacitated Vehicle Routing Problem - CVRP)
- **Machine Learning**: Scikit-Learn (ETA & demand prediction)
- **DevOps & Containers**: Docker, Multi-Stage Builds, Docker Compose

---

## ⚡ Getting Started

### 1. Prerequisites
- **Node.js** v18+ and **npm**
- **Python** 3.11+
- **Docker & Docker Compose** (Optional for containerized run)

### 2. Running with Docker Compose (Recommended)
```bash
# Copy environment configuration
cp .env.example .env

# Build and start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up --build
```
- **Frontend App**: `http://localhost:3000` (or `http://localhost:5173` locally)
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/api/v1/docs`

---

### 3. Running Locally (Without Docker)

#### Backend Setup:
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate  # Linux / macOS

# Install dependencies
pip install -r backend/requirements.txt

# Run migrations (when PostgreSQL is active)
alembic -c backend/alembic.ini upgrade head

# Start FastAPI server
uvicorn app.main:app --app-dir backend --reload --port 8000
```

#### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Running Automated Tests

Run the test suite with `pytest`:
```bash
pytest tests/
```

---

## 📡 Authentication & API Endpoints

| Endpoint | Method | Role | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/auth/register` | `POST` | Public | Register new user account |
| `/api/v1/auth/login` | `POST` | Public | Authenticate user & receive JWT access + refresh tokens |
| `/api/v1/auth/refresh` | `POST` | Public | Refresh expired access token |
| `/api/v1/auth/me` | `GET` | Authenticated | Retrieve authenticated user profile |
| `/api/v1/auth/logout` | `POST` | Authenticated | Logout active session |
| `/api/v1/auth/admin-only` | `GET` | `ADMIN` | Test admin-restricted route |
| `/api/v1/auth/manager-only` | `GET` | `ADMIN`, `LOGISTICS_MANAGER` | Test manager-restricted route |
| `/api/v1/auth/driver-only` | `GET` | All roles | Test driver-restricted route |
| `/api/v1/health` | `GET` | Public | System health check (DB, Redis, WebSockets) |
| `/api/v1/vehicles` | `GET`, `POST` | Authenticated | List and register fleet vehicles |
| `/api/v1/routes` | `GET` | Authenticated | Retrieve planned and dispatched routes |
| `/api/v1/optimization/solve` | `POST` | Authenticated | Execute Google OR-Tools VRP optimization |
| `/ws/tracking` | `WebSocket` | Public/Auth | Real-time vehicle telemetry streaming |

---

## 🛡️ License
MIT License. Built for Smart Logistics & Route Optimization operations.
