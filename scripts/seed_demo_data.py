#!/usr/bin/env python3
"""
Seed Script for Smart Logistics & Route Optimization Platform.
Idempotently populates the database with demo users, warehouses, customers,
drivers, vehicles, orders, routes, maintenance records, and notifications.
"""
import sys
import asyncio
from pathlib import Path

# Ensure backend directory is in path
backend_path = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_path))

from app.core.seed import main

if __name__ == "__main__":
    asyncio.run(main())

