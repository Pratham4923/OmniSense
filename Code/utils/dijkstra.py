import heapq


def reconstruct_path(previous, start_id, end_id):
    if end_id not in previous and start_id != end_id:
        return None

    path = [end_id]
    while path[-1] != start_id:
        path.append(previous[path[-1]])
    path.reverse()
    return path


def run_dijkstra(start_id, end_id, graph):
    queue = [(0.0, start_id)]
    distances = {start_id: 0.0}
    previous = {}
    visited = set()

    while queue:
        current_distance, node_id = heapq.heappop(queue)
        if node_id in visited:
            continue
        visited.add(node_id)

        if node_id == end_id:
            break

        for neighbor_id, weight in graph.get(node_id, {}).items():
            next_distance = current_distance + weight
            if next_distance < distances.get(neighbor_id, float("inf")):
                distances[neighbor_id] = next_distance
                previous[neighbor_id] = node_id
                heapq.heappush(queue, (next_distance, neighbor_id))

    if end_id not in distances:
        return None, None

    return reconstruct_path(previous, start_id, end_id), distances[end_id]
