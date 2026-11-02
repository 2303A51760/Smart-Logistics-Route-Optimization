# Smart Logistics & Route Optimization Platform — 10-Minute Demo Script

This script provides an exact, step-by-step presentation script designed for a 10-minute live demonstration or viva evaluation. It guides the presenter through the perspective of three distinct stakeholders: **Logistics Manager**, **Fleet Driver**, and **System Administrator**.

---

## Demo Overview & Credentials

| Role | Email | Password | Primary Interface |
|---|---|---|---|
| **Logistics Manager** | `manager@example.com` | `Manager@123456` | Operations Dashboard, Optimization Console, Fleet Map |
| **Fleet Driver** | `driver@example.com` | `Driver@123456` | Driver Mobile Cockpit, Route Execution, Live GPS Telemetry |
| **System Administrator** | `admin@example.com` | `Admin@123456` | Platform Governance, Health Probes, Immutable Audit Logs |

**Base Application URL**: `http://localhost:3000` (Docker Nginx) or `http://localhost:5173` (Vite dev server)  
**API Swagger Documentation**: `http://localhost:8000/docs`

---

## Step 1: Logistics Manager Journey (Minutes 0:00 – 4:30)

### 1.1 Login & Operations Overview
- **Action**: Open `http://localhost:3000/login`. Enter `manager@example.com` / `Manager@123456`. Click **Sign In**.
- **Page Displayed**: `/operations` (Manager Operations Dashboard).
- **What to Say**:
  > *"We begin our journey as the Logistics Manager. The dashboard gives us immediate operational visibility into active orders, available drivers, vehicle capacity utilization, and system alerts. Notice that all statistics are loaded directly from our PostgreSQL 16 database via asynchronous SQLAlchemy queries—no mock data stores or in-memory stubs are used."*

### 1.2 Inspecting Orders & Priority Scoring
- **Action**: Click **Orders** in the navigation bar (`/orders`). Point out the priority badges (`URGENT`, `HIGH`, `MEDIUM`, `LOW`). Filter by status `PENDING`.
- **What to Say**:
  > *"In the Orders module, we can inspect all incoming delivery requests across our NYC hubs. Notice the priority classifications: each order is evaluated by our explainable AI priority engine, which scores consignments based on package weight, delivery deadline urgency, and distance to destination."*

### 1.3 Running Google OR-Tools Route Optimization
- **Action**: Click **Optimization** in the navigation bar (`/optimization`). Select the **Midtown Logistics Hub** depot, select active pending orders, and click **Run Optimization**.
- **What to Say**:
  > *"Here is the core operations research engine. Instead of relying on naive greedy heuristics, our platform solves the Capacitated Vehicle Routing Problem with Time Windows (VRPTW) using Google OR-Tools. The solver enforces vehicle payload capacities, delivery time windows, and shift constraints. In just a few seconds, it returns an optimal multi-vehicle routing schedule minimizing total fleet distance."*

### 1.4 Visualizing the Live Fleet Map
- **Action**: Click **Fleet Map** in the navigation bar (`/map`). Inspect the Leaflet map showing depot markers, customer delivery pins, and the polyline route geometries.
- **What to Say**:
  > *"On the interactive Leaflet fleet map, dispatchers can view real-time depot locations, delivery stop sequences, and route paths. Leaflet renders these coordinates dynamically, and as drivers progress along their route, their live GPS coordinates stream directly onto this view."*

### 1.5 Predictive Analytics & Demand Forecast
- **Action**: Click **Demand** (`/demand`). Point to the 1-day, 7-day, 14-day, and 30-day forecast curves and capacity gap indicators.
- **What to Say**:
  > *"Our machine learning subsystem predicts future daily package volumes using an autoregressive gradient-boosting model. It automatically compares predicted demand against available fleet capacity, warning dispatchers in advance if extra drivers or vehicles need to be scheduled."*

---

## Step 2: Driver Mobile Journey (Minutes 4:30 – 7:30)

### 2.1 Driver Authentication & Role Gating
- **Action**: Click user profile in top-right, click **Logout**. Enter `driver@example.com` / `Driver@123456`. Click **Sign In**.
- **Page Displayed**: `/driver/dashboard` (Driver Cockpit).
- **What to Say**:
  > *"Now we switch to the perspective of John Doe, one of our fleet drivers. Notice the strict Role-Based Access Control: John cannot access managerial tabs like Optimization or Audit Logs—attempting to navigate there redirects him with an unauthorized warning. He is taken directly to his driver dashboard."*

