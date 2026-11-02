# Deployment & Operations Guide

## 1. Prerequisites

- **Docker**: Engine 24.0+ and Docker Compose v2.20+
- **Node.js**: v18+ (Node 20 LTS recommended)
- **Python**: v3.11+ (Python 3.11 or 3.13 recommended)
- **PostgreSQL**: v16+ (or run via Docker)
- **Redis**: v7+ (or run via Docker)

---

## 2. Local Bare-Metal Setup

### Backend Setup:
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate virtual environment
python -m venv .venv

# Windows:
.\.venv\Scripts\Activate.ps1

# Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Run database migrations (Alembic versions 001 - 008)
python -m alembic upgrade head

# 5. Seed demo data (idempotent, safe to run multiple times)
python scripts/seed_demo_data.py

# 6. Start Uvicorn ASGI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup:
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
# Running on http://localhost:5173
```

---

## 3. Containerized Deployment (Docker & Docker Compose)

The repository provides production-ready multi-stage Dockerfiles and Docker Compose configuration.

### Multi-Container Stack:
- **`postgres`**: PostgreSQL 16 Alpine with persistent volume `pgdata`.
- **`redis`**: Redis 7 Alpine with persistent volume `redisdata`.
- **`backend`**: Python 3.11 Slim with connection pooling and multi-worker Uvicorn.
- **`frontend`**: Nginx 1.27 Alpine serving optimized React production bundle and proxying `/api` & `/ws`.

### Single Command Launch:
```bash
# Build all images
docker compose build

# Start services in background
docker compose up -d

# Apply database migrations inside the backend container
docker compose exec backend alembic upgrade head

# Seed initial NYC demo hubs, customers, drivers, vehicles, and orders
docker compose exec backend python scripts/seed_demo_data.py

# Verify container health status
docker compose ps
```

### Checking Logs:
```bash
# Stream backend logs
docker compose logs -f backend

# Stream frontend logs
docker compose logs -f frontend
```

### Shutting Down:
```bash
docker compose down
```

---

## 4. Production Hardening Checklist

- [x] Set secure, cryptographically random `SECRET_KEY` and `JWT_SECRET_KEY` in environment.
- [x] Disable `DEBUG` mode in production (`DEBUG=False`).
- [x] Configure explicit `BACKEND_CORS_ORIGINS` with production domains.
- [x] Enable connection pooling recycling (`POSTGRES_POOL_RECYCLE=1800`).
- [x] Enforce sliding-window rate limiters on authentication and heavy AI/optimization endpoints.
- [x] Containerize backend as non-root user where appropriate.
- [x] Mount health and readiness probes (`/health`, `/ready`) to load balancer target groups.
