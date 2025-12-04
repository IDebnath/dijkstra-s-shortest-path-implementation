from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import heapq
import time


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLACE_FILE = PROJECT_ROOT / "data" / "raw" / "Place.txt"
DEFAULT_ROAD_FILE = PROJECT_ROOT / "data" / "raw" / "Road.txt"

AdjacencyList = Dict[int, List[Tuple[int, float, str]]]


def load_places(place_file: Path) -> Tuple[Dict[str, int], Dict[int, str]]:
    """
    Read Place.txt and build lookup dictionaries.

    Returns:
        name_to_id: maps exact place names to their numeric IDs.
        id_to_name: maps place IDs back to their names (used for printing paths).
    """
    if not place_file.exists():
        raise FileNotFoundError(f"Place file not found: {place_file}")

    name_to_id: Dict[str, int] = {}
    id_to_name: Dict[int, str] = {}

    with place_file.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue  # Skip blank lines.

            parts = stripped.split(",", maxsplit=1)
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid format in {place_file} on line {line_number}: {raw_line!r}"
                )

            place_id_str, place_name = parts
            place_id_str = place_id_str.strip()
            place_name = place_name.strip()

            if not place_id_str:
                raise ValueError(
                    f"Missing place ID in {place_file} on line {line_number}: {raw_line!r}"
                )

            try:
                place_id = int(place_id_str)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid place ID '{place_id_str}' on line {line_number}"
                ) from exc

            if not place_name:
                # Names can be missing in Place.txt, but the file format guarantees
                # two columns, so treat empty names as "null" placeholders.
                place_name = "null"

            # A place ID should be unique; if duplicates appear, we keep the first.
            if place_id not in id_to_name:
                id_to_name[place_id] = place_name

            # Place names may repeat (for example, multiple entries for similar names).
            # We only record the first occurrence to keep lookups deterministic.
            name_to_id.setdefault(place_name, place_id)

    return name_to_id, id_to_name


def load_graph(road_file: Path) -> AdjacencyList:
    """
    Read Road.txt and construct an undirected adjacency list.

    Each edge is stored twice (both directions) so the caller can traverse
    neighbors efficiently without extra conditionals.
    """
    if not road_file.exists():
        raise FileNotFoundError(f"Road file not found: {road_file}")

    graph: AdjacencyList = {}

    with road_file.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue

            parts = stripped.split(",", maxsplit=3)
            if len(parts) != 4:
                raise ValueError(
                    f"Invalid format in {road_file} on line {line_number}: {raw_line!r}"
                )

            left_id_str, right_id_str, miles_str, description = (
                part.strip() for part in parts
            )

            try:
                left_id = int(left_id_str)
                right_id = int(right_id_str)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid place ID on line {line_number}: {raw_line!r}"
                ) from exc

            try:
                miles = float(miles_str)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid distance '{miles_str}' on line {line_number}"
                ) from exc

            if miles < 0:
                raise ValueError(
                    f"Negative distance detected on line {line_number}: {raw_line!r}"
                )

            # Store both directions because the dataset represents undirected roads.
            graph.setdefault(left_id, []).append((right_id, miles, description))
            graph.setdefault(right_id, []).append((left_id, miles, description))

    return graph


def get_place_id(name_to_id: Dict[str, int], prompt_text: str) -> int:
    """
    Prompt the user for a place name and resolve it to a place ID.

    The lookup is an exact string match, as required by the assignment.
    """
    user_input = input(prompt_text).strip()
    if not user_input:
        raise ValueError("Empty place name provided.")

    try:
        return name_to_id[user_input]
    except KeyError as exc:
        raise KeyError(
            f"Place name {user_input!r} was not found. "
            "Make sure you type it exactly as it appears in Place.txt."
        ) from exc


def dijkstra(graph: AdjacencyList, source: int, target: int) -> Tuple[Dict[int, float], Dict[int, int]]:
    """
    Run Dijkstra's algorithm from source toward target.

    Returns:
        dist: best-known distances from source to each visited node.
        prev: back-pointers for path reconstruction.
    """
    dist: Dict[int, float] = {source: 0.0}
    prev: Dict[int, int] = {}

    # (distance_so_far, node_id)
    heap: List[Tuple[float, int]] = [(0.0, source)]

    while heap:
        current_dist, u = heapq.heappop(heap)

        # Skip outdated heap entries.
        if current_dist > dist.get(u, float("inf")):
            continue

        if u == target:
            break

        for v, weight, _description in graph.get(u, []):
            new_dist = current_dist + weight
            if new_dist < dist.get(v, float("inf")):
                dist[v] = new_dist
                prev[v] = u
                heapq.heappush(heap, (new_dist, v))

    return dist, prev


