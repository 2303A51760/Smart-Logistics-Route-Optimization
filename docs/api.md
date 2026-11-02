# API Reference & Documentation

Interactive Swagger UI is available at `/docs` and OpenAPI JSON specification is available at `/openapi.json`.

---

## 1. Authentication & User Management (`/api/v1/auth/*`)

| Method | Endpoint | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Public | Registers a new user account with hashed password (`bcrypt`). |
| `POST` | `/api/v1/auth/login` | Public | Authenticates credentials; issues JWT access and refresh tokens. |
| `POST` | `/api/v1/auth/refresh` | Public | Exchanges a valid refresh token for a new access token. |
| `GET` | `/api/v1/auth/me` | Authenticated | Retrieves profile of currently authenticated user. |
| `POST` | `/api/v1/auth/logout` | Authenticated | Revokes current session and token. |
| `GET` | `/api/v1/auth/admin-only` | `ADMIN` | Test endpoint validating Admin RBAC access. |
| `GET` | `/api/v1/auth/manager-only` | `ADMIN`, `LOGISTICS_MANAGER` | Test endpoint validating Manager RBAC access. |
| `GET` | `/api/v1/auth/driver-only` | All Roles | Test endpoint validating Driver RBAC access. |

---

## 2. Core Logistics Entities

### Warehouses (`/api/v1/warehouses/*`)
| Method | Endpoint | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/warehouses` | Authenticated | List all active logistics distribution hubs and depots. |
| `POST` | `/api/v1/warehouses` | Manager / Admin | Create a new warehouse distribution facility. |
| `GET` | `/api/v1/warehouses/{id}` | Authenticated | Retrieve details and capacity of a specific warehouse. |

### Orders (`/api/v1/orders/*`)
| Method | Endpoint | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/orders` | Authenticated | List orders with optional status, priority, and warehouse filtering. |
| `POST` | `/api/v1/orders` | Manager / Admin | Register a new consignment delivery order. |
| `GET` | `/api/v1/orders/{id}` | Authenticated | Retrieve complete consignment details and delivery status. |
| `PATCH` | `/api/v1/orders/{id}/status` | Authenticated | Transition order status (`PENDING`, `DISPATCHED`, `DELIVERED`, `FAILED`). |

### Vehicles & Maintenance (`/api/v1/vehicles/*`)
| Method | Endpoint | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/vehicles` | Authenticated | List fleet vehicles with type, fuel status, and capacity. |
| `POST` | `/api/v1/vehicles` | Manager / Admin | Register a new fleet vehicle. |
| `GET` | `/api/v1/vehicles/maintenance` | Manager / Admin | List maintenance logs and upcoming service schedules. |
| `POST` | `/api/v1/vehicles/{id}/maintenance` | Manager / Admin | Record vehicle maintenance or repair service. |

### Drivers (`/api/v1/drivers/*`)
| Method | Endpoint | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/drivers` | Authenticated | List all drivers with duty status and vehicle assignments. |
| `POST` | `/api/v1/drivers` | Manager / Admin | Register a new driver profile. |
| `GET` | `/api/v1/drivers/{id}` | Authenticated | Retrieve detailed driver profile and route history. |
| `PATCH` | `/api/v1/drivers/{id}/status` | Driver / Admin | Update driver duty status (`AVAILABLE`, `ON_ROUTE`, `OFF_DUTY`). |
| `GET` | `/api/v1/drivers/{id}/locations` | Authenticated | Retrieve driver GPS historical track path. |

---

## 3. Optimization & Route Execution (`/api/v1/routes/*` & `/api/v1/optimization/*`)

| Method | Endpoint | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/optimization/solve` | Manager / Admin | Execute Google OR-Tools VRP route optimization solver. |
| `GET` | `/api/v1/routes` | Authenticated | List planned and active fleet delivery routes. |
| `GET` | `/api/v1/routes/{id}` | Authenticated | Retrieve full ordered route stops and sequence details. |
| `POST` | `/api/v1/routes/{id}/start` | Driver / Manager | Start route execution (`PENDING` $\rightarrow$ `IN_PROGRESS`). |
| `POST` | `/api/v1/routes/{id}/complete` | Driver / Manager | Complete route execution and update manifests. |
| `PATCH` | `/api/v1/routes/stops/{stop_id}/status` | Driver / Manager | Update stop status (`PENDING`, `ARRIVED`, `COMPLETED`, `FAILED`). |

---

## 4. Artificial Intelligence & Analytics (`/api/v1/ai/*`, `/analytics/*`)

| Method | Endpoint | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/ai/order-priority/{order_id}` | Authenticated | Explainable AI priority score (0–100) and factor breakdown. |
| `GET` | `/api/v1/ai/order-priority` | Manager / Admin | List prioritized orders with classification tiers. |
| `GET` | `/api/v1/ai/dispatch/recommendations` | Manager / Admin | AI driver-vehicle matching with reasoning. |
| `POST` | `/api/v1/ai/delay-risk` | Authenticated | Predict delivery delay probability and risk levels. |
| `GET` | `/api/v1/ai/demand-forecast` | Manager / Admin | Multi-horizon demand forecast (1, 7, 14, 30 days). |
| `POST` | `/api/v1/ai/routes/{id}/reoptimize` | Manager / Admin | Evaluate route re-optimization and fuel/cost savings. |
| `GET` | `/api/v1/ai/operations-summary` | Manager / Admin | Executive KPI and fleet operational intelligence summary. |
| `POST` | `/api/v1/analytics/eta/predict` | Authenticated | Predict machine learning ETA using Gradient Boosting model. |

---

## 5. Security & Observability (`/api/v1/audit-logs/*`, `/health`, `/ready`, `/metrics`)

| Method | Endpoint | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/audit-logs` | `ADMIN` | Search and filter immutable security and operational audit logs. |
| `GET` | `/api/v1/audit-logs/stats` | `ADMIN` | Aggregate audit metrics and security event summaries. |
| `GET` | `/health` | Public | System liveness probe checking DB, Redis, and WebSockets. |
| `GET` | `/ready` | Public | System readiness probe for container orchestrators. |
| `GET` | `/metrics` | Public | Operational telemetry metrics and uptime counters. |

---

## 6. Real-Time Telemetry (`/ws/tracking`)

- **Protocol**: WebSocket (`ws://` / `wss://`)
- **Payload Format**: JSON
```json
{
  "driver_id": "drv-001",
  "latitude": 40.7538,
  "longitude": -74.0017,
  "speed": 34.5,
  "heading": 180.0,
  "timestamp": "2026-08-30T12:00:00Z"
}
```
