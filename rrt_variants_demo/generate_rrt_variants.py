#!/usr/bin/env python3
"""Generate RRT variant demo images (14 PNGs).

Implements four RRT-family planners on a unit-square world with rectangular
obstacles and renders anatomy, snapshot, and final images for each variant.

Output directory: same as this script.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse
from pathlib import Path

# ── Output directory ──────────────────────────────────────────────
OUT_DIR = Path(__file__).resolve().parent

# ── World ─────────────────────────────────────────────────────────
START = np.array([0.10, 0.10])
GOAL  = np.array([0.90, 0.90])

OBSTACLES = [
    (0.20, 0.35, 0.25, 0.10),   # horizontal bar  x=[0.20,0.45] y=[0.35,0.45]
    (0.55, 0.20, 0.10, 0.30),   # vertical bar     x=[0.55,0.65] y=[0.20,0.50]
    (0.65, 0.65, 0.20, 0.10),   # horizontal bar   x=[0.65,0.85] y=[0.65,0.75]
]

# ── Algorithm parameters ──────────────────────────────────────────
STEP_SIZE   = 0.08
GOAL_RADIUS = 0.08
GOAL_BIAS   = 0.05
N_COLL_SAMPLES = 20       # collision-check samples per segment

# ── Colours ───────────────────────────────────────────────────────
TREE_A_CLR  = "#1f77b4"   # blue
TREE_B_CLR  = "#ff7f0e"   # orange
PATH_CLR    = "#d62728"   # red
OBS_FACE    = "#808080"
OBS_ALPHA   = 0.40
START_CLR   = "#2ca02c"   # green
GOAL_CLR    = "#d62728"   # red
XRAND_CLR   = "#9467bd"   # purple
XNEAR_CLR   = "#8c564b"   # brown
XNEW_CLR    = "#e377c2"   # pink
NEIGH_CLR   = "#17becf"   # cyan
ELLIPSE_CLR = "#bcbd22"   # olive


# ══════════════════════════════════════════════════════════════════
# Geometry helpers
# ══════════════════════════════════════════════════════════════════

def _dist(a, b):
    return np.linalg.norm(a - b)


def _steer(x_from, x_to, step=STEP_SIZE):
    d = _dist(x_from, x_to)
    if d <= step:
        return x_to.copy()
    return x_from + (x_to - x_from) / d * step


def _pt_in_obs(pt):
    for ox, oy, ow, oh in OBSTACLES:
        if ox <= pt[0] <= ox + ow and oy <= pt[1] <= oy + oh:
            return True
    return False


def _seg_free(a, b, n=N_COLL_SAMPLES):
    for t in np.linspace(0, 1, n):
        if _pt_in_obs(a + t * (b - a)):
            return False
    return True


def _nearest_idx(nodes, pt):
    return int(np.argmin(np.linalg.norm(np.asarray(nodes) - pt, axis=1)))


def _near_idxs(nodes, pt, radius):
    d = np.linalg.norm(np.asarray(nodes) - pt, axis=1)
    return list(np.where(d <= radius)[0])


def _rrt_radius(n, dim=2, gamma=0.40):
    """RRT* neighbourhood radius."""
    r = gamma * (np.log(n + 1) / (n + 1)) ** (1.0 / dim)
    return max(r, STEP_SIZE * 1.5)


def _extract_path(nodes, parents, idx):
    path = []
    while idx >= 0:
        path.append(nodes[idx])
        idx = parents[idx]
    return path[::-1]


def _sample_unit(goal_bias=GOAL_BIAS):
    if np.random.rand() < goal_bias:
        return GOAL.copy()
    return np.random.rand(2)


def _propagate_costs(nodes, parents, costs, idx):
    """DFS propagation of cost updates after rewiring."""
    stack = [idx]
    while stack:
        cur = stack.pop()
        for i in range(len(parents)):
            if parents[i] == cur:
                new_c = costs[cur] + _dist(nodes[cur], nodes[i])
                if new_c + 1e-12 < costs[i]:
                    costs[i] = new_c
                    stack.append(i)


# ── Informed sampling helpers ─────────────────────────────────────

def _ellipse_consts():
    """Pre-compute rotation matrix for informed sampling ellipse."""
    diff = GOAL - START
    c_min = np.linalg.norm(diff)
    centre = (START + GOAL) / 2.0
    angle = np.arctan2(diff[1], diff[0])
    C = np.array([[np.cos(angle), -np.sin(angle)],
                   [np.sin(angle),  np.cos(angle)]])
    return c_min, centre, C, angle


def _sample_ellipse(c_best, c_min, centre, C):
    """Sample uniformly inside the informed ellipse."""
    r1 = c_best / 2.0
    r2 = np.sqrt(max(c_best ** 2 - c_min ** 2, 0.0)) / 2.0
    if r2 < 1e-9:
        r2 = 1e-9
    r = np.sqrt(np.random.rand())
    theta = 2.0 * np.pi * np.random.rand()
    x_ball = np.array([r * np.cos(theta), r * np.sin(theta)])
    x_scaled = np.array([r1 * x_ball[0], r2 * x_ball[1]])
    return centre + C @ x_scaled


# ══════════════════════════════════════════════════════════════════
# Plotting helpers
# ══════════════════════════════════════════════════════════════════

def _new_fig(title=""):
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.25, ls="--")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title:
        ax.set_title(title, fontsize=12, pad=10)
    for ox, oy, ow, oh in OBSTACLES:
        ax.add_patch(Rectangle((ox, oy), ow, oh,
                                fc=OBS_FACE, ec="black",
                                alpha=OBS_ALPHA, lw=0.8))
    return fig, ax


def _mark_sg(ax):
    ax.plot(*START, "o", color=START_CLR, ms=12, zorder=5, label="start")
    ax.plot(*GOAL,  "*", color=GOAL_CLR,  ms=16, zorder=5, label="goal")


def _draw_tree(ax, nodes, parents, color=TREE_A_CLR, lw=0.5, alpha=0.55):
    for i, p in enumerate(parents):
        if p < 0:
            continue
        ax.plot([nodes[p][0], nodes[i][0]],
                [nodes[p][1], nodes[i][1]],
                color=color, lw=lw, alpha=alpha)


def _draw_path(ax, path, color=PATH_CLR, lw=2.8):
    pts = np.asarray(path)
    ax.plot(pts[:, 0], pts[:, 1], color=color, lw=lw, zorder=4, label="path")


def _draw_ellipse(ax, c_best, angle_rad):
    c_min = _dist(START, GOAL)
    if c_best >= 1e12 or c_best < c_min:
        return
    centre = (START + GOAL) / 2.0
    w = c_best                                          # full width
    h = np.sqrt(max(c_best ** 2 - c_min ** 2, 0.0))    # full height
    ell = Ellipse(centre, width=w, height=h,
                  angle=np.degrees(angle_rad),
                  fill=False, ec=ELLIPSE_CLR, ls="--", lw=2,
                  zorder=2, label="informed ellipse")
    ax.add_patch(ell)


def _save(fig, name):
    fig.savefig(OUT_DIR / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {name}")


# ══════════════════════════════════════════════════════════════════
# RRT
# ══════════════════════════════════════════════════════════════════

def _run_rrt(*, max_iter=8000, snapshots=()):
    nodes = [START.copy()]
    parents = [-1]
    snap, snap_need = {}, set(snapshots)
    goal_idx = -1

    for _ in range(max_iter):
        x_rand = _sample_unit()
        ni = _nearest_idx(nodes, x_rand)
        x_new = _steer(nodes[ni], x_rand)
        if _pt_in_obs(x_new) or not _seg_free(nodes[ni], x_new):
            continue
        nodes.append(x_new)
        parents.append(ni)
        n = len(nodes)
        for s in list(snap_need):
            if n >= s:
                snap[s] = ([nd.copy() for nd in nodes], list(parents))
                snap_need.discard(s)
        if _dist(x_new, GOAL) < GOAL_RADIUS and _seg_free(x_new, GOAL):
            nodes.append(GOAL.copy())
            parents.append(n - 1)
            goal_idx = n
            for s in snap_need:
                snap[s] = ([nd.copy() for nd in nodes], list(parents))
            break

    return nodes, parents, goal_idx, snap


def gen_rrt_images():
    print("RRT ─────────────────────────────────────────")

    # ── anatomy ────────────────────────────────────────
    np.random.seed(42)
    anat_n, anat_p = [START.copy()], [-1]
    for _ in range(800):
        if len(anat_n) >= 30:
            break
        xr = _sample_unit(goal_bias=0)
        ni = _nearest_idx(anat_n, xr)
        xn = _steer(anat_n[ni], xr)
        if _pt_in_obs(xn) or not _seg_free(anat_n[ni], xn):
            continue
        anat_n.append(xn)
        anat_p.append(ni)
    # one valid iteration for the illustration
    while True:
        x_rand = np.random.rand(2)
        ni = _nearest_idx(anat_n, x_rand)
        x_near = anat_n[ni]
        x_new = _steer(x_near, x_rand)
        if not _pt_in_obs(x_new) and _seg_free(x_near, x_new):
            break

    fig, ax = _new_fig("RRT — one iteration anatomy")
    _draw_tree(ax, anat_n, anat_p)
    ax.plot([x_near[0], x_rand[0]], [x_near[1], x_rand[1]],
            ls="--", color=XRAND_CLR, lw=1, alpha=0.5, zorder=2)
    ax.plot([x_near[0], x_new[0]], [x_near[1], x_new[1]],
            color=XNEW_CLR, lw=2.5, zorder=3)
    ax.plot(*x_rand, "x", color=XRAND_CLR, ms=14, mew=3, zorder=6,
            label=r"$x_{\mathrm{rand}}$  (×)")
    ax.plot(*x_near, "s", color=XNEAR_CLR, ms=10, zorder=6,
            label=r"$x_{\mathrm{near}}$  (■)")
    ax.plot(*x_new, "D", color=XNEW_CLR, ms=10, zorder=6,
            label=r"$x_{\mathrm{new}}$  (◆)")
    _mark_sg(ax)
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "01_rrt_anatomy.png")

    # ── tree snapshots + final ─────────────────────────
    np.random.seed(42)
    nodes, parents, gi, snaps = _run_rrt(snapshots=(100, 300))

    for cnt, fn in [(100, "02_rrt_snapshot_01_n100.png"),
                    (300, "02_rrt_snapshot_02_n300.png")]:
        sn, sp = snaps.get(cnt, (nodes, parents))
        fig, ax = _new_fig(f"RRT — ~{cnt} nodes  (n={len(sn)})")
        _draw_tree(ax, sn, sp)
        _mark_sg(ax)
        ax.legend(loc="upper left", fontsize=9)
        _save(fig, fn)

    fig, ax = _new_fig(f"RRT — final tree  (n={len(nodes)})")
    _draw_tree(ax, nodes, parents)
    if gi >= 0:
        _draw_path(ax, _extract_path(nodes, parents, gi))
    _mark_sg(ax)
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "03_rrt_final.png")


# ══════════════════════════════════════════════════════════════════
# RRT-Connect
# ══════════════════════════════════════════════════════════════════

def _run_rrt_connect(max_iter=2000):
    """Two trees, alternating extend + aggressive connect."""
    na, pa = [START.copy()], [-1]
    nb, pb = [GOAL.copy()],  [-1]
    max_connect_steps = int(2.0 / STEP_SIZE)

    for _ in range(max_iter):
        # extend the active tree (na)
        xr = _sample_unit(goal_bias=0)
        ni = _nearest_idx(na, xr)
        xn = _steer(na[ni], xr)
        if _pt_in_obs(xn) or not _seg_free(na[ni], xn):
            na, pa, nb, pb = nb, pb, na, pa
            continue
        na.append(xn)
        pa.append(ni)

        # connect nb toward xn
        for _ in range(max_connect_steps):
            nib = _nearest_idx(nb, xn)
            xs = _steer(nb[nib], xn)
            if _pt_in_obs(xs) or not _seg_free(nb[nib], xs):
                break
            nb.append(xs)
            pb.append(nib)
            if _dist(xs, xn) < 1e-6:
                ca, cb = len(na) - 1, len(nb) - 1
                pa_ = _extract_path(na, pa, ca)
                pb_ = _extract_path(nb, pb, cb)
                if np.allclose(na[0], START):
                    return na, pa, nb, pb, pa_ + list(reversed(pb_[:-1]))
                else:
                    return nb, pb, na, pa, pb_ + list(reversed(pa_[:-1]))

        na, pa, nb, pb = nb, pb, na, pa

    # no connection
    if np.allclose(na[0], START):
        return na, pa, nb, pb, None
    return nb, pb, na, pa, None


def gen_rrt_connect_images():
    print("RRT-Connect ────────────────────────────────")

    # ── anatomy ────────────────────────────────────────
    np.random.seed(200)
    an_a, ap_a = [START.copy()], [-1]
    an_b, ap_b = [GOAL.copy()],  [-1]
    for _ in range(500):
        if len(an_a) >= 20:
            break
        xr = np.random.rand(2)
        ni = _nearest_idx(an_a, xr)
        xn = _steer(an_a[ni], xr)
        if not _pt_in_obs(xn) and _seg_free(an_a[ni], xn):
            an_a.append(xn); ap_a.append(ni)
    for _ in range(500):
        if len(an_b) >= 15:
            break
        xr = np.random.rand(2)
        ni = _nearest_idx(an_b, xr)
        xn = _steer(an_b[ni], xr)
        if not _pt_in_obs(xn) and _seg_free(an_b[ni], xn):
            an_b.append(xn); ap_b.append(ni)
    while True:
        x_rand = np.random.rand(2)
        ni = _nearest_idx(an_a, x_rand)
        x_near = an_a[ni]
        x_new = _steer(x_near, x_rand)
        if not _pt_in_obs(x_new) and _seg_free(x_near, x_new):
            break

    fig, ax = _new_fig("RRT-Connect — one iteration anatomy (extend)")
    _draw_tree(ax, an_a, ap_a, color=TREE_A_CLR)
    _draw_tree(ax, an_b, ap_b, color=TREE_B_CLR)
    ax.plot([x_near[0], x_rand[0]], [x_near[1], x_rand[1]],
            ls="--", color=XRAND_CLR, lw=1, alpha=0.5)
    ax.plot([x_near[0], x_new[0]], [x_near[1], x_new[1]],
            color=XNEW_CLR, lw=2.5, zorder=3)
    ax.plot(*x_rand, "x", color=XRAND_CLR, ms=14, mew=3, zorder=6,
            label=r"$x_{\mathrm{rand}}$  (×)")
    ax.plot(*x_near, "s", color=XNEAR_CLR, ms=10, zorder=6,
            label=r"$x_{\mathrm{near}}$  (■)")
    ax.plot(*x_new, "D", color=XNEW_CLR, ms=10, zorder=6,
            label=r"$x_{\mathrm{new}}$  (◆)")
    _mark_sg(ax)
    ax.plot([], [], color=TREE_A_CLR, lw=2, label="Tree A (start)")
    ax.plot([], [], color=TREE_B_CLR, lw=2, label="Tree B (goal)")
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "11_rrt_connect_anatomy.png")

    # ── final ──────────────────────────────────────────
    np.random.seed(200)
    na, pa, nb, pb, full_path = _run_rrt_connect()

    fig, ax = _new_fig(f"RRT-Connect — final  (n_a={len(na)}, n_b={len(nb)})")
    _draw_tree(ax, na, pa, color=TREE_A_CLR)
    _draw_tree(ax, nb, pb, color=TREE_B_CLR)
    if full_path is not None:
        _draw_path(ax, full_path)
    _mark_sg(ax)
    ax.plot([], [], color=TREE_A_CLR, lw=2, label="Tree A (start)")
    ax.plot([], [], color=TREE_B_CLR, lw=2, label="Tree B (goal)")
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "13_rrt_connect_final.png")


# ══════════════════════════════════════════════════════════════════
# RRT*
# ══════════════════════════════════════════════════════════════════

def _run_rrt_star(*, max_iter=8000, snapshots=(), stop_first=True):
    nodes = [START.copy()]
    parents = [-1]
    costs = [0.0]
    goal_idx = -1
    snap, snap_need = {}, set(snapshots)

    for _ in range(max_iter):
        x_rand = _sample_unit()
        ni = _nearest_idx(nodes, x_rand)
        x_new = _steer(nodes[ni], x_rand)
        if _pt_in_obs(x_new) or not _seg_free(nodes[ni], x_new):
            continue

        n = len(nodes)
        r = _rrt_radius(n)
        nbrs = _near_idxs(nodes, x_new, r)

        best_p, best_c = ni, costs[ni] + _dist(nodes[ni], x_new)
        for j in nbrs:
            c = costs[j] + _dist(nodes[j], x_new)
            if c < best_c and _seg_free(nodes[j], x_new):
                best_p, best_c = j, c

        nodes.append(x_new)
        parents.append(best_p)
        costs.append(best_c)
        new_i = n

        for j in nbrs:
            c = best_c + _dist(x_new, nodes[j])
            if c < costs[j] and _seg_free(x_new, nodes[j]):
                parents[j] = new_i
                costs[j] = c

        nn = len(nodes)
        for s in list(snap_need):
            if nn >= s:
                snap[s] = ([nd.copy() for nd in nodes], list(parents))
                snap_need.discard(s)

        if _dist(x_new, GOAL) < GOAL_RADIUS and _seg_free(x_new, GOAL):
            gc = best_c + _dist(x_new, GOAL)
            if goal_idx < 0:
                nodes.append(GOAL.copy())
                parents.append(new_i)
                costs.append(gc)
                goal_idx = len(nodes) - 1
                if stop_first:
                    for s in snap_need:
                        snap[s] = ([nd.copy() for nd in nodes], list(parents))
                    break
            elif gc < costs[goal_idx]:
                parents[goal_idx] = new_i
                costs[goal_idx] = gc

    return nodes, parents, costs, goal_idx, snap


def gen_rrt_star_images():
    print("RRT* ────────────────────────────────────────")

    # ── anatomy ────────────────────────────────────────
    np.random.seed(42)
    an, ap, ac = [START.copy()], [-1], [0.0]
    for _ in range(800):
        if len(an) >= 40:
            break
        xr = _sample_unit(goal_bias=0)
        ni = _nearest_idx(an, xr)
        xn = _steer(an[ni], xr)
        if _pt_in_obs(xn) or not _seg_free(an[ni], xn):
            continue
        n = len(an)
        r = _rrt_radius(n)
        nbrs = _near_idxs(an, xn, r)
        bp, bc = ni, ac[ni] + _dist(an[ni], xn)
        for j in nbrs:
            c = ac[j] + _dist(an[j], xn)
            if c < bc and _seg_free(an[j], xn):
                bp, bc = j, c
        an.append(xn); ap.append(bp); ac.append(bc)
        new_i = n
        for j in nbrs:
            c = bc + _dist(xn, an[j])
            if c < ac[j] and _seg_free(xn, an[j]):
                ap[j] = new_i; ac[j] = c

    # one more iteration with visible neighbourhood
    for _ in range(200):
        x_rand = np.random.rand(2)
        ni = _nearest_idx(an, x_rand)
        x_near = an[ni]
        x_new = _steer(x_near, x_rand)
        if not _pt_in_obs(x_new) and _seg_free(x_near, x_new):
            r = _rrt_radius(len(an))
            nbrs = _near_idxs(an, x_new, r)
            if len(nbrs) >= 2:
                break

    fig, ax = _new_fig("RRT* — one iteration anatomy")
    _draw_tree(ax, an, ap)
    circ = plt.Circle(x_new, r, fill=False, ec=NEIGH_CLR, ls="--", lw=1.5,
                       zorder=3, label="neighbourhood")
    ax.add_patch(circ)
    for j in nbrs:
        ax.plot([x_new[0], an[j][0]], [x_new[1], an[j][1]],
                color=NEIGH_CLR, lw=1, ls=":", alpha=0.7, zorder=2)
    ax.plot([x_near[0], x_rand[0]], [x_near[1], x_rand[1]],
            ls="--", color=XRAND_CLR, lw=1, alpha=0.5)
    ax.plot([x_near[0], x_new[0]], [x_near[1], x_new[1]],
            color=XNEW_CLR, lw=2.5, zorder=3)
    ax.plot(*x_rand, "x", color=XRAND_CLR, ms=14, mew=3, zorder=6,
            label=r"$x_{\mathrm{rand}}$  (×)")
    ax.plot(*x_near, "s", color=XNEAR_CLR, ms=10, zorder=6,
            label=r"$x_{\mathrm{near}}$  (■)")
    ax.plot(*x_new, "D", color=XNEW_CLR, ms=10, zorder=6,
            label=r"$x_{\mathrm{new}}$  (◆)")
    _mark_sg(ax)
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "21_rrt_star_anatomy.png")

    # ── snapshot + final ───────────────────────────────
    np.random.seed(42)
    nodes, parents, costs, gi, snaps = _run_rrt_star(snapshots=(150,))

    if 150 in snaps:
        sn, sp = snaps[150]
        fig, ax = _new_fig(f"RRT* — ~150 nodes  (n={len(sn)})")
        _draw_tree(ax, sn, sp)
        _mark_sg(ax)
        ax.legend(loc="upper left", fontsize=9)
        _save(fig, "22_rrt_star_snapshot_01_n150.png")

    fig, ax = _new_fig(f"RRT* — final tree  (n={len(nodes)})")
    _draw_tree(ax, nodes, parents)
    if gi >= 0:
        _draw_path(ax, _extract_path(nodes, parents, gi))
    _mark_sg(ax)
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "23_rrt_star_final.png")


# ══════════════════════════════════════════════════════════════════
# Informed RRT*
# ══════════════════════════════════════════════════════════════════

def _run_informed_rrt_star(*, max_nodes=2500, max_iter=40000, snapshots=()):
    c_min, centre, C, _angle = _ellipse_consts()
    nodes = [START.copy()]
    parents = [-1]
    costs = [0.0]
    goal_idx = -1
    c_best = float("inf")
    snap, snap_need = {}, set(snapshots)

    for _ in range(max_iter):
        if len(nodes) >= max_nodes:
            break

        if c_best < float("inf"):
            if np.random.rand() < 0.05:
                x_rand = GOAL.copy()
            else:
                x_rand = _sample_ellipse(c_best, c_min, centre, C)
                x_rand = np.clip(x_rand, 0, 1)
        else:
            x_rand = _sample_unit()

        ni = _nearest_idx(nodes, x_rand)
        x_new = _steer(nodes[ni], x_rand)
        if _pt_in_obs(x_new) or not _seg_free(nodes[ni], x_new):
            continue

        n = len(nodes)
        r = _rrt_radius(n)
        nbrs = _near_idxs(nodes, x_new, r)

        bp, bc = ni, costs[ni] + _dist(nodes[ni], x_new)
        for j in nbrs:
            c = costs[j] + _dist(nodes[j], x_new)
            if c < bc and _seg_free(nodes[j], x_new):
                bp, bc = j, c

        nodes.append(x_new)
        parents.append(bp)
        costs.append(bc)
        new_i = n

        for j in nbrs:
            c = bc + _dist(x_new, nodes[j])
            if c < costs[j] and _seg_free(x_new, nodes[j]):
                parents[j] = new_i
                costs[j] = c
                _propagate_costs(nodes, parents, costs, j)

        # update c_best if goal cost improved via rewiring
        if goal_idx >= 0 and costs[goal_idx] < c_best:
            c_best = costs[goal_idx]

        if _dist(x_new, GOAL) < GOAL_RADIUS and _seg_free(x_new, GOAL):
            gc = bc + _dist(x_new, GOAL)
            if goal_idx < 0:
                nodes.append(GOAL.copy())
                parents.append(new_i)
                costs.append(gc)
                goal_idx = len(nodes) - 1
                c_best = gc
            elif gc < costs[goal_idx]:
                parents[goal_idx] = new_i
                costs[goal_idx] = gc
                c_best = gc

        nn = len(nodes)
        for s in list(snap_need):
            if nn >= s:
                snap[s] = ([nd.copy() for nd in nodes], list(parents), c_best)
                snap_need.discard(s)

    for s in snap_need:
        snap[s] = ([nd.copy() for nd in nodes], list(parents), c_best)

    return nodes, parents, costs, goal_idx, c_best, snap


def gen_informed_rrt_star_images():
    print("Informed RRT* ──────────────────────────────")
    c_min, centre, C, angle = _ellipse_consts()

    # ── full run ───────────────────────────────────────
    np.random.seed(42)
    nodes, parents, costs, gi, cb, snaps = _run_informed_rrt_star(
        max_nodes=2500, snapshots=(250, 900, 2000))

    # ── anatomy (separate small run to get solution + illustrate one step)
    np.random.seed(42)
    an, ap, ac = [START.copy()], [-1], [0.0]
    cb_a, gi_a = float("inf"), -1
    for _ in range(25000):
        # stop once we have a solution AND enough nodes
        if cb_a < float("inf") and len(an) >= 60:
            break
        if len(an) >= 500:
            break
        if cb_a < float("inf"):
            xr = _sample_ellipse(cb_a, c_min, centre, C)
            xr = np.clip(xr, 0, 1)
        else:
            xr = _sample_unit()
        ni = _nearest_idx(an, xr)
        xn = _steer(an[ni], xr)
        if _pt_in_obs(xn) or not _seg_free(an[ni], xn):
            continue
        n = len(an)
        r = _rrt_radius(n)
        nbrs = _near_idxs(an, xn, r)
        bp, bc = ni, ac[ni] + _dist(an[ni], xn)
        for j in nbrs:
            c = ac[j] + _dist(an[j], xn)
            if c < bc and _seg_free(an[j], xn):
                bp, bc = j, c
        an.append(xn); ap.append(bp); ac.append(bc)
        new_i = n
        for j in nbrs:
            c = bc + _dist(xn, an[j])
            if c < ac[j] and _seg_free(xn, an[j]):
                ap[j] = new_i; ac[j] = c
        if _dist(xn, GOAL) < GOAL_RADIUS and _seg_free(xn, GOAL):
            gc = bc + _dist(xn, GOAL)
            if gi_a < 0:
                an.append(GOAL.copy()); ap.append(new_i); ac.append(gc)
                gi_a = len(an) - 1; cb_a = gc
            elif gc < ac[gi_a]:
                ap[gi_a] = new_i; ac[gi_a] = gc; cb_a = gc

    # one more iteration with visible neighbourhood
    for _ in range(300):
        if cb_a < float("inf"):
            x_rand = _sample_ellipse(cb_a, c_min, centre, C)
            x_rand = np.clip(x_rand, 0, 1)
        else:
            x_rand = np.random.rand(2)
        ni = _nearest_idx(an, x_rand)
        x_near = an[ni]
        x_new = _steer(x_near, x_rand)
        if not _pt_in_obs(x_new) and _seg_free(x_near, x_new):
            r = _rrt_radius(len(an))
            nbrs = _near_idxs(an, x_new, r)
            if len(nbrs) >= 2:
                break

    fig, ax = _new_fig("Informed RRT* — one iteration anatomy")
    _draw_tree(ax, an, ap)
    _draw_ellipse(ax, cb_a, angle)
    circ = plt.Circle(x_new, r, fill=False, ec=NEIGH_CLR, ls="--", lw=1.5,
                       zorder=3, label="neighbourhood")
    ax.add_patch(circ)
    for j in nbrs:
        ax.plot([x_new[0], an[j][0]], [x_new[1], an[j][1]],
                color=NEIGH_CLR, lw=1, ls=":", alpha=0.7)
    ax.plot([x_near[0], x_rand[0]], [x_near[1], x_rand[1]],
            ls="--", color=XRAND_CLR, lw=1, alpha=0.5)
    ax.plot([x_near[0], x_new[0]], [x_near[1], x_new[1]],
            color=XNEW_CLR, lw=2.5, zorder=3)
    ax.plot(*x_rand, "x", color=XRAND_CLR, ms=14, mew=3, zorder=6,
            label=r"$x_{\mathrm{rand}}$  (×)")
    ax.plot(*x_near, "s", color=XNEAR_CLR, ms=10, zorder=6,
            label=r"$x_{\mathrm{near}}$  (■)")
    ax.plot(*x_new, "D", color=XNEW_CLR, ms=10, zorder=6,
            label=r"$x_{\mathrm{new}}$  (◆)")
    _mark_sg(ax)
    ax.legend(loc="upper left", fontsize=8)
    _save(fig, "31_informed_rrt_star_anatomy.png")

    # ── snapshots ──────────────────────────────────────
    for cnt, fn in [(250,  "32_informed_rrt_star_snapshot_01_n250.png"),
                    (900,  "32_informed_rrt_star_snapshot_02_n900.png"),
                    (2000, "32_informed_rrt_star_snapshot_03_n2000.png")]:
        sn, sp, cb_s = snaps.get(cnt, (nodes, parents, cb))
        fig, ax = _new_fig(f"Informed RRT* — ~{cnt} nodes  (n={len(sn)})")
        _draw_tree(ax, sn, sp)
        _draw_ellipse(ax, cb_s, angle)
        _mark_sg(ax)
        ax.legend(loc="upper left", fontsize=9)
        _save(fig, fn)

    # ── final ──────────────────────────────────────────
    fig, ax = _new_fig(f"Informed RRT* — final  (n={len(nodes)}, "
                        f"cost={cb:.3f})")
    _draw_tree(ax, nodes, parents)
    _draw_ellipse(ax, cb, angle)
    if gi >= 0:
        _draw_path(ax, _extract_path(nodes, parents, gi))
    _mark_sg(ax)
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "33_informed_rrt_star_final.png")


# ══════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    gen_rrt_images()
    gen_rrt_connect_images()
    gen_rrt_star_images()
    gen_informed_rrt_star_images()
    print("\nDone — all images saved to", OUT_DIR)
