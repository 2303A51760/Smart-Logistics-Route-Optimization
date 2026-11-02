# Phase 14 — AI-Powered Intelligent Dispatch, Demand Forecasting & Dynamic Route Optimization

## 1. Overview & Architecture

Phase 14 enhances the **Smart Logistics & Route Optimization Platform** by establishing an **explainable, non-destructive AI Decision-Support Layer** operating in concert with the existing Google OR-Tools VRP optimization solver, Scikit-Learn ML models, and real-time execution pipelines.

```
                    ┌────────────────────────────────────────────────────────┐
                    │          AI Intelligence & Decision Support            │
                    │   (/ai-insights, /api/v1/ai/*, Explainable Models)     │
                    └───────────────────────────┬────────────────────────────┘
                                                │
         ┌───────────────────┬──────────────────┼───────────────────┬───────────────────┐
         ▼                   ▼                  ▼                   ▼                   ▼
┌──────────────────┐┌──────────────────┐┌──────────────────┐┌──────────────────┐┌──────────────────┐
│  Order Priority  ││  Delay Risk      ││  AI Dispatch     ││  Dynamic Route   ││  Demand Forecast │
│  Scoring Engine  ││  Predictor       ││  Matching Engine ││  Re-Optimizer    ││  Ensemble        │
│  (0-100 Tiers)   ││  (GBM + Baseline)││  (Proximity/Load)││  (Time/Fuel/Cost)││  (1/7/14/30 Days)│
└──────────────────┘└──────────────────┘└──────────────────┘└──────────────────┘└──────────────────┘
                                                │
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │               Deterministic Optimizer Core             │
                    │         (RouteOptimizer, VRPSolver / Google OR-Tools)  │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │             Route Execution & Live Tracking            │
                    │         (/routes/*, /ws/tracking, Audit Logging)       │
                    └────────────────────────────────────────────────────────┘
```

---

## 2. Core AI Capabilities & Mathematical Formulations

### A. Intelligent Order Priority Engine (`backend/app/services/order_priority.py`)
- **Normalized Score Range**: 0.0 to 100.0.
- **Classification Tiers**:
  - `85–100`: **CRITICAL** (Immediate dispatch to highest-capacity available driver).
  - `70–84`: **HIGH** (Priority dispatch queue).
  - `40–69`: **MEDIUM** (Standard daily VRP solver batch).
  - `0–39`: **LOW** (Consolidated low-density manifest).
- **Factors Combined**:
  $$\text{Priority Score} = \text{Base Priority (40)} + \text{Deadline Urgency (30)} + \text{Distance (15)} + \text{Weight Load (10)} + \text{Backlog Status (5)}$$
- **Explainability**: Outputs granular component breakdowns and human-readable reasoning notes for dispatchers.

### B. Delivery Delay Prediction (`backend/app/ml/delay_prediction.py`)
- Predicts `delay_probability` (0.0 to 1.0) and `risk_level` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- Predicts estimated delay minutes based on traffic index ($1.0\times - 2.5\times$), waypoint stop density, weather severity factors, transit corridor distance, and deadline window remaining.
- Powered by Scikit-Learn Gradient Boosting Classifier with automatic analytical baseline fallback.

### C. AI-Assisted Dispatch Matching (`backend/app/services/dispatch_ai.py`)
- Generates ranked driver-vehicle candidate pairings for orders.
- Evaluates:
  - Driver availability status (Available, Active, On-route, Off-duty).
  - Vehicle cargo capacity fit (hard constraint excluding overloaded vehicles).
  - Depot and customer proximity via Haversine distance calculations.
  - **Maintenance Safety Constraint**: Vehicles with active maintenance schedules (`SCHEDULED`, `IN_PROGRESS`, `MAINTENANCE`) are strictly excluded from dispatch recommendations.

### D. Cost & Fuel-Aware Route Optimization (`backend/app/services/cost_optimizer.py`)
- Computes vehicle class fuel burn adjustments (Truck: 22.0 L/100km, Van: 12.5 L/100km, Bike: 4.0 L/100km).
- Evaluates cargo load factor penalty ($0\%$ to $+20\%$ fuel under full payload).
- Calculates estimated fuel cost ($= \text{liters} \times \text{fuel\_cost\_per\_liter}$) and total operational transit cost.

### E. Dynamic Route Re-Optimization (`backend/app/services/dynamic_routing.py`)
- Evaluates candidate route improvements against current active manifests using Google OR-Tools VRP Solver.
- Determines whether re-routing is beneficial ($\ge 5$ minutes or $\ge 2.0$ km saved).
- Provides distance, duration, fuel, and cost savings delta.

