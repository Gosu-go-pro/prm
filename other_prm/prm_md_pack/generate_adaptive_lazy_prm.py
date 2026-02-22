#!/usr/bin/env python3
"""Generate all 13 Adaptive PRM & Lazy PRM* demo images for README.md.

Implements:
  - Adaptive PRM: density-guided sampling that learns hard zones over iterations.
  - Lazy PRM*: PRM* radius connections built lazily, validate only path edges.

Output directory: images/ relative to this script.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.collections import LineCollection
from pathlib import Path
from scipy.ndimage import gaussian_filter
import heapq

# ── Reproducibility ───────────────────────────────────────────────
np.random.seed(42)

# ── Output directory ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
IMG_DIR = SCRIPT_DIR / "images"
IMG_DIR.mkdir(exist_ok=True)

# ── World ─────────────────────────────────────────────────────────
X_LIM = (0.0, 10.0)
Y_LIM = (0.0, 7.0)
START = np.array([0.8, 0.8])
GOAL = np.array([9.2, 6.2])

# Rectangles (x, y, w, h) — create narrow passages and corners
OBSTACLES = [
    (2.0, 0.0, 0.6, 3.8),   # vertical wall left-bottom
    (4.0, 3.2, 0.6, 3.8),   # vertical wall center-top
    (6.5, 0.0, 0.6, 4.5),   # vertical wall right-bottom
    (8.0, 5.0, 2.0, 0.6),   # horizontal bar upper-right
]

# ── Colours ───────────────────────────────────────────────────────
OBS_FACE = "#7B9DBF"
OBS_EDGE = "#34495E"
OBS_ALPHA = 0.70
SAMPLE_CLR = "#1f77b4"
EDGE_CLR = "#AAAAAA"
PATH_CLR = "#E91E63"
COLLISION_CLR = "#D32F2F"
START_CLR = "#2ECC40"
GOAL_CLR = "#FF851B"
CHECKED_OK_CLR = "#2196F3"
CHECKED_FAIL_CLR = "#D32F2F"

# ── Density grid resolution ──────────────────────────────────────
GRID_RES = 0.1
NX = int((X_LIM[1] - X_LIM[0]) / GRID_RES)
NY = int((Y_LIM[1] - Y_LIM[0]) / GRID_RES)


# =====================================================================
#  Utility functions
# =====================================================================

def point_in_obstacle(pt):
    """Return True if pt is inside any obstacle."""
    for (ox, oy, ow, oh) in OBSTACLES:
        if ox <= pt[0] <= ox + ow and oy <= pt[1] <= oy + oh:
            return True
    return False


def segment_collides(a, b, n_checks=20):
    """Return True if segment a-b crosses any obstacle."""
    for t in np.linspace(0, 1, n_checks):
        p = a + t * (b - a)
        if point_in_obstacle(p):
            return True
    return False


def collision_midpoint(a, b, n_checks=20):
    """Return midpoint of first collision along segment, or None."""
    for t in np.linspace(0, 1, n_checks):
        p = a + t * (b - a)
        if point_in_obstacle(p):
            return (a + b) / 2.0
    return None


def draw_obstacles(ax, alpha=OBS_ALPHA):
    """Draw obstacle rectangles on ax."""
    for (ox, oy, ow, oh) in OBSTACLES:
        ax.add_patch(Rectangle((ox, oy), ow, oh,
                                facecolor=OBS_FACE, edgecolor=OBS_EDGE,
                                linewidth=1.2, alpha=alpha))


def draw_start_goal(ax, markersize=10):
    """Draw start (green) and goal (orange) markers."""
    ax.plot(*START, "o", color=START_CLR, markersize=markersize,
            zorder=10, markeredgecolor="k", markeredgewidth=0.8, label="Start")
    ax.plot(*GOAL, "*", color=GOAL_CLR, markersize=markersize + 4,
            zorder=10, markeredgecolor="k", markeredgewidth=0.8, label="Goal")


def setup_ax(ax, title=""):
    """Standard axis setup."""
    ax.set_xlim(*X_LIM)
    ax.set_ylim(*Y_LIM)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.25, linewidth=0.5)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title:
        ax.set_title(title, fontsize=11, fontweight="bold")


def savefig(fig, name):
    """Save figure and close."""
    path = IMG_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  ✓ saved {path.name}")


def build_obstacle_mask():
    """Return boolean grid (NY, NX) — True where obstacle."""
    mask = np.zeros((NY, NX), dtype=bool)
    for iy in range(NY):
        for ix in range(NX):
            px = X_LIM[0] + (ix + 0.5) * GRID_RES
            py = Y_LIM[0] + (iy + 0.5) * GRID_RES
            if point_in_obstacle(np.array([px, py])):
                mask[iy, ix] = True
    return mask


def boundary_bias_density(obs_mask, sigma=5.0, base=0.3):
    """Compute initial density: uniform + boost near obstacle boundaries."""
    from scipy.ndimage import distance_transform_edt, binary_dilation
    dilated = binary_dilation(obs_mask, iterations=3)
    boundary = dilated & ~obs_mask
    density = np.full((NY, NX), base)
    density[boundary] = 1.0
    density = gaussian_filter(density.astype(float), sigma=sigma)
    density[obs_mask] = 0.0
    density = np.clip(density, 0, None)
    s = density.sum()
    if s > 0:
        density /= s
    return density


def sample_from_density(density, n_samples):
    """Sample n_samples free-space points from density grid."""
    flat = density.ravel()
    s = flat.sum()
    if s <= 0:
        flat = np.ones_like(flat)
        flat /= flat.sum()
    else:
        flat = flat / s
    indices = np.random.choice(len(flat), size=n_samples * 3, p=flat)
    iy, ix = np.unravel_index(indices, (NY, NX))
    pts = np.column_stack([
        X_LIM[0] + (ix + np.random.rand(len(ix))) * GRID_RES,
        Y_LIM[0] + (iy + np.random.rand(len(iy))) * GRID_RES,
    ])
    free = np.array([not point_in_obstacle(p) for p in pts])
    pts = pts[free]
    return pts[:n_samples]


def build_roadmap(nodes, radius):
    """Build roadmap edges (collision-checked)."""
    edges = []
    coll_mids = []
    n = len(nodes)
    for i in range(n):
        for j in range(i + 1, n):
            d = np.linalg.norm(nodes[i] - nodes[j])
            if d < radius:
                mid = collision_midpoint(nodes[i], nodes[j])
                if mid is not None:
                    coll_mids.append(mid)
                else:
                    edges.append((i, j))
    return edges, np.array(coll_mids) if coll_mids else np.empty((0, 2))


def dijkstra(nodes, edges, start_idx, goal_idx):
    """Shortest path on graph. Return path indices or None."""
    adj = {i: [] for i in range(len(nodes))}
    for (i, j) in edges:
        d = np.linalg.norm(nodes[i] - nodes[j])
        adj[i].append((j, d))
        adj[j].append((i, d))
    dist = {i: float("inf") for i in range(len(nodes))}
    prev = {i: None for i in range(len(nodes))}
    dist[start_idx] = 0
    pq = [(0, start_idx)]
    while pq:
        cd, u = heapq.heappop(pq)
        if u == goal_idx:
            break
        if cd > dist[u]:
            continue
        for v, w in adj[u]:
            nd = cd + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if dist[goal_idx] == float("inf"):
        return None
    path = []
    c = goal_idx
    while c is not None:
        path.append(c)
        c = prev[c]
    return path[::-1]


def draw_edges(ax, nodes, edges, color=EDGE_CLR, alpha=0.3, lw=0.6):
    """Draw edges as a LineCollection."""
    if not edges:
        return
    segs = [[nodes[i], nodes[j]] for (i, j) in edges]
    lc = LineCollection(segs, colors=color, alpha=alpha, linewidths=lw)
    ax.add_collection(lc)


def draw_path(ax, nodes, path_idx, color=PATH_CLR, lw=2.5, ls="-", label="Best path"):
    """Draw path on ax."""
    if path_idx is None:
        return
    pts = nodes[path_idx]
    ax.plot(pts[:, 0], pts[:, 1], ls, color=color, linewidth=lw,
            zorder=8, label=label)


def draw_density_heatmap(ax, density, title="", cmap="YlOrRd"):
    """Draw density heatmap."""
    extent = [X_LIM[0], X_LIM[1], Y_LIM[0], Y_LIM[1]]
    im = ax.imshow(density, origin="lower", extent=extent, cmap=cmap,
                   aspect="equal", interpolation="bilinear")
    draw_obstacles(ax, alpha=0.5)
    setup_ax(ax, title)
    return im


# =====================================================================
#  Adaptive PRM
# =====================================================================

def run_adaptive_prm():
    """Run Adaptive PRM and generate images A1–A5 + final images."""
    print("\n╔══════════════════════════════════════╗")
    print("║   Adaptive PRM — density-guided      ║")
    print("╚══════════════════════════════════════╝")

    obs_mask = build_obstacle_mask()
    density = boundary_bias_density(obs_mask, sigma=4.0, base=0.3)
    density_history = [density.copy()]

    # ── A1: Initial density map ──────────────────────────────────
    print("[A1] Initial density map …")
    fig, ax = plt.subplots(figsize=(8, 5.6))
    draw_density_heatmap(ax, density, "A1 — Initial Density Map (uniform + boundary bias)")
    draw_start_goal(ax)
    ax.legend(loc="lower right", fontsize=8)
    fig.colorbar(ax.images[0], ax=ax, shrink=0.7, label="sampling weight")
    savefig(fig, "A1_adaptive_prm_step0_init_density.png")

    # ── Iterate ──────────────────────────────────────────────────
    all_nodes = np.array([START, GOAL])
    all_edges = []
    all_coll_mids = np.empty((0, 2))
    n_samples_per_iter = [40, 50, 60, 70]
    radius = 2.2

    for it in range(4):
        iter_num = it + 1
        name = f"A{iter_num + 1}"
        print(f"[{name}] Iteration {iter_num}/4 …")

        # Sample
        new_pts = sample_from_density(density, n_samples_per_iter[it])
        old_n = len(all_nodes)
        all_nodes = np.vstack([all_nodes, new_pts])

        # Build edges for new nodes
        new_edges = []
        iter_coll_mids = []
        for i in range(old_n, len(all_nodes)):
            for j in range(i):
                d = np.linalg.norm(all_nodes[i] - all_nodes[j])
                if d < radius:
                    mid = collision_midpoint(all_nodes[i], all_nodes[j])
                    if mid is not None:
                        iter_coll_mids.append(mid)
                    else:
                        new_edges.append((i, j))
        all_edges.extend(new_edges)
        iter_coll_mids = np.array(iter_coll_mids) if iter_coll_mids else np.empty((0, 2))
        all_coll_mids = np.vstack([all_coll_mids, iter_coll_mids]) if len(iter_coll_mids) > 0 else all_coll_mids

        # Update density: boost around collision midpoints
        if len(iter_coll_mids) > 0:
            for cm in iter_coll_mids:
                ix = int((cm[0] - X_LIM[0]) / GRID_RES)
                iy = int((cm[1] - Y_LIM[0]) / GRID_RES)
                ix = np.clip(ix, 0, NX - 1)
                iy = np.clip(iy, 0, NY - 1)
                r = 8
                y_lo, y_hi = max(0, iy - r), min(NY, iy + r + 1)
                x_lo, x_hi = max(0, ix - r), min(NX, ix + r + 1)
                density[y_lo:y_hi, x_lo:x_hi] += 0.5
        density = gaussian_filter(density, sigma=3.0)
        density[obs_mask] = 0.0
        density = np.clip(density, 0, None)
        s = density.sum()
        if s > 0:
            density /= s
        density_history.append(density.copy())

        # Shortest path
        path_idx = dijkstra(all_nodes, all_edges, 0, 1)

        # ── 3-panel figure ───────────────────────────────────────
        fig, axes = plt.subplots(1, 3, figsize=(18, 5.2))

        # Panel A: roadmap + new samples
        ax = axes[0]
        draw_obstacles(ax)
        draw_edges(ax, all_nodes, all_edges, alpha=0.25)
        ax.scatter(all_nodes[2:old_n, 0], all_nodes[2:old_n, 1],
                   s=12, c=SAMPLE_CLR, alpha=0.4, zorder=4)
        ax.scatter(new_pts[:, 0], new_pts[:, 1],
                   s=22, c="#E53935", marker="o", alpha=0.8, zorder=5,
                   label=f"New samples (iter {iter_num})")
        if path_idx is not None and iter_num >= 3:
            draw_path(ax, all_nodes, path_idx)
        draw_start_goal(ax)
        ax.legend(loc="lower right", fontsize=7)
        setup_ax(ax, f"A — Roadmap (iter {iter_num})")

        # Panel B: collision midpoints
        ax = axes[1]
        draw_obstacles(ax)
        draw_edges(ax, all_nodes, all_edges, alpha=0.15)
        if len(all_coll_mids) > 0:
            ax.scatter(all_coll_mids[:, 0], all_coll_mids[:, 1],
                       s=40, c=COLLISION_CLR, marker="x", linewidths=1.5,
                       zorder=6, label="Collision midpoints")
        draw_start_goal(ax, markersize=8)
        ax.legend(loc="lower right", fontsize=7)
        setup_ax(ax, f"B — Collision midpoints (cumulative)")

        # Panel C: updated density
        ax = axes[2]
        draw_density_heatmap(ax, density, f"C — Updated density (iter {iter_num})")
        draw_start_goal(ax, markersize=8)
        fig.colorbar(ax.images[0], ax=ax, shrink=0.75, label="weight")

        fig.suptitle(f"Adaptive PRM — Iteration {iter_num}/4",
                     fontsize=13, fontweight="bold", y=1.02)
        fig.tight_layout()
        savefig(fig, f"A{iter_num + 1}_adaptive_prm_iter{iter_num}.png")

    # ── A_final: Density evolution ───────────────────────────────
    print("[A_final] Density evolution …")
    fig, axes = plt.subplots(1, 5, figsize=(22, 4))
    for k, ax in enumerate(axes):
        draw_density_heatmap(ax, density_history[k],
                             f"Iter {k}", cmap="YlOrRd")
        draw_start_goal(ax, markersize=6)
    fig.suptitle("Adaptive PRM — Density Evolution (iter 0 → 4)",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    savefig(fig, "A_final_adaptive_prm_density_evolution.png")

    # ── A_compare: Final roadmap vs heatmap ──────────────────────
    print("[A_compare] Final comparison …")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.6))

    ax = axes[0]
    draw_obstacles(ax)
    draw_edges(ax, all_nodes, all_edges, alpha=0.25)
    ax.scatter(all_nodes[2:, 0], all_nodes[2:, 1],
               s=10, c=SAMPLE_CLR, alpha=0.5, zorder=4)
    path_idx = dijkstra(all_nodes, all_edges, 0, 1)
    draw_path(ax, all_nodes, path_idx)
    draw_start_goal(ax)
    ax.legend(loc="lower right", fontsize=8)
    setup_ax(ax, "Final Roadmap + Best Path")

    ax = axes[1]
    draw_density_heatmap(ax, density_history[-1], "Sampling Focus (density)")
    draw_start_goal(ax, markersize=8)
    fig.colorbar(ax.images[0], ax=ax, shrink=0.75, label="weight")

    fig.suptitle("Adaptive PRM — Final Comparison",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    savefig(fig, "A_compare_adaptive_prm_final.png")


# =====================================================================
#  Lazy PRM*
# =====================================================================

def prm_star_radius(n, d=2, gamma=12.0):
    """PRM* connection radius: r(n) = gamma * (ln(n)/n)^(1/d)."""
    if n < 2:
        return gamma
    return gamma * (np.log(n) / n) ** (1.0 / d)


def run_lazy_prm_star():
    """Run Lazy PRM* and generate images L1–L6."""
    print("\n╔══════════════════════════════════════╗")
    print("║   Lazy PRM* — lazy collision check   ║")
    print("╚══════════════════════════════════════╝")

    np.random.seed(42)  # reseed for independent reproducibility

    # ── Sample nodes ─────────────────────────────────────────────
    n_samples = 200
    pts = []
    while len(pts) < n_samples:
        p = np.array([np.random.uniform(*X_LIM),
                       np.random.uniform(*Y_LIM)])
        if not point_in_obstacle(p):
            pts.append(p)
    nodes = np.array([START, GOAL] + pts)
    n = len(nodes)
    r = prm_star_radius(n, d=2)

    # ── L1: Sample nodes + PRM* radius ──────────────────────────
    print("[L1] Sample nodes + PRM* radius …")
    fig, ax = plt.subplots(figsize=(8, 5.6))
    draw_obstacles(ax)
    ax.scatter(nodes[2:, 0], nodes[2:, 1], s=14, c=SAMPLE_CLR,
               alpha=0.7, zorder=4, label=f"Samples (n={n})")
    draw_start_goal(ax)
    # Show radius circle on a few nodes
    for idx in [0, 1, 20, 80, 140]:
        circle = plt.Circle(nodes[idx], r, fill=False, linestyle="--",
                            edgecolor="#E91E63", linewidth=1.0, alpha=0.6)
        ax.add_patch(circle)
    ax.plot([], [], "--", color="#E91E63", alpha=0.6,
            label=f"PRM* radius r={r:.2f}")
    ax.legend(loc="lower right", fontsize=8)
    setup_ax(ax, f"L1 — Samples + PRM* radius  r(n)∝(ln n/n)^{{1/d}}")
    ax.text(0.02, 0.02, f"n = {n},  r = {r:.2f}",
            transform=ax.transAxes, fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))
    savefig(fig, "L1_lazy_prm_star_step1_samples.png")

    # ── Build ALL radius edges (no collision check) ──────────────
    all_potential_edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if np.linalg.norm(nodes[i] - nodes[j]) < r:
                all_potential_edges.append((i, j))
    total_edges = len(all_potential_edges)

    # Classify: colliding or free
    edge_collides = {}
    for (i, j) in all_potential_edges:
        edge_collides[(i, j)] = segment_collides(nodes[i], nodes[j])

    free_edges = [(i, j) for (i, j) in all_potential_edges if not edge_collides[(i, j)]]
    coll_edges = [(i, j) for (i, j) in all_potential_edges if edge_collides[(i, j)]]

    # ── L2: Unchecked graph ──────────────────────────────────────
    print("[L2] Unchecked graph …")
    fig, ax = plt.subplots(figsize=(8, 5.6))
    draw_obstacles(ax)
    draw_edges(ax, nodes, free_edges, color="#999999", alpha=0.3, lw=0.5)
    draw_edges(ax, nodes, coll_edges, color=CHECKED_FAIL_CLR, alpha=0.45, lw=0.7)
    ax.scatter(nodes[2:, 0], nodes[2:, 1], s=10, c=SAMPLE_CLR, alpha=0.5, zorder=4)
    draw_start_goal(ax)
    ax.plot([], [], "-", color="#999999", alpha=0.5, label=f"Free edges")
    ax.plot([], [], "-", color=CHECKED_FAIL_CLR, alpha=0.6,
            label=f"Colliding edges (unknown)")
    ax.legend(loc="lower right", fontsize=8)
    setup_ax(ax, f"L2 — All {total_edges} edges built, NO collision check")
    savefig(fig, "L2_lazy_prm_star_step2_unchecked_graph.png")

    # ── Lazy evaluation loop ─────────────────────────────────────
    forbidden = set()          # edges confirmed colliding
    checked_count = 0          # total collision checks done
    iteration_data = []        # for L4

    max_iters = 12
    final_path = None

    for it in range(max_iters):
        # Build graph with non-forbidden edges
        active_edges = [(i, j) for (i, j) in all_potential_edges
                        if (i, j) not in forbidden]
        path_idx = dijkstra(nodes, active_edges, 0, 1)
        if path_idx is None:
            break

        # Check only path edges
        path_edges = list(zip(path_idx[:-1], path_idx[1:]))
        collision_found = False
        iter_checks = 0
        removed_this_iter = []
        for (u, v) in path_edges:
            key = (min(u, v), max(u, v))
            if key in forbidden:
                continue
            iter_checks += 1
            checked_count += 1
            if edge_collides.get(key, segment_collides(nodes[u], nodes[v])):
                forbidden.add(key)
                removed_this_iter.append(key)
                collision_found = True

        iteration_data.append({
            "path_idx": path_idx,
            "forbidden": set(forbidden),
            "removed": removed_this_iter,
            "checks": iter_checks,
            "total_checks": checked_count,
            "collision_found": collision_found,
        })

        if not collision_found:
            final_path = path_idx
            break

    n_iters = len(iteration_data)

    # ── L3: Iteration 1 (Dijkstra -> validate) ──────────────────
    print("[L3] Iteration 1 detail …")
    it0 = iteration_data[0]
    fig, ax = plt.subplots(figsize=(8, 5.6))
    draw_obstacles(ax)
    active0 = [(i, j) for (i, j) in all_potential_edges
                if (i, j) not in it0["forbidden"]]
    draw_edges(ax, nodes, active0, color="#CCCCCC", alpha=0.2, lw=0.4)
    # Proposed path (blue dashed)
    ppts = nodes[it0["path_idx"]]
    ax.plot(ppts[:, 0], ppts[:, 1], "--", color=CHECKED_OK_CLR, linewidth=2.2,
            zorder=7, label="Proposed path (Dijkstra)")
    # Mark removed edges
    for (u, v) in it0["removed"]:
        ax.plot([nodes[u][0], nodes[v][0]], [nodes[u][1], nodes[v][1]],
                "-", color=CHECKED_FAIL_CLR, linewidth=2.0, alpha=0.8, zorder=6)
    if it0["removed"]:
        ax.plot([], [], "-", color=CHECKED_FAIL_CLR, linewidth=2.0,
                label="Collision → removed")
    ax.scatter(nodes[2:, 0], nodes[2:, 1], s=8, c=SAMPLE_CLR, alpha=0.4, zorder=3)
    draw_start_goal(ax)
    ax.legend(loc="lower right", fontsize=8)
    setup_ax(ax, f"L3 — Iter 1: Dijkstra path → check {it0['checks']} edges → replan")
    savefig(fig, "L3_lazy_prm_star_step3_iter1.png")

    # ── L4: All iterations grid ──────────────────────────────────
    print("[L4] All iterations grid …")
    n_show = min(n_iters, 6)
    cols = 3
    rows = (n_show + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows))
    axes_flat = np.array(axes).ravel()

    for k in range(n_show):
        ax = axes_flat[k]
        itk = iteration_data[k]
        active_k = [(i, j) for (i, j) in all_potential_edges
                     if (i, j) not in itk["forbidden"]]
        draw_obstacles(ax)
        draw_edges(ax, nodes, active_k, color="#CCCCCC", alpha=0.2, lw=0.3)
        # Forbidden edges in faded red
        for fe in itk["forbidden"]:
            ax.plot([nodes[fe[0]][0], nodes[fe[1]][0]],
                    [nodes[fe[0]][1], nodes[fe[1]][1]],
                    "-", color=CHECKED_FAIL_CLR, linewidth=0.8, alpha=0.35)
        # Path
        ppts_k = nodes[itk["path_idx"]]
        style = "-" if not itk["collision_found"] else "--"
        clr = "#4CAF50" if not itk["collision_found"] else CHECKED_OK_CLR
        ax.plot(ppts_k[:, 0], ppts_k[:, 1], style, color=clr,
                linewidth=2.0, zorder=7)
        # Removed this iter
        for (u, v) in itk["removed"]:
            ax.plot([nodes[u][0], nodes[v][0]], [nodes[u][1], nodes[v][1]],
                    "-", color=CHECKED_FAIL_CLR, linewidth=2.0, alpha=0.9, zorder=8)
        draw_start_goal(ax, markersize=7)
        setup_ax(ax, f"Iter {k + 1}  (checks: {itk['checks']}, "
                      f"forbidden: {len(itk['forbidden'])})")

    for k in range(n_show, len(axes_flat)):
        axes_flat[k].set_visible(False)

    fig.suptitle("Lazy PRM* — All Replan Iterations",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    savefig(fig, "L4_lazy_prm_star_all_iters.png")

    # ── L5: Final path ───────────────────────────────────────────
    print("[L5] Final collision-free path …")
    fig, ax = plt.subplots(figsize=(8, 5.6))
    draw_obstacles(ax)
    final_active = [(i, j) for (i, j) in all_potential_edges
                     if (i, j) not in forbidden]
    draw_edges(ax, nodes, final_active, color="#CCCCCC", alpha=0.2, lw=0.4)
    ax.scatter(nodes[2:, 0], nodes[2:, 1], s=10, c=SAMPLE_CLR, alpha=0.4, zorder=3)
    if final_path is not None:
        draw_path(ax, nodes, final_path, color="#4CAF50", lw=3.0,
                  label="Final path (collision-free)")
    draw_start_goal(ax)
    ax.legend(loc="lower right", fontsize=8)
    setup_ax(ax, f"L5 — Final Path: {checked_count} checks / {total_edges} edges "
                 f"→ {100*(1 - checked_count/max(total_edges,1)):.0f}% saved")
    savefig(fig, "L5_lazy_prm_star_final_path.png")

    # ── L6: Efficiency charts ────────────────────────────────────
    print("[L6] Efficiency charts …")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Bar chart: Eager vs Lazy
    ax = axes[0]
    bars = ax.bar(["Eager PRM*\n(check all)", "Lazy PRM*\n(check on path)"],
                  [total_edges, checked_count],
                  color=["#EF5350", "#66BB6A"], edgecolor="k", linewidth=0.8)
    for bar, val in zip(bars, [total_edges, checked_count]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 15,
                str(val), ha="center", fontsize=11, fontweight="bold")
    ax.set_ylabel("# collision checks")
    ax.set_title("Eager vs Lazy — Total Collision Checks", fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    # Step chart: checks per iteration
    ax = axes[1]
    iters = list(range(1, n_iters + 1))
    cum_checks = [iteration_data[k]["total_checks"] for k in range(n_iters)]
    ax.step(iters, cum_checks, where="mid", color=CHECKED_OK_CLR,
            linewidth=2.0, marker="o", markersize=6)
    ax.fill_between(iters, cum_checks, step="mid", alpha=0.15,
                    color=CHECKED_OK_CLR)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Cumulative collision checks")
    ax.set_title("Checks per Iteration (step chart)", fontweight="bold")
    ax.set_xticks(iters)
    ax.grid(True, alpha=0.3)

    fig.suptitle("Lazy PRM* — Efficiency",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    savefig(fig, "L6_lazy_prm_star_efficiency.png")

    return checked_count, total_edges


# =====================================================================
#  Main
# =====================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  Generating Adaptive PRM & Lazy PRM* images")
    print("=" * 50)

    run_adaptive_prm()
    run_lazy_prm_star()

    print("\n✅ All 13 images generated in", IMG_DIR)
