import json
import math
import os

from utils.a_star import run_a_star_fallback
from utils.dijkstra import reconstruct_path, run_dijkstra
from utils.tsp_optimizer import solve_pickup_order


DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "route_network.json",
)

DEFAULT_TRAFFIC_PROFILES = {
    "normal": 1.0,
    "moderate": 1.2,
    "heavy": 1.45,
    "gridlock": 1.8,
}
SEVERITY_WEIGHTS = {
    "low": 1.0,
    "medium": 1.5,
    "high": 2.4,
    "critical": 3.4,
}
MAX_PICKUPS = 3


def _load_network():
    with open(DATA_PATH, "r", encoding="utf-8") as file_obj:
        payload = json.load(file_obj)

    locations = {entry["id"]: entry for entry in payload["locations"]}
    graph = payload["graph"]
    traffic_profiles = payload.get("trafficProfiles", DEFAULT_TRAFFIC_PROFILES)
    max_pickups = payload.get("maxPickups", MAX_PICKUPS)
    traffic_hotspots = payload.get("trafficHotspots", {})
    return locations, graph, traffic_profiles, max_pickups, traffic_hotspots


LOCATION_NODES, ROAD_GRAPH, TRAFFIC_PROFILES, MAX_PICKUPS, TRAFFIC_HOTSPOTS = _load_network()


def haversine_km(start_coords, end_coords):
    lat1, lon1 = map(math.radians, start_coords)
    lat2, lon2 = map(math.radians, end_coords)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_location_catalog():
    return list(LOCATION_NODES.values())


def get_dispatch_config():
    return {
        "maxPickups": MAX_PICKUPS,
        "trafficProfiles": [
            {"id": profile_id, "label": profile_id.replace("_", " ").title()}
            for profile_id in TRAFFIC_PROFILES
        ],
        "severityOptions": [
            {"id": severity_id, "label": severity_id.title()}
            for severity_id in SEVERITY_WEIGHTS
        ],
    }


def _traffic_multiplier(traffic_profile, left, right):
    profile_factor = TRAFFIC_PROFILES.get(traffic_profile, TRAFFIC_PROFILES["normal"])
    hotspot_key = f"{left}:{right}"
    reverse_key = f"{right}:{left}"
    hotspot_factor = TRAFFIC_HOTSPOTS.get(hotspot_key, TRAFFIC_HOTSPOTS.get(reverse_key, 1.0))
    return profile_factor * hotspot_factor


def _build_weighted_graph(traffic_profile):
    weighted = {}
    for node_id, neighbors in ROAD_GRAPH.items():
        weighted[node_id] = {}
        for neighbor_id, base_weight in neighbors.items():
            weighted[node_id][neighbor_id] = round(
                base_weight * _traffic_multiplier(traffic_profile, node_id, neighbor_id),
                3,
            )
    return weighted


def _normalize_pickups(pickup_inputs, start_id, end_id):
    if not pickup_inputs:
        return []

    normalized = []
    seen = set()
    for pickup in pickup_inputs:
        if isinstance(pickup, str):
            pickup_id = pickup
            severity = "medium"
        else:
            pickup_id = pickup.get("id")
            severity = pickup.get("severity", "medium")

        if pickup_id in seen or pickup_id in {start_id, end_id}:
            continue
        if pickup_id not in LOCATION_NODES:
            raise ValueError("Unknown pickup point selected.")
        if severity not in SEVERITY_WEIGHTS:
            raise ValueError("Unknown pickup severity selected.")

        seen.add(pickup_id)
        normalized.append({"id": pickup_id, "severity": severity})

    if len(normalized) > MAX_PICKUPS:
        raise ValueError(f"Select at most {MAX_PICKUPS} pickup points for real-time dispatch.")

    return normalized


def _build_route_response(
    node_ids,
    algorithm,
    traffic_profile,
    fallback_reason=None,
    rescue_edges=None,
    visit_order=None,
    segment_algorithms=None,
    traffic_factor=None,
    travelMinutes=None,
):
    stops = [LOCATION_NODES[node_id] for node_id in node_ids]
    total_distance_km = 0.0
    for left, right in zip(node_ids, node_ids[1:]):
        total_distance_km += haversine_km(
            LOCATION_NODES[left]["coords"],
            LOCATION_NODES[right]["coords"],
        )

    traffic_factor = traffic_factor or TRAFFIC_PROFILES.get(traffic_profile, 1.0)
    travel_minutes = travelMinutes if travelMinutes is not None else max(3, round(total_distance_km * 2.8 * traffic_factor))

    return {
        "algorithm": algorithm,
        "fallbackReason": fallback_reason,
        "distanceKm": round(total_distance_km, 2),
        "etaMinutes": int(max(1, round(travel_minutes))),
        "nodeCount": len(stops),
        "stops": stops,
        "rescueEdges": rescue_edges or [],
        "visitOrder": visit_order or [],
        "segmentAlgorithms": segment_algorithms or [],
        "trafficProfile": traffic_profile,
        "trafficFactor": round(traffic_factor, 2),
        "maxPickups": MAX_PICKUPS,
        "pickupCount": max(0, len(visit_order or []) - 2),
    }