### F. Multi-Horizon Demand Forecasting (`backend/app/ml/demand/`)
- Supports 1, 7, 14, and 30-day forecast horizons with uncertainty upper/lower bounds, peak period analysis, and warehouse zone filtering.

---

## 3. REST API Endpoints

| Method | Path | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/ai/order-priority/{order_id}` | Authenticated | Calculates priority score and factor breakdown for an order |
| `GET` | `/api/v1/ai/order-priority` | `ADMIN`, `LOGISTICS_MANAGER` | Lists and filters order priorities with classification tiers |
| `GET` | `/api/v1/ai/dispatch/recommendations` | `ADMIN`, `LOGISTICS_MANAGER` | Returns ranked driver-vehicle assignment pairings |
| `POST` | `/api/v1/ai/delay-risk` | Authenticated | Predicts delay probability from transit parameters |
| `GET` | `/api/v1/ai/delay-risk/order/{order_id}` | Authenticated | Evaluates delay risk for an existing platform order |
| `GET` | `/api/v1/ai/demand-forecast` | `ADMIN`, `LOGISTICS_MANAGER` | Retrieves multi-horizon order demand predictions |
| `POST` | `/api/v1/ai/routes/{route_id}/reoptimize` | `ADMIN`, `LOGISTICS_MANAGER` | Evaluates dynamic route re-optimization and logs audit event |
| `GET` | `/api/v1/ai/operations-summary` | `ADMIN`, `LOGISTICS_MANAGER` | Executive operations intelligence and fleet savings summary |

---

## 4. Frontend AI Insights Console (`/ai-insights`)

- **Interactive Metric Banners**: Real-time KPI cards tracking Critical Priority Orders, High Delay Risks, Fleet Time Savings, and Estimated Fuel Saved.
- **Explainable Dispatch Recommendations**: Displays ranked driver-vehicle pairings with "Why this pairing?" bullet points.
- **Dynamic Route Re-Optimization**: Compares original vs proposed route distance, duration, and fuel savings.
- **Priority Scoring Matrix**: Filterable table with interactive factor breakdown modal.
- **Demand Forecasting Horizons**: 1, 7, 14, and 30-day horizon selector with volume totals and peak day analysis.

---

## 5. Security, RBAC & Audit Logging

- **Role-Based Access Control (RBAC)**:
  - **ADMIN** & **LOGISTICS_MANAGER**: Unrestricted access to dispatch intelligence, demand forecasts, and fleet re-optimization.
  - **DRIVER**: Restricted from global management intelligence (`403 Forbidden` on `/ai/dispatch/recommendations` and `/ai/operations-summary`).
- **Audit Logging**: Every AI calculation and re-optimization action automatically logs structured events (`AI_PRIORITY_CALCULATED`, `AI_DISPATCH_RECOMMENDATION`, `AI_ROUTE_REOPTIMIZATION`, `AI_FORECAST_GENERATED`) to the `audit_logs` table via `AuditService`.
- **Rate Limiting**: Sliding-window rate limiters protecting AI endpoints from abuse.

---

## 6. Verification & Test Suite Results

### 1. Pytest Full Platform Regression: **137 / 137 Passed (100%)**
```bash
backend\.venv\Scripts\python -m pytest tests/
================= 137 passed, 2 warnings in 133.78s (0:02:13) =================
```

### 2. Frontend Production Build: **0 Errors**
```bash
cd frontend && npm run build
✓ 2395 modules transformed.
✓ built in 11.21s
```

### 3. Alembic Database Migration
```bash
cd backend && ..\.venv\Scripts\python.exe -m alembic heads
007_create_ai_recommendations_table (head)
```

---

## 7. Model Versioning & Transparency

| Model Capability | Model Identifier | Version | Underlying Technique |
| :--- | :--- | :--- | :--- |
| **Order Priority Scoring** | `order_priority_heuristic_v1` | `1.0.0` | Multi-factor weighted heuristic engine |
| **Delivery Delay Risk** | `gradient_boosting_delay_risk` | `1.0.0` | Scikit-Learn Gradient Boosting Classifier |
| **Dispatch Assignment Matching** | `dispatch_matcher_v1` | `1.0.0` | Proximity & capacity heuristic ranker |
| **Dynamic Route Re-Optimization** | `dynamic_reoptimizer_v1` | `1.0.0` | Google OR-Tools VRP Solver + Fuel Model |
| **Route Cost & Fuel Estimator** | `cost_fuel_estimator_v1` | `1.0.0` | Vehicle class load-adjusted consumption model |

---

## 8. Status

**PHASE 14 COMPLETE: AI-Powered Intelligent Dispatch, Demand Forecasting & Dynamic Route Optimization fully implemented and verified with 100% test pass rate.**
