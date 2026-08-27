import heapq
from typing import Dict, List, Tuple, Optional, Any


def dijkstra_shortest_path(
    graph: Dict[str, Dict[str, float]],
    start_node: str,
    end_node: Optional[str] = None,
) -> Dict[str, Any]:
    """Computes shortest paths from start_node to all reachable nodes (or target end_node)
    using Dijkstra's algorithm with a priority queue (min-heap).
    
    graph: dict where graph[u][v] = weight of edge u -> v
    start_node: origin node ID
    end_node: optional destination node ID to terminate early
    
    Returns:
    {
        "distances": {node: min_distance, ...},
        "predecessors": {node: prev_node, ...},
        "path": [start_node, ..., end_node] (if end_node specified and reachable),
        "total_cost": float
    }
    """
    if start_node not in graph:
        raise ValueError(f"Start node '{start_node}' not found in graph.")

    distances: Dict[str, float] = {node: float("inf") for node in graph}
    distances[start_node] = 0.0
    predecessors: Dict[str, Optional[str]] = {node: None for node in graph}

    # Priority queue storing (cost, node)
    pq: List[Tuple[float, str]] = [(0.0, start_node)]
    visited = set()

    while pq:
        current_cost, u = heapq.heappop(pq)

        if u in visited:
            continue
        visited.add(u)

        if end_node and u == end_node:
            break

        if current_cost > distances[u]:
            continue

        for v, weight in graph.get(u, {}).items():
            if weight < 0:
                raise ValueError("Dijkstra does not support negative edge weights.")
            
            new_cost = current_cost + weight
            if v not in distances:
                distances[v] = float("inf")
                predecessors[v] = None

            if new_cost < distances[v]:
                distances[v] = new_cost
                predecessors[v] = u
                heapq.heappush(pq, (new_cost, v))

    # Path reconstruction if end_node requested
    path = []
    total_cost = distances.get(end_node, float("inf")) if end_node else 0.0

    if end_node and distances.get(end_node, float("inf")) < float("inf"):
        curr = end_node
        while curr is not None:
            path.append(curr)
            curr = predecessors.get(curr)
        path.reverse()

    return {
        "distances": distances,
        "predecessors": predecessors,
        "path": path,
        "total_cost": total_cost,
    }


def dijkstra_from_matrix(
    matrix: List[List[float]],
    start_idx: int,
    end_idx: Optional[int] = None,
) -> Dict[str, Any]:
    """Helper to run Dijkstra on an adjacency matrix."""
    n = len(matrix)
    graph: Dict[str, Dict[str, float]] = {}
    for i in range(n):
        node_i = str(i)
        graph[node_i] = {}
        for j in range(n):
            if i != j and matrix[i][j] > 0 and matrix[i][j] < float("inf"):
                graph[node_i][str(j)] = float(matrix[i][j])

    res = dijkstra_shortest_path(
        graph=graph,
        start_node=str(start_idx),
        end_node=str(end_idx) if end_idx is not None else None,
    )
    # Convert string node IDs back to integer indices in path
    if res["path"]:
        res["path_indices"] = [int(x) for x in res["path"]]
    else:
        res["path_indices"] = []
    return res
