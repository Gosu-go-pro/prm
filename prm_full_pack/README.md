# PRM Variants — Full Visualization and Explanation (13 Images)

This pack contains all PRM variants and explanations, including the key Lazy PRM behavior where edges intentionally cross obstacles.

---

# Why Lines Cross Obstacles (Important Concept)

Lazy PRM intentionally builds edges WITHOUT collision checking first.

Later, only edges on candidate shortest paths are checked.

This reduces collision checks dramatically.

---

# Image 01 — PRM Classic Step 1: Uniform Sampling

![Image 01](images/01_prm_classic_step1_samples.png)

Uniform random samples in free space.

No knowledge of obstacles beyond collision rejection.

Weakness: narrow passages may be under-sampled.

---

# Image 02 — PRM Classic Step 2: k‑NN Connections

![Image 02](images/02_prm_classic_step2_connections.png)

Each node connects to its k nearest neighbors.

Collision checking removes edges that intersect obstacles.

Sparse connectivity appears in narrow regions.

---

# Image 03 — PRM Classic Step 3: Shortest Path

![Image 03](images/03_prm_classic_step3_path.png)

Dijkstra finds shortest collision‑free path.

Quality depends on sampling density.

---

# Image 04 — Gaussian PRM

![Image 04](images/04_gaussian_prm_step1_samples.png)

Samples concentrate near obstacle boundaries.

Improves connectivity near narrow passages.

---

# Image 05 — Bridge PRM

![Image 05](images/05_bridge_prm_step1_samples.png)

Samples concentrated directly inside narrow passages.

Strongest variant for narrow corridor environments.

---

# Image 06 — Uniform Zoom

![Image 06](images/06_zoom_uniform.png)

Uniform sampling often misses narrow passages.

---

# Image 07 — Gaussian Zoom

![Image 07](images/07_zoom_gaussian.png)

More samples near obstacle edges.

Better than uniform.

---

# Image 08 — Bridge Zoom

![Image 08](images/08_zoom_bridge.png)

High concentration inside narrow passage.

Best performance for tight corridors.

---

# Image 09 — Lazy PRM Step 1 (Unchecked Edges)

![Image 09](images/09_lazy_prm_step1_unchecked_edges.png)

Edges cross obstacles intentionally.

Collision checking skipped to speed construction.

Core Lazy PRM concept.

---

# Image 10 — Lazy PRM Step 2 (Validate Only Path Edges)

![Image 10](images/10_lazy_prm_step2_checked_edges_and_path.png)

Only edges along candidate path are checked.

Rejected edges are removed.

Final path is fully valid.

Major efficiency gain.

---

# Image 11 — PRM* Large Graph

![Image 11](images/11_prm_star_large_n.png)

Uses radius‑based connection rule.

Guarantees asymptotic optimality.

---

# Image 12 — PRM* Smaller Graph

![Image 12](images/11_prm_star_small_n.png)

Fewer nodes produce less optimal path.

Improves as sample count increases.

---

# Image 13 — Visibility PRM

![Image 13](images/13_visibility_prm_concept.png)

Uses guards and connectors.

Produces very small roadmap.

Memory efficient.

---

# Summary

Variant | Benefit
---|---
Classic PRM | Simple baseline
Gaussian PRM | Better boundary coverage
Bridge PRM | Excellent narrow passage handling
Lazy PRM | Massive speed improvement
PRM* | Asymptotic optimality
Visibility PRM | Minimal roadmap size

---

All images verified correct and collision logic confirmed.