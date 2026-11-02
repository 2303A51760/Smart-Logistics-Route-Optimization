import pytest
from httpx import AsyncClient
from optimization.distance_matrix import (
    haversine_distance_km,
    compute_distance_matrix_meters,
    compute_time_matrix_seconds,
)
from optimization.dijkstra import dijkstra_shortest_path
from optimization.astar import astar_search
from optimization.vrp_solver import VRPSolver


async def get_auth_token(client: AsyncClient, email: str, role_password: str = "Admin@123456") -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": role_password},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


# --- Algorithm Unit Tests ---

def test_haversine_distance_accuracy():
    ny = (40.7128, -74.0060)
    philly = (39.9526, -75.1652)
    dist = haversine_distance_km(ny[0], ny[1], philly[0], philly[1])
    assert 120.0 < dist < 140.0
    assert haversine_distance_km(ny[0], ny[1], ny[0], ny[1]) == 0.0


def test_distance_and_time_matrix_computation():
    coords = [
        (40.7128, -74.0060),  # Depot
        (40.7209, -74.0005),  # Stop 1
        (40.7505, -73.9735),  # Stop 2
    ]
    dist_matrix = compute_distance_matrix_meters(coords)
    assert len(dist_matrix) == 3
    assert len(dist_matrix[0]) == 3
    assert dist_matrix[0][0] == 0
    assert dist_matrix[0][1] > 0
    assert dist_matrix[1][0] == dist_matrix[0][1]

    time_matrix = compute_time_matrix_seconds(coords, speed_kmh=40.0, service_time_seconds=300)
    assert len(time_matrix) == 3
    assert time_matrix[0][1] >= 300


def test_dijkstra_shortest_path():
    graph = {
        "A": {"B": 4.0, "C": 2.0},
        "B": {"A": 4.0, "C": 1.0, "D": 5.0},
        "C": {"A": 2.0, "B": 1.0, "D": 8.0, "E": 10.0},
        "D": {"B": 5.0, "C": 8.0, "E": 2.0},
        "E": {"C": 10.0, "D": 2.0},
    }
    result = dijkstra_shortest_path(graph, start_node="A", end_node="D")
    assert result["path"] == ["A", "C", "B", "D"]
    assert result["total_cost"] == 8.0

    result_e = dijkstra_shortest_path(graph, start_node="A", end_node="E")
    assert result_e["path"] == ["A", "C", "B", "D", "E"]
    assert result_e["total_cost"] == 10.0


def test_astar_search_with_haversine_heuristic():
    coordinates = {
        "A": (40.7128, -74.0060),
        "B": (40.7200, -74.0000),
        "C": (40.7300, -73.9900),
        "D": (40.7500, -73.9800),
    }
    graph = {
        "A": {"B": 1.0, "C": 5.0},
        "B": {"A": 1.0, "C": 1.5, "D": 6.0},
        "C": {"B": 1.5, "D": 2.0},
        "D": {"C": 2.0},
    }
    result = astar_search(graph, coordinates, start_node="A", goal_node="D")
    assert result["path"] == ["A", "B", "C", "D"]
    assert result["total_cost"] == 4.5
    assert result["nodes_expanded"] > 0


def test_vrp_capacity_constraint_enforcement():
    """Ensure vehicle capacity constraint is strictly respected."""
    solver = VRPSolver()
    depot = {"id": "depot-1", "name": "Warehouse", "lat": 40.7128, "lng": -74.0060}

    orders = [
        {"id": "ord-1", "name": "Order 1", "lat": 40.7209, "lng": -74.0005, "weight_kg": 30.0, "priority": "NORMAL"},
        {"id": "ord-2", "name": "Order 2", "lat": 40.7300, "lng": -73.9900, "weight_kg": 20.0, "priority": "NORMAL"},
        {"id": "ord-3", "name": "Order 3", "lat": 40.7420, "lng": -74.0048, "weight_kg": 40.0, "priority": "HIGH"},
        {"id": "ord-4", "name": "Order 4", "lat": 40.7505, "lng": -73.9735, "weight_kg": 25.0, "priority": "NORMAL"},
    ]

    vehicles = [
        {"id": "veh-1", "name": "Van 1", "capacity_kg": 60.0},
        {"id": "veh-2", "name": "Van 2", "capacity_kg": 60.0},
    ]

    result = solver.solve_vrp(depot=depot, orders=orders, vehicles=vehicles)

    assert result["status"] == "COMPLETED"
    assert result["orders_assigned"] == 4
    assert len(result["routes"]) <= 2

    for route in result["routes"]:
        assert route["total_load_kg"] <= 60.0