def reconstruct_path(prev: Dict[int, int], source: int, target: int) -> Optional[List[int]]:
    """
    Rebuild the path from source to target using the prev map.

    Returns a list of node IDs from source to target, or None if no path exists.
    """
    if source == target:
        return [source]

    # If the target was never reached during Dijkstra, there is no path.
    if target not in prev:
        return None

    path: List[int] = [target]
    current = target

    # Walk backwards from target to source using the prev map.
    while current != source:
        current = prev.get(current)
        if current is None:
            # We lost the chain back to the source; treat as no path.
            return None
        path.append(current)

    path.reverse()
    return path


def find_edge(
    graph: AdjacencyList, from_id: int, to_id: int
) -> Optional[Tuple[float, str]]:
    """
    Look up the edge from from_id to to_id in the adjacency list.

    Returns:
        (distance, description) if the edge exists, otherwise None.
    """
    for neighbor_id, miles, description in graph.get(from_id, []):
        if neighbor_id == to_id:
            return miles, description
    return None


def main() -> None:
    """Manual test harness for Phases 2–6."""
    try:
        name_to_id, id_to_name = load_places(DEFAULT_PLACE_FILE)
    except (FileNotFoundError, ValueError) as error:
        print(f"Failed to load places: {error}")
        return

    print(f"Loaded {len(id_to_name)} place IDs with names.")
    print(f"Unique place names stored: {len(name_to_id)}")

    sample_items = list(name_to_id.items())[:5]
    if sample_items:
        print("Sample entries:")
        for name, pid in sample_items:
            print(f"  {name} -> {pid}")

    try:
        graph = load_graph(DEFAULT_ROAD_FILE)
    except (FileNotFoundError, ValueError) as error:
        print(f"Failed to load roads: {error}")
        return

    node_count = len(graph)
    directed_edge_count = sum(len(neighbors) for neighbors in graph.values())
    undirected_edges = directed_edge_count // 2

    print(f"Graph contains {node_count} nodes with at least one incident road.")
    print(f"Stored {directed_edge_count} directed edges (~{undirected_edges} undirected segments).")

    # Display one sample node to verify the adjacency structure without flooding the console.
    try:
        sample_node, neighbors = next(iter(graph.items()))
        print(f"Sample node {sample_node} has {len(neighbors)} neighbors.")
    except StopIteration:
        print("Graph appears to be empty.")
        return

    print()
    print("You can now test name-to-ID resolution.")
    try:
        source_id = get_place_id(name_to_id, "Enter the Source Name: ")
        dest_id = get_place_id(name_to_id, "Enter the Destination Name: ")
    except (ValueError, KeyError) as error:
        print(f"Could not resolve place name: {error}")
        return

    source_name = id_to_name.get(source_id, "null")
    dest_name = id_to_name.get(dest_id, "null")

    print(f"Searching from {source_id}({source_name}) to {dest_id}({dest_name})")

    start_time = time.time()

    # Run Dijkstra to find the shortest path.
    dist, prev = dijkstra(graph, source_id, dest_id)
    best_distance = dist.get(dest_id, float("inf"))

    if best_distance == float("inf"):
        print(
            "No route found between the given places. "
            "They may be in different disconnected components (e.g., mainland vs. Alaska/Hawaii)."
        )
        return

    path = reconstruct_path(prev, source_id, dest_id)
    if not path:
        print(
            "Dijkstra reported a finite distance but no path could be reconstructed. "
            "This should not normally happen."
        )
        return

    total_distance = 0.0
    for index in range(len(path) - 1):
        from_id = path[index]
        to_id = path[index + 1]

        edge_info = find_edge(graph, from_id, to_id)
        if edge_info is None:
            print(
                f"Warning: no edge data found from {from_id} to {to_id} "
                "even though the path reconstruction included it."
            )
            continue

        miles, description = edge_info
        total_distance += miles

        from_name = id_to_name.get(from_id, "null")
        to_name = id_to_name.get(to_id, "null")
        step_number = index + 1

        print(
            f"\t{step_number}: {from_id}({from_name}) -> "
            f"{to_id}({to_name}), {description}, {miles:.2f} mi."
        )

    end_time = time.time()

    print(
        f"It takes {total_distance:.2f} miles from "
        f"{source_id}({source_name}) to {dest_id}({dest_name})."
    )
    print(f"Computation time (Dijkstra + path reconstruction/printing): {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    main()

