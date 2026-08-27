import heapq
from typing import Dict, List, Tuple, Optional, Any, Callable
from optimization.distance_matrix import haversine_distance_km


def astar_search(
    graph: Dict[str, Dict[str, float]],
    coordinates: Dict[str, Tuple[float, float]],
    start_node: str,
    goal_node: str,
    heuristic_func: Optional[Callable[[Tuple[float, float], Tuple[float, float]], float]] = None,
) -> Dict[str, Any]:
    """A* search algorithm for finding the optimal path between start_node and goal_node
    guided by a heuristic function (defaults to Haversine great-circle distance).
    
    graph: adjacency list graph[u][v] = edge cost
    coordinates: coordinates[node] = (latitude, longitude)
    start_node: origin node
    goal_node: destination node
    heuristic_func: custom heuristic h(coord_a, coord_b) -> float
    
    Returns:
    {
        "path": [start_node, ..., goal_node],
        "total_cost": float,
        "nodes_expanded": int,
        "g_scores": {node: cost_from_start, ...}
    }
    """
    if start_node not in graph:
        raise ValueError(f"Start node '{start_node}' not found in graph.")
    if goal_node not in graph:
        raise ValueError(f"Goal node '{goal_node}' not found in graph.")
    if start_node not in coordinates or goal_node not in coordinates:
        raise ValueError("Nodes must have coordinates defined for A* heuristic calculation.")

    if heuristic_func is None:
        def default_heuristic(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
            return haversine_distance_km(p1[0], p1[1], p2[0], p2[1])
        heuristic_func = default_heuristic

    goal_coord = coordinates[goal_node]

    # Open set priority queue storing (f_score, current_node)
    open_set: List[Tuple[float, str]] = []
    initial_h = heuristic_func(coordinates[start_node], goal_coord)
    heapq.heappush(open_set, (initial_h, start_node))

    came_from: Dict[str, Optional[str]] = {start_node: None}
    g_score: Dict[str, float] = {node: float("inf") for node in graph}
    g_score[start_node] = 0.0

    f_score: Dict[str, float] = {node: float("inf") for node in graph}
    f_score[start_node] = initial_h

    closed_set = set()
    nodes_expanded = 0

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal_node:
            # Reconstruct path
            path = []
            curr = goal_node
            while curr is not None:
                path.append(curr)
                curr = came_from.get(curr)
            path.reverse()

            return {
                "path": path,
                "total_cost": g_score[goal_node],
                "nodes_expanded": nodes_expanded,
                "g_scores": g_score,
            }

        if current in closed_set:
            continue
        closed_set.add(current)
        nodes_expanded += 1

        for neighbor, weight in graph.get(current, {}).items():
            if weight < 0:
                raise ValueError("A* does not support negative edge weights.")

            tentative_g = g_score[current] + weight

            if neighbor not in g_score:
                g_score[neighbor] = float("inf")
                f_score[neighbor] = float("inf")

            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                h = heuristic_func(coordinates.get(neighbor, (0.0, 0.0)), goal_coord)
                f_score[neighbor] = tentative_g + h
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    # Path not found
    return {
        "path": [],
        "total_cost": float("inf"),
        "nodes_expanded": nodes_expanded,
        "g_scores": g_score,
    }