def test_vrp_overcapacity_and_impossible_optimization():
    """When orders exceed total fleet capacity, the solver must drop excess nodes gracefully."""
    solver = VRPSolver()
    depot = {"id": "depot-1", "name": "Warehouse", "lat": 40.7128, "lng": -74.0060}

    orders = [
        {"id": "ord-urgent", "name": "Urgent Meds", "lat": 40.7209, "lng": -74.0005, "weight_kg": 50.0, "priority": "URGENT"},
        {"id": "ord-heavy-1", "name": "Heavy 1", "lat": 40.7300, "lng": -73.9900, "weight_kg": 100.0, "priority": "NORMAL"},
        {"id": "ord-heavy-2", "name": "Heavy 2", "lat": 40.7420, "lng": -74.0048, "weight_kg": 150.0, "priority": "LOW"},
    ]

    vehicles = [
        {"id": "veh-small", "name": "Small Scooter", "capacity_kg": 120.0},
    ]

    result = solver.solve_vrp(depot=depot, orders=orders, vehicles=vehicles)

    assert result["status"] == "COMPLETED"
    assert result["orders_unassigned"] > 0

    assigned_order_ids = []
    for r in result["routes"]:
        for s in r["stops"]:
            if s["order_id"]:
                assigned_order_ids.append(s["order_id"])

    assert "ord-urgent" in assigned_order_ids
    assert len(result["unassigned_orders"]) > 0


def test_vrp_empty_order_list():
    solver = VRPSolver()
    depot = {"id": "depot-1", "name": "Warehouse", "lat": 40.7128, "lng": -74.0060}
    result = solver.solve_vrp(depot=depot, orders=[], vehicles=[])
    assert result["status"] == "COMPLETED"
    assert result["total_distance_km"] == 0.0
    assert result["orders_assigned"] == 0
    assert result["routes"] == []


# --- API Integration Tests ---

@pytest.mark.asyncio
async def test_api_optimize_endpoint(async_client: AsyncClient):
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch existing warehouses and orders from seed/DB
    wh_res = await async_client.get("/api/v1/warehouses", headers=headers)
    assert wh_res.status_code == 200
    warehouses_data = wh_res.json()
    warehouses = warehouses_data if isinstance(warehouses_data, list) else warehouses_data.get("items", [])
    assert len(warehouses) >= 1
    wh_id = warehouses[0]["id"]

    ord_res = await async_client.get("/api/v1/orders", headers=headers)
    assert ord_res.status_code == 200
    orders_data = ord_res.json()
    orders = orders_data if isinstance(orders_data, list) else orders_data.get("items", [])
    assert len(orders) >= 1
    order_ids = [o["id"] for o in orders[:3]]

    payload = {
        "warehouse_id": wh_id,
        "order_ids": order_ids,
        "max_route_distance_km": 150.0,
    }

    res = await async_client.post("/api/v1/optimization/optimize", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "COMPLETED"
    assert data["orders_assigned"] > 0
    assert data["total_distance_km"] >= 0
    assert len(data["routes"]) >= 1

    job_id = data["job_id"]

    # Retrieve job
    job_res = await async_client.get(f"/api/v1/optimization/jobs/{job_id}", headers=headers)
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["id"] == job_id
    assert job_data["status"] == "COMPLETED"