def _run_direct_leg(start_id, end_id, traffic_profile):
    weighted_graph = _build_weighted_graph(traffic_profile)
    dijkstra_path, dijkstra_minutes = run_dijkstra(start_id, end_id, weighted_graph)
    if dijkstra_path:
        return {
            "path": dijkstra_path,
            "travelMinutes": dijkstra_minutes,
            "algorithm": "Dijkstra",
            "fallbackReason": None,
            "rescueEdges": [],
        }

    a_star_route = run_a_star_fallback(
        start_id,
        end_id,
        weighted_graph,
        traffic_profile,
        LOCATION_NODES,
        haversine_km,
        TRAFFIC_PROFILES,
        reconstruct_path,
    )
    if a_star_route:
        return a_star_route

    raise ValueError("No recoverable route is available for the selected locations.")


def _dedupe_preserve_order(node_ids):
    ordered = []
    for node_id in node_ids:
        if not ordered or ordered[-1] != node_id:
            ordered.append(node_id)
    return ordered


def _merge_leg_paths(legs):
    merged = []
    for leg in legs:
        if not merged:
            merged.extend(leg["path"])
        else:
            merged.extend(leg["path"][1:])
    return _dedupe_preserve_order(merged)


def _build_multi_stop_route(start_id, pickup_details, end_id, traffic_profile):
    optimized_order = solve_pickup_order(
        start_id,
        pickup_details,
        end_id,
        traffic_profile,
        _run_direct_leg,
        SEVERITY_WEIGHTS,
    )
    route_points = [start_id, *[entry["id"] for entry in optimized_order], end_id]
    legs = [_run_direct_leg(left, right, traffic_profile) for left, right in zip(route_points, route_points[1:])]
    merged_path = _merge_leg_paths(legs)

    segment_algorithms = [leg["algorithm"] for leg in legs]
    fallback_reasons = [leg["fallbackReason"] for leg in legs if leg["fallbackReason"]]
    rescue_edges = []
    total_minutes = 0.0
    for leg in legs:
        rescue_edges.extend(leg["rescueEdges"])
        total_minutes += leg["travelMinutes"]

    visit_order = [
        {"id": start_id, "name": LOCATION_NODES[start_id]["name"], "role": "Origin", "severity": None},
        *[
            {
                "id": pickup["id"],
                "name": LOCATION_NODES[pickup["id"]]["name"],
                "role": f"Pickup {index + 1}",
                "severity": pickup["severity"],
            }
            for index, pickup in enumerate(optimized_order)
        ],
        {"id": end_id, "name": LOCATION_NODES[end_id]["name"], "role": "Destination", "severity": None},
    ]

    fallback_reason = None
    if fallback_reasons:
        fallback_reason = "TSP optimized the pickup order, and one or more route legs required A* recovery."

    algorithm = "TSP + Dijkstra"
    if any(segment != "Dijkstra" for segment in segment_algorithms):
        algorithm = "TSP + Dijkstra/A*"

    return _build_route_response(
        merged_path,
        algorithm=algorithm,
        traffic_profile=traffic_profile,
        fallback_reason=fallback_reason,
        rescue_edges=rescue_edges,
        visit_order=visit_order,
        segment_algorithms=segment_algorithms,
        traffic_factor=TRAFFIC_PROFILES.get(traffic_profile, 1.0),
        travelMinutes=total_minutes,
    )


def plan_location_route(start_id, end_id, pickup_inputs=None, traffic_profile="normal"):
    if start_id not in LOCATION_NODES or end_id not in LOCATION_NODES:
        raise ValueError("Unknown location selected.")
    if traffic_profile not in TRAFFIC_PROFILES:
        raise ValueError("Unknown traffic profile selected.")

    pickup_details = _normalize_pickups(pickup_inputs or [], start_id, end_id)

    if start_id == end_id and not pickup_details:
        return {
            "algorithm": "Dijkstra",
            "fallbackReason": "Origin and destination are the same location.",
            "distanceKm": 0.0,
            "etaMinutes": 0,
            "nodeCount": 1,
            "stops": [LOCATION_NODES[start_id]],
            "rescueEdges": [],
            "visitOrder": [
                {"id": start_id, "name": LOCATION_NODES[start_id]["name"], "role": "Origin / Destination", "severity": None}
            ],
            "segmentAlgorithms": [],
            "trafficProfile": traffic_profile,
            "trafficFactor": TRAFFIC_PROFILES[traffic_profile],
            "maxPickups": MAX_PICKUPS,
            "pickupCount": 0,
        }

    if pickup_details:
        return _build_multi_stop_route(start_id, pickup_details, end_id, traffic_profile)

    direct_leg = _run_direct_leg(start_id, end_id, traffic_profile)
    return _build_route_response(
        direct_leg["path"],
        algorithm=direct_leg["algorithm"],
        traffic_profile=traffic_profile,
        fallback_reason=direct_leg["fallbackReason"],
        rescue_edges=direct_leg["rescueEdges"],
        visit_order=[
            {"id": start_id, "name": LOCATION_NODES[start_id]["name"], "role": "Origin", "severity": None},
            {"id": end_id, "name": LOCATION_NODES[end_id]["name"], "role": "Destination", "severity": None},
        ],
        segment_algorithms=[direct_leg["algorithm"]],
        traffic_factor=TRAFFIC_PROFILES.get(traffic_profile, 1.0),
        travelMinutes=direct_leg["travelMinutes"],
    )
