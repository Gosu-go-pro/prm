#!/usr/bin/env python3
"""Generate all 13 PRM variant demo images described in README.md.

Implements Classic PRM, Gaussian PRM, Bridge PRM, Lazy PRM, PRM*, and
Visibility PRM on a 10×10 world with rectangular obstacles.

Output directory: images/ relative to this script.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
import heapq

# ── Reproducibility ───────────────────────────────────────────────
np.random.seed(42)

# ── Output directory ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
IMG_DIR = SCRIPT_DIR / "images"
IMG_DIR.mkdir(exist_ok=True)

# ── World ─────────────────────────────────────────────────────────
X_LIM = (0.0, 10.0)
Y_LIM = (0.0, 10.0)
START = np.array([1.0, 1.0])
GOAL = np.array([9.0, 9.0])

# Rectangles (x, y, w, h) — two horizontal bars create a narrow passage
OBSTACLES = [
    (1.0, 4.5, 3.2, 0.8),   # horizontal bar left
    (5.0, 4.5, 4.5, 0.8),   # horizontal bar right  (gap x ∈ [4.2, 5.0])
    (7.0, 1.0, 0.8, 2.5),   # vertical bar lower-right
    (2.5, 7.5, 1.2, 1.2),   # small square upper-left
    (6.5, 7.0, 2.8, 0.6),   # horizontal bar upper-right
]

# Narrow passage bounding box (for zoom images)
ZOOM_X = (3.2, 5.8)
ZOOM_Y = (3.5, 6.0)

# ── Colours ───────────────────────────────────────────────────────
OBS_FACE = "#B0CFE4"
OBS_ALPHA = 0.65
SAMPLE_CLR = "#1f77b4"
START_GOAL_CLR = "#ff7f0e"
EDGE_CLR = "#1f77b4"
PATH_CLR = "#8c564b"
UNCHECKED_EDGE_CLR = "#9467bd"
GUARD_CLR = "#2ca02c"
CONNECTOR_CLR = "#d62728"

N_COLL_SAMPLES = 30  # samples along a segment for collision check

# ══════════════════════════════════════════════════════════════════
# Geometry helpers
# ══════════════════════════════════════════════════════════════════

def pt_in_obs(pt):
    """Return True if *pt* is inside any obstacle."""
    for ox, oy, ow, oh in OBSTACLES:
        if ox <= pt[0] <= ox + ow and oy <= pt[1] <= oy + oh:
            return True
    return False


def seg_free(a, b, n=N_COLL_SAMPLES):
    """Return True if the segment a→b is collision-free."""
    for t in np.linspace(0, 1, n):
        if pt_in_obs(a + t * (b - a)):
            return False
    return True


def dist(a, b):
    return np.linalg.norm(a - b)


# ══════════════════════════════════════════════════════════════════
# Sampling helpers
# ══════════════════════════════════════════════════════════════════

def sample_uniform(n):
    """Return *n* collision-free uniform samples."""
    pts = []
    while len(pts) < n:
        p = np.array([np.random.uniform(*X_LIM), np.random.uniform(*Y_LIM)])
        if not pt_in_obs(p):
            pts.append(p)
    return np.array(pts)


def sample_gaussian(n, sigma=1.0):
    """Gaussian PRM: keep a sample if exactly one of a pair collides."""
    pts = []
    while len(pts) < n:
        p1 = np.array([np.random.uniform(*X_LIM), np.random.uniform(*Y_LIM)])
        p2 = p1 + np.random.normal(0, sigma, size=2)
        if not (X_LIM[0] <= p2[0] <= X_LIM[1] and Y_LIM[0] <= p2[1] <= Y_LIM[1]):
            continue
        c1, c2 = pt_in_obs(p1), pt_in_obs(p2)
        if c1 and not c2:
            pts.append(p2)
        elif c2 and not c1:
            pts.append(p1)
    return np.array(pts)


def sample_bridge(n, sigma=1.2):
    """Bridge PRM: both endpoints collide, keep midpoint if free."""
    pts = []
    attempts = 0
    max_attempts = n * 500
    while len(pts) < n and attempts < max_attempts:
        attempts += 1
        p1 = np.array([np.random.uniform(*X_LIM), np.random.uniform(*Y_LIM)])
        if not pt_in_obs(p1):
            continue
        p2 = p1 + np.random.normal(0, sigma, size=2)
        if not (X_LIM[0] <= p2[0] <= X_LIM[1] and Y_LIM[0] <= p2[1] <= Y_LIM[1]):
            continue
        if not pt_in_obs(p2):
            continue
        mid = (p1 + p2) / 2.0
        if not pt_in_obs(mid):
            pts.append(mid)
    return np.array(pts) if pts else np.empty((0, 2))


# ══════════════════════════════════════════════════════════════════
# Graph helpers
# ══════════════════════════════════════════════════════════════════

def knn_edges(nodes, k, check_collision=True):
    """Return list of (i, j) edges using k-nearest-neighbours."""
    from scipy.spatial import KDTree
    tree = KDTree(nodes)
    edges = set()
    for i, node in enumerate(nodes):
        dists, idxs = tree.query(node, k=k + 1)
        for j_pos in range(1, len(idxs)):
            j = idxs[j_pos]
            if j == i:
                continue
            edge = (min(i, j), max(i, j))
            if edge in edges:
                continue
            if check_collision and not seg_free(nodes[i], nodes[j]):
                continue
            edges.add(edge)
    return list(edges)


def radius_edges(nodes, r, check_collision=True):
    """Return list of (i, j) edges within radius *r*."""
    from scipy.spatial import KDTree
    tree = KDTree(nodes)
    edges = set()
    for i, node in enumerate(nodes):
        idxs = tree.query_ball_point(node, r)
        for j in idxs:
            if j <= i:
                continue
            if check_collision and not seg_free(nodes[i], nodes[j]):
                continue
            edges.add((i, j))
    return list(edges)


def dijkstra(nodes, edges, start_idx, goal_idx):
    """Return shortest-path index list or None."""
    adj = {i: [] for i in range(len(nodes))}
    for i, j in edges:
        d = dist(nodes[i], nodes[j])
        adj[i].append((j, d))
        adj[j].append((i, d))
    visited = set()
    heap = [(0.0, start_idx, [start_idx])]
    while heap:
        cost, u, path = heapq.heappop(heap)
        if u == goal_idx:
            return path
        if u in visited:
            continue
        visited.add(u)
        for v, w in adj[u]:
            if v not in visited:
                heapq.heappush(heap, (cost + w, v, path + [v]))
    return None


# ══════════════════════════════════════════════════════════════════
# Drawing helpers
# ══════════════════════════════════════════════════════════════════

def draw_obstacles(ax):
    for ox, oy, ow, oh in OBSTACLES:
        ax.add_patch(Rectangle((ox, oy), ow, oh,
                               facecolor=OBS_FACE, edgecolor="black",
                               linewidth=0.8, alpha=OBS_ALPHA))


def draw_start_goal(ax):
    ax.plot(*START, marker="x", color=START_GOAL_CLR, ms=12, mew=3, zorder=5)
    ax.plot(*GOAL, marker="x", color=START_GOAL_CLR, ms=12, mew=3, zorder=5)
    ax.annotate("Start", START, textcoords="offset points",
                xytext=(8, -12), fontsize=9, color=START_GOAL_CLR, fontweight="bold")
    ax.annotate("Goal", GOAL, textcoords="offset points",
                xytext=(8, -12), fontsize=9, color=START_GOAL_CLR, fontweight="bold")


def new_fig(title, xlim=X_LIM, ylim=Y_LIM):
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=0.25)
    return fig, ax


def save(fig, name):
    path = IMG_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    print(f"  saved {path.name}")


# ══════════════════════════════════════════════════════════════════
# Build nodes array with Start and Goal as first two entries
# ══════════════════════════════════════════════════════════════════

def build_nodes(samples):
    """Prepend START (idx 0) and GOAL (idx 1) to *samples*."""
    return np.vstack([START, GOAL, samples])


# ══════════════════════════════════════════════════════════════════
# Image generators
# ══════════════════════════════════════════════════════════════════

def gen_classic_prm():
    print("Classic PRM …")
    N = 250
    K = 8
    samples = sample_uniform(N)
    nodes = build_nodes(samples)

    # --- Step 1: samples ---
    fig, ax = new_fig("PRM Classic — Step 1: Uniform Sampling")
    draw_obstacles(ax)
    ax.scatter(samples[:, 0], samples[:, 1], s=8, c=SAMPLE_CLR, zorder=3)
    draw_start_goal(ax)
    save(fig, "01_prm_classic_step1_samples.png")

    # --- Step 2: k-NN connections ---
    edges = knn_edges(nodes, K, check_collision=True)
    fig, ax = new_fig("PRM Classic — Step 2: k-NN Connections")
    draw_obstacles(ax)
    for i, j in edges:
        ax.plot([nodes[i][0], nodes[j][0]], [nodes[i][1], nodes[j][1]],
                c=EDGE_CLR, lw=0.4, alpha=0.5, zorder=2)
    ax.scatter(nodes[2:, 0], nodes[2:, 1], s=8, c=SAMPLE_CLR, zorder=3)
    draw_start_goal(ax)
    save(fig, "02_prm_classic_step2_connections.png")

    # --- Step 3: shortest path ---
    path_idxs = dijkstra(nodes, edges, 0, 1)
    fig, ax = new_fig("PRM Classic — Step 3: Shortest Path")
    draw_obstacles(ax)
    for i, j in edges:
        ax.plot([nodes[i][0], nodes[j][0]], [nodes[i][1], nodes[j][1]],
                c=EDGE_CLR, lw=0.3, alpha=0.3, zorder=2)
    ax.scatter(nodes[2:, 0], nodes[2:, 1], s=6, c=SAMPLE_CLR, alpha=0.4, zorder=3)
    if path_idxs:
        pp = nodes[path_idxs]
        ax.plot(pp[:, 0], pp[:, 1], c=PATH_CLR, lw=2.5, zorder=4, label="Shortest path")
        ax.legend(loc="lower right", fontsize=9)
    draw_start_goal(ax)
    save(fig, "03_prm_classic_step3_path.png")

    return nodes, edges  # reuse for zoom-uniform


def gen_gaussian_prm():
    print("Gaussian PRM …")
    N = 250
    K = 8
    samples = sample_gaussian(N, sigma=1.0)
    nodes = build_nodes(samples)
    edges = knn_edges(nodes, K, check_collision=True)

    fig, ax = new_fig("Gaussian PRM — Samples Near Obstacle Boundaries")
    draw_obstacles(ax)
    for i, j in edges:
        ax.plot([nodes[i][0], nodes[j][0]], [nodes[i][1], nodes[j][1]],
                c=EDGE_CLR, lw=0.4, alpha=0.4, zorder=2)
    ax.scatter(samples[:, 0], samples[:, 1], s=8, c=SAMPLE_CLR, zorder=3)
    draw_start_goal(ax)
    save(fig, "04_gaussian_prm_step1_samples.png")
    return nodes, edges


def gen_bridge_prm():
    print("Bridge PRM …")
    N_bridge = 120
    N_uniform = 150
    K = 8
    bridge_samples = sample_bridge(N_bridge, sigma=1.2)
    uniform_samples = sample_uniform(N_uniform)
    if len(bridge_samples) > 0:
        samples = np.vstack([bridge_samples, uniform_samples])
    else:
        samples = uniform_samples
    nodes = build_nodes(samples)
    edges = knn_edges(nodes, K, check_collision=True)

    fig, ax = new_fig("Bridge PRM — Samples in Narrow Passages")
    draw_obstacles(ax)
    for i, j in edges:
        ax.plot([nodes[i][0], nodes[j][0]], [nodes[i][1], nodes[j][1]],
                c=EDGE_CLR, lw=0.4, alpha=0.4, zorder=2)
    ax.scatter(samples[:, 0], samples[:, 1], s=8, c=SAMPLE_CLR, zorder=3)
    draw_start_goal(ax)
    save(fig, "05_bridge_prm_step1_samples.png")
    return nodes, edges


def gen_zoom_images():
    print("Zoom images …")
    N = 400
    K = 8

    # Uniform
    u_samples = sample_uniform(N)
    fig, ax = new_fig("Zoom — Uniform Sampling", xlim=ZOOM_X, ylim=ZOOM_Y)
    draw_obstacles(ax)
    mask = ((u_samples[:, 0] >= ZOOM_X[0]) & (u_samples[:, 0] <= ZOOM_X[1]) &
            (u_samples[:, 1] >= ZOOM_Y[0]) & (u_samples[:, 1] <= ZOOM_Y[1]))
    ax.scatter(u_samples[mask, 0], u_samples[mask, 1], s=18, c=SAMPLE_CLR, zorder=3)
    draw_start_goal(ax)
    save(fig, "06_zoom_uniform.png")

    # Gaussian
    g_samples = sample_gaussian(N, sigma=1.0)
    fig, ax = new_fig("Zoom — Gaussian Sampling", xlim=ZOOM_X, ylim=ZOOM_Y)
    draw_obstacles(ax)
    mask = ((g_samples[:, 0] >= ZOOM_X[0]) & (g_samples[:, 0] <= ZOOM_X[1]) &
            (g_samples[:, 1] >= ZOOM_Y[0]) & (g_samples[:, 1] <= ZOOM_Y[1]))
    ax.scatter(g_samples[mask, 0], g_samples[mask, 1], s=18, c=SAMPLE_CLR, zorder=3)
    draw_start_goal(ax)
    save(fig, "07_zoom_gaussian.png")

    # Bridge
    b_bridge = sample_bridge(200, sigma=1.2)
    b_uniform = sample_uniform(200)
    if len(b_bridge) > 0:
        b_samples = np.vstack([b_bridge, b_uniform])
    else:
        b_samples = b_uniform
    fig, ax = new_fig("Zoom — Bridge Sampling", xlim=ZOOM_X, ylim=ZOOM_Y)
    draw_obstacles(ax)
    mask = ((b_samples[:, 0] >= ZOOM_X[0]) & (b_samples[:, 0] <= ZOOM_X[1]) &
            (b_samples[:, 1] >= ZOOM_Y[0]) & (b_samples[:, 1] <= ZOOM_Y[1]))
    ax.scatter(b_samples[mask, 0], b_samples[mask, 1], s=18, c=SAMPLE_CLR, zorder=3)
    draw_start_goal(ax)
    save(fig, "08_zoom_bridge.png")


def gen_lazy_prm():
    print("Lazy PRM …")
    N = 200
    K = 8
    samples = sample_uniform(N)
    nodes = build_nodes(samples)

    # Step 1: edges WITHOUT collision checking
    all_edges = knn_edges(nodes, K, check_collision=False)

    fig, ax = new_fig("Lazy PRM — Step 1: Unchecked Edges")
    draw_obstacles(ax)
    for i, j in all_edges:
        ax.plot([nodes[i][0], nodes[j][0]], [nodes[i][1], nodes[j][1]],
                c=UNCHECKED_EDGE_CLR, lw=0.5, alpha=0.45, zorder=2)
    ax.scatter(nodes[2:, 0], nodes[2:, 1], s=8, c=SAMPLE_CLR, zorder=3)
    draw_start_goal(ax)
    save(fig, "09_lazy_prm_step1_unchecked_edges.png")

    # Step 2: find path on unchecked graph, then validate path edges
    path_idxs = dijkstra(nodes, all_edges, 0, 1)

    # Separate valid/invalid path edges and remaining edges
    valid_edges = set()
    invalid_edges = set()
    if path_idxs:
        for a_idx in range(len(path_idxs) - 1):
            ei, ej = path_idxs[a_idx], path_idxs[a_idx + 1]
            edge = (min(ei, ej), max(ei, ej))
            if seg_free(nodes[ei], nodes[ej]):
                valid_edges.add(edge)
            else:
                invalid_edges.add(edge)

    # If some path edges are invalid, re-plan on valid-only graph
    if invalid_edges:
        remaining = [e for e in all_edges if e not in invalid_edges]
        path_idxs = dijkstra(nodes, remaining, 0, 1)
        # Validate new path edges iteratively (simplified: one round)
        if path_idxs:
            valid_edges = set()
            for a_idx in range(len(path_idxs) - 1):
                ei, ej = path_idxs[a_idx], path_idxs[a_idx + 1]
                edge = (min(ei, ej), max(ei, ej))
                if seg_free(nodes[ei], nodes[ej]):
                    valid_edges.add(edge)
                else:
                    invalid_edges.add(edge)
            # Final replanning
            remaining = [e for e in all_edges if e not in invalid_edges]
            path_idxs = dijkstra(nodes, remaining, 0, 1)

    # Checked (valid) edges for the graph
    checked_edges = [e for e in all_edges if seg_free(nodes[e[0]], nodes[e[1]])]

    fig, ax = new_fig("Lazy PRM — Step 2: Validated Path")
    draw_obstacles(ax)
    for i, j in checked_edges:
        ax.plot([nodes[i][0], nodes[j][0]], [nodes[i][1], nodes[j][1]],
                c=EDGE_CLR, lw=0.3, alpha=0.3, zorder=2)
    ax.scatter(nodes[2:, 0], nodes[2:, 1], s=6, c=SAMPLE_CLR, alpha=0.4, zorder=3)
    if path_idxs:
        pp = nodes[path_idxs]
        ax.plot(pp[:, 0], pp[:, 1], c=PATH_CLR, lw=2.5, zorder=4, label="Validated path")
        ax.legend(loc="lower right", fontsize=9)
    draw_start_goal(ax)
    save(fig, "10_lazy_prm_step2_checked_edges_and_path.png")


def gen_prm_star():
    print("PRM* …")
    d = 2  # dimension
    gamma = 12.0  # tuning constant

    # --- Large n ---
    N_large = 500
    samples_large = sample_uniform(N_large)
    nodes_large = build_nodes(samples_large)
    n = len(nodes_large)
    r_large = gamma * (np.log(n) / n) ** (1.0 / d)
    edges_large = radius_edges(nodes_large, r_large, check_collision=True)
    path_large = dijkstra(nodes_large, edges_large, 0, 1)

    fig, ax = new_fig("PRM* — Large n (%d nodes, r=%.2f)" % (n, r_large))
    draw_obstacles(ax)
    for i, j in edges_large:
        ax.plot([nodes_large[i][0], nodes_large[j][0]],
                [nodes_large[i][1], nodes_large[j][1]],
                c=EDGE_CLR, lw=0.3, alpha=0.3, zorder=2)
    ax.scatter(nodes_large[2:, 0], nodes_large[2:, 1], s=5, c=SAMPLE_CLR,
               alpha=0.5, zorder=3)
    if path_large:
        pp = nodes_large[path_large]
        ax.plot(pp[:, 0], pp[:, 1], c=PATH_CLR, lw=2.5, zorder=4, label="Path")
        ax.legend(loc="lower right", fontsize=9)
    draw_start_goal(ax)
    save(fig, "11_prm_star_large_n.png")

    # --- Small n ---
    N_small = 80
    samples_small = sample_uniform(N_small)
    nodes_small = build_nodes(samples_small)
    n = len(nodes_small)
    r_small = gamma * (np.log(n) / n) ** (1.0 / d)
    edges_small = radius_edges(nodes_small, r_small, check_collision=True)
    path_small = dijkstra(nodes_small, edges_small, 0, 1)

    fig, ax = new_fig("PRM* — Small n (%d nodes, r=%.2f)" % (n, r_small))
    draw_obstacles(ax)
    for i, j in edges_small:
        ax.plot([nodes_small[i][0], nodes_small[j][0]],
                [nodes_small[i][1], nodes_small[j][1]],
                c=EDGE_CLR, lw=0.4, alpha=0.4, zorder=2)
    ax.scatter(nodes_small[2:, 0], nodes_small[2:, 1], s=12, c=SAMPLE_CLR, zorder=3)
    if path_small:
        pp = nodes_small[path_small]
        ax.plot(pp[:, 0], pp[:, 1], c=PATH_CLR, lw=2.5, zorder=4, label="Path")
        ax.legend(loc="lower right", fontsize=9)
    draw_start_goal(ax)
    save(fig, "11_prm_star_small_n.png")


def gen_visibility_prm():
    print("Visibility PRM …")
    # Visibility PRM: guards see new free-space regions; connectors link guards
    max_attempts = 3000
    guards = [START.copy(), GOAL.copy()]
    connectors = []
    connector_edges = []  # (guard_i, guard_j) index pairs

    def visible(a, b):
        return seg_free(a, b, n=40)

    def visible_guards(pt):
        """Return indices of guards visible from pt."""
        vis = []
        for gi, g in enumerate(guards):
            if visible(pt, g):
                vis.append(gi)
        return vis

    for _ in range(max_attempts):
        p = np.array([np.random.uniform(*X_LIM), np.random.uniform(*Y_LIM)])
        if pt_in_obs(p):
            continue
        vis = visible_guards(p)
        if len(vis) == 0:
            # New guard — sees a region no existing guard covers
            guards.append(p)
        elif len(vis) >= 2:
            # Connector — links two guards that couldn't see each other
            # Check if any pair of visible guards is not yet connected
            added = False
            for a in range(len(vis)):
                for b in range(a + 1, len(vis)):
                    gi, gj = vis[a], vis[b]
                    edge = (min(gi, gj), max(gi, gj))
                    if edge not in connector_edges:
                        connectors.append(p)
                        connector_edges.append(edge)
                        added = True
                        break
                if added:
                    break

    # Build edge list for path finding
    # Each connector connects its two guards through itself
    # For simplicity, treat guards + connectors as nodes and build adjacency
    all_nodes = list(guards) + list(connectors)
    n_guards = len(guards)
    edges_vis = []
    # Guard-to-guard direct visibility edges from connector_edges
    for gi, gj in connector_edges:
        edges_vis.append((gi, gj))
    # Also add direct guard-guard edges if visible
    for i in range(n_guards):
        for j in range(i + 1, n_guards):
            if visible(all_nodes[i], all_nodes[j]):
                if (i, j) not in edges_vis:
                    edges_vis.append((i, j))

    path_idxs = dijkstra(all_nodes, edges_vis, 0, 1)

    fig, ax = new_fig("Visibility PRM — Guards & Connectors")
    draw_obstacles(ax)
    # Draw edges
    for i, j in edges_vis:
        ax.plot([all_nodes[i][0], all_nodes[j][0]],
                [all_nodes[i][1], all_nodes[j][1]],
                c=EDGE_CLR, lw=0.6, alpha=0.4, zorder=2)
    # Draw guards
    g_arr = np.array(guards)
    ax.scatter(g_arr[2:, 0], g_arr[2:, 1], s=40, c=GUARD_CLR, marker="o",
               zorder=4, label="Guards (%d)" % len(guards))
    # Draw connectors
    if connectors:
        c_arr = np.array(connectors)
        ax.scatter(c_arr[:, 0], c_arr[:, 1], s=25, c=CONNECTOR_CLR, marker="s",
                   zorder=4, label="Connectors (%d)" % len(connectors))
    # Path
    if path_idxs:
        pp = np.array([all_nodes[i] for i in path_idxs])
        ax.plot(pp[:, 0], pp[:, 1], c=PATH_CLR, lw=2.5, zorder=5, label="Path")
    draw_start_goal(ax)
    ax.legend(loc="lower right", fontsize=8)
    save(fig, "13_visibility_prm_concept.png")


# ══════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════

def main():
    print(f"Output directory: {IMG_DIR}")
    gen_classic_prm()
    gen_gaussian_prm()
    gen_bridge_prm()
    gen_zoom_images()
    gen_lazy_prm()
    gen_prm_star()
    gen_visibility_prm()
    print("Done — 13 images generated.")


if __name__ == "__main__":
    main()