### 2.2 Active Route Execution
- **Action**: Click **My Routes** (`/driver/routes`). Open the assigned active route (`/driver/routes/:id`).
- **What to Say**:
  > *"Here John sees his sequenced delivery stops. Each stop details the customer name, delivery address, time window, and package weight. Notice the status transitions: John can mark a stop as `IN_TRANSIT` when departing and `COMPLETED` upon delivery."*

### 2.3 Live WebSocket Telemetry Streaming
- **Action**: Point out the active GPS streaming indicator in the driver cockpit. (If running the demo test script or simulator, show live coordinates updating).
- **What to Say**:
  > *"As the driver travels, the mobile client streams live GPS coordinates over a persistent WebSocket connection to `/ws/tracking`. The backend uses Redis to buffer location coordinates with sub-millisecond latency, broadcasting real-time updates to dispatcher dashboards."*

---

## Step 3: Administrator & Security Governance (Minutes 7:30 – 10:00)

### 3.1 Admin Authentication & System Health
- **Action**: Logout and sign in as `admin@example.com` / `Admin@123456`. Navigate to `/health` or open `http://localhost:8000/health`.
- **What to Say**:
  > *"Finally, we log in as the System Administrator. The admin possesses full platform governance privileges. First, looking at our health probe endpoint, we see the live health status of our containerized PostgreSQL 16 connection pool, Redis 7 caching cluster, and active WebSocket connection count."*

### 3.2 Tamper-Evident Security Audit Logs
- **Action**: Click **Audit Logs** (`/audit-logs`). Show the recent audit trail entries.
- **What to Say**:
  > *"A critical enterprise requirement is accountability and compliance. The platform maintains an append-only, tamper-evident audit log in PostgreSQL. Every single authentication attempt, order creation, route optimization, and status change is recorded with timestamps, user identity, IP address, and metadata. Notice our automatic PII redaction engine: sensitive credentials, tokens, and private contact data are scrubbed before persistence."*

### 3.3 Fail-Safe Production Hardening
- **Action**: Show `backend/app/core/config.py` in the IDE or report.
- **What to Say**:
  > *"Security is enforced at the configuration layer. When deployed with `ENVIRONMENT=production`, the application refuses to start if any secret key, JWT secret, or database password is left at default or placeholder values. Combined with rate limiting and strict TypeScript compilation, the platform is robust against operational failures."*

---

## Manual Screenshot Guide for Viva Submission

To capture screenshots of the running platform for project reports and submission slides, open the application in your browser and capture the following pages:

| # | Page / Feature | URL Route | Recommended Size | What to Highlight |
|---|---|---|---|---|
| **1** | **Authentication Screen** | `http://localhost:3000/login` | 1440 × 900 | Clean branded login form, demo credentials helper text, validation feedback. |
| **2** | **Manager Operations Dashboard** | `http://localhost:3000/operations` | 1440 × 900 | High-level KPI cards (Total Orders, Available Drivers, Fleet Capacity, Active Alerts), recent order table. |
| **3** | **Order Management Console** | `http://localhost:3000/orders` | 1440 × 900 | Filtered orders list, priority tags (`URGENT`, `HIGH`), customer names, package weight column. |
| **4** | **Google OR-Tools Optimization** | `http://localhost:3000/optimization` | 1440 × 900 | Depot selection dropdown, consignment checkboxes, optimization results summary (total km, routes, solved status). |
| **5** | **Interactive Leaflet Fleet Map** | `http://localhost:3000/map` | 1440 × 900 | NYC map view showing warehouse depot markers, delivery stop pins, and colored route polylines. |
| **6** | **ML Demand Forecast Analytics** | `http://localhost:3000/demand` | 1440 × 900 | Recharts demand forecast curves (1d, 7d, 14d, 30d), confidence intervals, fleet capacity gap alert badge. |
| **7** | **Driver Mobile Cockpit** | `http://localhost:3000/driver/dashboard` | 390 × 844 (Mobile) | Assigned route banner, stop sequence cards, waypoint status toggle buttons, GPS active indicator. |
| **8** | **Security Audit Logs** | `http://localhost:3000/audit-logs` | 1440 × 900 | Audit trail table showing actions (`USER_LOGIN`, `ORDER_CREATE`, `ROUTE_OPTIMIZE`), user email, timestamp, PII-redacted details. |
| **9** | **Swagger Interactive API Docs** | `http://localhost:8000/docs` | 1440 × 900 | OpenAPI 3.0 specification showing authenticated endpoints, Pydantic schemas, and interactive test buttons. |

