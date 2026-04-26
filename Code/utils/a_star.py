import heapq


def build_rescue_graph(
    start_id,
    end_id,
    graph,
    traffic_profile,
    location_nodes,
    haversine_km,
    traffic_profiles,
    nearest_links=2,
    penalty_factor=1.2,
):
    rescue_graph = {node_id: dict(neighbors) for node_id, neighbors in graph.items()}
    rescue_edges = []

    for anchor_id in {start_id, end_id}:
        if rescue_graph.get(anchor_id):
            continue

        distances = []
        for candidate_id in location_nodes:
            if candidate_id == anchor_id:
                continue
            distance_km = haversine_km(
                location_nodes[anchor_id]["coords"],
                location_nodes[candidate_id]["coords"],
            )
            distances.append((distance_km, candidate_id))

        for distance_km, candidate_id in sorted(distances)[:nearest_links]:
            weighted_distance = round(
                distance_km * penalty_factor * traffic_profiles.get(traffic_profile, 1.0),
                3,
            )
            rescue_graph.setdefault(anchor_id, {})[candidate_id] = weighted_distance
            rescue_graph.setdefault(candidate_id, {})[anchor_id] = weighted_distance
            rescue_edges.append(
                {
                    "from": anchor_id,
                    "to": candidate_id,
                    "distanceKm": round(distance_km, 2),
                }
            )

    return rescue_graph, rescue_edges


def run_a_star_fallback(
    start_id,
    end_id,
    graph,
    traffic_profile,
    location_nodes,
    haversine_km,
    traffic_profiles,
    reconstruct_path,
):
    def heuristic(node_id, goal_id):
        return haversine_km(
            location_nodes[node_id]["coords"],
            location_nodes[goal_id]["coords"],
        )

    rescue_graph, rescue_edges = build_rescue_graph(
        start_id,
        end_id,
        graph,
        traffic_profile,
        location_nodes,
        haversine_km,
        traffic_profiles,
    )
    queue = [(0.0, start_id)]
    previous = {}
    g_score = {start_id: 0.0}
    visited = set()

    while queue:
        _, node_id = heapq.heappop(queue)
        if node_id in visited:
            continue
        visited.add(node_id)

        if node_id == end_id:
            path = reconstruct_path(previous, start_id, end_id)
            if path:
                return {
                    "path": path,
                    "travelMinutes": g_score[end_id],
                    "algorithm": "A* recovery",
                    "fallbackReason": (
                        "Dijkstra could not find a fully connected road path, so the planner "
                        "used heuristic recovery edges for point-to-point routing."
                    ),
                    "rescueEdges": rescue_edges,
                }
            break

        for neighbor_id, weight in rescue_graph.get(node_id, {}).items():
            tentative_g = g_score[node_id] + weight
            if tentative_g >= g_score.get(neighbor_id, float("inf")):
                continue

            previous[neighbor_id] = node_id
            g_score[neighbor_id] = tentative_g
            f_score = tentative_g + heuristic(neighbor_id, end_id)
            heapq.heappush(queue, (f_score, neighbor_id))

    return None
