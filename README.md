## Dijkstra's Shortest Path on the US Road Network

This project is a Python implementation of **Dijkstra's shortest path algorithm** on a large, real-world road network of the United States.  
Given two place names, the program finds the **shortest driving route by distance** and prints:

- **Every road segment** along the route (IDs, names, road description, miles)
- The **total distance** between the two places
- A simple **runtime measurement** for the computation

The implementation is focused on clean data handling, an efficient graph representation, and a textbook Dijkstra using a priority queue.

---

## Data

The graph is built from two plain-text files (from the course dataset):

- `data/raw/Place.txt`  
  - Maps **place IDs → names** (and vice versa).
  - Only some place IDs have names; others are reported as `null` in the output.

- `data/raw/Road.txt`  
  - Each line is a road segment: `place_id_1, place_id_2, distance_miles, description`.
  - All segments are **two-way**; the graph is therefore **undirected**.

Dataset scale:

- ~**91,203** nodes (place IDs with at least one incident road)
- ~**127,806** undirected road segments (~255,612 directed edges in the adjacency list)

---

## How It Works

- **Graph representation**:  
  - The road network is stored as an **adjacency list**:  
    `Dict[int, List[Tuple[int, float, str]]]`  
  - For each place ID, we keep a list of neighbors with `(neighbor_id, miles, description)`.

- **Place lookups**:  
  - `name_to_id`: exact string match for user input → place ID  
  - `id_to_name`: place ID → human-readable name (or `null` if missing)

- **Dijkstra's algorithm**:  
  - Implemented with Python’s `heapq` as a **min-priority queue**.
  - Tracks:
    - `dist[node]`: best-known distance from the source
    - `prev[node]`: previous node on the shortest path
  - Stops early when the destination is finalized or when no more nodes are reachable.

- **Path reconstruction**:  
  - Walks backward from destination to source using `prev`, then reverses the list to get the forward path.
  - For each consecutive pair of nodes, the program looks up the corresponding road segment to print description and distance.

- **Disconnected components**:  
  - If the destination is unreachable (e.g., mainland → Hawaii), the program reports that **no route exists** instead of looping or crashing.

---

## Usage

From the project root:

```bash
python -m src.main
```

The program will:

1. Load `Place.txt` and `Road.txt` and print basic statistics (number of places, nodes, edges).
2. Prompt for:
   - `Enter the Source Name:`
   - `Enter the Destination Name:`
3. Run Dijkstra’s algorithm on the road network.
4. Either:
   - Print that no route exists (if the graph components are disconnected), or
   - Print the full path and total distance.

Input place names must match exactly the names as they appear in `Place.txt`.

---

## Example Output (Structure)

The output follows this style:

- Header:

```text
Searching from 39087(MIKALAMAZOO N) to 39059(MIANN ARBOR N)
```

- Path steps:

```text
    1: 39087(MIKALAMAZOO N) -> 39123(null), U131 BARK ST, 1.11 mi.
    2: 39123(null) -> 39122(null), O94  BALAMAZOO AV, 0.38 mi.
    ...
```

- Summary:

```text
It takes 100.49 miles from 39087(MIKALAMAZOO N) to 39059(MIANN ARBOR N).
Computation time (Dijkstra + path reconstruction/printing): X.XX seconds.
```

---

## Implementation Details

- **Language**: Python 3
- **External dependencies**: None (only Python standard library)
- **Key modules**:
  - `heapq` for the priority queue
  - `pathlib` for robust file paths
  - `typing` for basic type hints

The theoretical time complexity of the Dijkstra step is:
\[
O((V + E)\log V)
\]
for \(V\) vertices (places) and \(E\) edges (road segments), which is suitable for this dataset size.

---

## Project Structure

- `src/main.py`  
  Main entry point: loads data, resolves names, runs Dijkstra, prints the route and statistics.

- `data/raw/Place.txt`  
  Place IDs and names, used for user input and human-readable output.

- `data/raw/Road.txt`  
  Road segment definitions (place IDs, distances, descriptions).

- `README_explained.md`  
  In-depth explanation of the assignment, algorithm, and design choices.

- `README_workflow.md`  
  Step-by-step development workflow with checklists for each phase.

- `requirements.txt`  
  Documents that only standard-library modules are required.


