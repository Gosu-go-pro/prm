# Visibility Roadmap (C-space) — Step-by-step (8 images + 1 GIF)

This package contains the **rendered figures** (PNG) and an animated **GIF** that illustrate how to construct a **visibility roadmap** (milestone-based), **not** a visibility graph (obstacle-vertex graph), for a simple 2D configuration space.

- C-space: **2D translation only** (q = (x, y))
- Obstacles: 3 axis-aligned rectangles (treated as **C_obs** regions)
- Roadmap nodes: **milestones** (start, goal, + random samples in C_free)
- Roadmap edges: straight segments between milestones that are **collision-free** (line-of-sight visibility)
- Planning: **Dijkstra** on the roadmap graph

---

## Files

### Images (PNG)

1. `step01_environment.png`  
   **Step 1 — Define the C-space environment**: show C_obs (blue rectangles) and C_free (white). Start **S** and Goal **G** are placed in C_free.

2. `step02_init_graph.png`  
   **Step 2 — Initialise graph**: V = {q_start, q_goal}, E = ∅. Start and goal are marked as **mandatory milestones**.

3. `step03_sample_milestones.png`  
   **Step 3 — Sample milestones**: 18 random milestones in C_free (reject samples in obstacles). Now |V| = 20, still E = ∅.

4. `step04a_blocked_edge.png`  
   **Step 4a — Visibility test (BLOCKED)**: test the direct segment S→G. The segment intersects an obstacle, so the edge is **rejected**.

5. `step04b_accepted_edge.png`  
   **Step 4b — Visibility test (ACCEPTED)**: show a sample pair (q_i, q_j) whose segment does **not** intersect any obstacle. The edge is **added**.

6. `step05_full_roadmap.png`  
   **Step 5 — Build full roadmap** with **all-pairs visibility**: all C(20,2) = 190 pairs are tested. Accepted edges: **|E| = 79**.

7. `step06_shortest_path.png`  
   **Step 6 — Graph search (Dijkstra)**: shortest path on the roadmap is highlighted (orange). Path length ≈ **12.13**, through **4 waypoints** (numbered).

8. `step07_final_summary.png`  
   **Final summary**: roadmap + highlighted path + stats box (|V|, |E|, path length, path nodes).

### Animation (GIF)

- `visibility_roadmap_steps.gif`  
  Plays the 8 steps in order (slower frame duration for readability) and pauses briefly on the final result.

---

## Key concept reminders (why this is a *visibility roadmap*, not a *visibility graph*)

- **Visibility graph**: nodes are obstacle vertices (plus start/goal); optimal shortest paths in polygonal domains can be extracted.
- **Visibility roadmap** (this demo): nodes are **sampled configurations** (“milestones”) and edges connect **visible** milestone pairs.
  - It is scalable and simple.
  - It is **not guaranteed optimal** unless sampling/connectivity are strong enough.

In practice, this sits close to PRM-style planning, except here we demonstrate the “visibility” logic explicitly.

---

## Notes on collision checking used in the demo

An edge (q_i, q_j) is accepted if:
- both endpoints are in C_free, and
- the segment does **not** intersect any obstacle boundary, and
- sampled points along the segment are not inside obstacles (midpoint / discretized checks).

This is a clean didactic check for axis-aligned rectangles; for production use you would want robust geometric predicates.

---

## Optional: Re-run the generator script

A helper script is included:

- `visibility_roadmap_steps.py`

It re-generates all images + the GIF into a local `./outputs/` folder.

### Requirements
- Python 3.9+
- `numpy`, `matplotlib`, `pillow`

Install (example):
```bash
pip install numpy matplotlib pillow
```

Run:
```bash
python visibility_roadmap_steps.py
```

---

Generated: 2026-02-22
