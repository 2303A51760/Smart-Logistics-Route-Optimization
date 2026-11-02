from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    health,
    dashboard,
    map_view,
    drivers,
    vehicles,
    warehouses,
    customers,
    orders,
    routes,
    optimization,
    tracking,
    eta,
    forecast,
    maintenance,
    notifications,
    audit,
    ai,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(health.router, prefix="/health", tags=["System Health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Operations Analytics & Dashboards"])
api_router.include_router(map_view.router, prefix="/map", tags=["Interactive Logistics Maps"])
api_router.include_router(drivers.router, prefix="/drivers", tags=["Driver Management"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["Fleet & Vehicles"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["Warehouse Management"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customer Management"])
api_router.include_router(orders.router, prefix="/orders", tags=["Order Management"])
api_router.include_router(routes.router, prefix="/routes", tags=["Routes & Deliveries"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["Route Optimization"])
api_router.include_router(tracking.router, prefix="/tracking", tags=["Real-Time GPS Tracking & History"])
api_router.include_router(eta.router, prefix="/eta", tags=["AI-Based ETA Prediction & Analytics"])
api_router.include_router(forecast.router, prefix="/forecast", tags=["AI Demand Forecasting & Capacity Planning"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Vehicle Maintenance & Fleet Health"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Intelligent Logistics Alerts & Notifications"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["Security & Enterprise Audit Logs"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI-Powered Intelligent Dispatch & Decision Support"])
