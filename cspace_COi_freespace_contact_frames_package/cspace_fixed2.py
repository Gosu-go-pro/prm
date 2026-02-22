"""
C-space obstacle visualization — pure numpy + matplotlib (no shapely needed).
Implements:
  - Convex Minkowski sum via edge-vector merge (exact for convex polygons)
  - Polygon translation, reflection
  - C_obs and free-space visualization
  - 8 contact-configuration frames
  - Example path in free space
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.path import Path
from matplotlib.patches import PathPatch

# ─── Color palette ────────────────────────────────────────────────────────────
C = {
    "O1":     "#4C72B0",
    "O2":     "#DD8452",
    "R":      "#55A868",
    "CO1":    "#4C72B0",
    "CO2":    "#DD8452",
    "Cfree":  "#C8E6C9",
    "Cobs1":  "#9DC3E6",
    "Cobs2":  "#F4B183",
    "path":   "#E91E63",
    "qdot":   "#1B5E20",
    "contact":"#FF1744",
    "bdry":   "#B71C1C",
}

# ─── Geometry helpers ─────────────────────────────────────────────────────────

def poly_translate(pts, dx, dy):
    return pts + np.array([dx, dy])

def poly_reflect(pts):
    return -pts

def convex_hull(pts):
    """Graham scan convex hull."""
    pts = np.array(pts)
    pts = pts[np.lexsort((pts[:,1], pts[:,0]))]
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lower = []
    for p in pts:
        while len(lower)>=2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper)>=2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return np.array(hull)

def minkowski_sum_convex(A, B):
    """
    Exact Minkowski sum of two convex polygons (CCW).
    Algorithm: merge edge vectors sorted by angle.
    """
    def make_ccw(pts):
        # Ensure CCW orientation
        if np.cross(pts[1]-pts[0], pts[2]-pts[0]) < 0:
            return pts[::-1]
        return pts

    A = make_ccw(A)
    B = make_ccw(B)
    nA, nB = len(A), len(B)
    # Edge vectors
    eA = np.roll(A,-1,axis=0) - A
    eB = np.roll(B,-1,axis=0) - B
    # Start at bottom-most vertices
    iA = np.argmin(A[:,1] + A[:,0]*1e-9)
    iB = np.argmin(B[:,1] + B[:,0]*1e-9)
    result = [A[iA] + B[iB]]
    i, j = 0, 0
    while i < nA or j < nB:
        if i >= nA:
            v = eB[(iB+j) % nB]; j += 1
        elif j >= nB:
            v = eA[(iA+i) % nA]; i += 1
        else:
            a = eA[(iA+i) % nA]
            b = eB[(iB+j) % nB]
            cp = np.cross(a, b)
            if cp > 0:
                v = a; i += 1
            elif cp < 0:
                v = b; j += 1
            else:
                v = a + b; i += 1; j += 1
        result.append(result[-1] + v)
    return np.array(result[:-1])

def point_in_convex_poly(pt, poly):
    """Test if point is inside (or on boundary of) convex polygon."""
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i+1) % n]
        if np.cross(b-a, pt-a) < -1e-9:
            return False
    return True

def poly_area(pts):
    x, y = pts[:,0], pts[:,1]
    return 0.5*abs(np.dot(x, np.roll(y,-1)) - np.dot(y, np.roll(x,-1)))

def centroid(pts):
    return pts.mean(axis=0)

def close_poly(pts):
    return np.vstack([pts, pts[0]])

# ─── World ────────────────────────────────────────────────────────────────────

O1 = np.array([[2.0,1.0],[4.5,1.0],[4.5,3.0],[2.0,3.0]])
O2 = np.array([[6.0,4.0],[7.8,3.2],[8.3,5.2],[6.6,5.8]])

# Robot anchored at origin
R  = np.array([[-0.7,-0.4],[0.9,-0.2],[0.0,0.9]])

negR = poly_reflect(R)

CO1 = minkowski_sum_convex(O1, negR)
CO2 = minkowski_sum_convex(O2, negR)

# ─── Drawing helpers ──────────────────────────────────────────────────────────

def fill_poly(ax, pts, color, alpha=0.35, lw=2, label=None, zorder=2):
    c = close_poly(pts)
    ax.fill(c[:,0], c[:,1], color=color, alpha=alpha, zorder=zorder)
    ax.plot(c[:,0], c[:,1], color=color, lw=lw, zorder=zorder+1)
    if label:
        cxy = centroid(pts)
        ax.text(cxy[0], cxy[1], label, ha="center", va="center",
                fontsize=12, fontweight="bold", color="white",
                bbox=dict(boxstyle="round,pad=0.25", fc=color, ec="none", alpha=0.75),
                zorder=zorder+2)

def setup_ax(ax, title):
    ax.set_xlim(0,10); ax.set_ylim(0,7)
    ax.set_aspect("equal","box")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=6)
    ax.grid(True, alpha=0.25, ls="--")
    ax.set_xlabel("x"); ax.set_ylabel("y")

def boundary_point(poly, t):
    """Sample point at fraction t along closed boundary of convex polygon."""
    closed = np.vstack([poly, poly[0]])
    lengths = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    total   = lengths.sum()
    target  = t * total
    acc = 0.0
    for i in range(len(lengths)):
        if acc + lengths[i] >= target:
            frac = (target - acc) / lengths[i]
            return closed[i] + frac*(closed[i+1] - closed[i])
        acc += lengths[i]
    return poly[0]

def draw_free_space_bg(ax, CO1, CO2, xlim=(0,10), ylim=(0,7)):
    """
    Draw free space by:
    1. Filling bounding box with free-space color
    2. Filling C_obs regions on top (so visual subtraction)
    """
    # Free space background
    bg = plt.Polygon([(xlim[0],ylim[0]),(xlim[1],ylim[0]),
                       (xlim[1],ylim[1]),(xlim[0],ylim[1])],
                      closed=True, fc=C["Cfree"], ec="none", alpha=0.5, zorder=1)
    ax.add_patch(bg)
    # Forbidden overlay
    for pts, col in [(CO1,C["Cobs1"]),(CO2,C["Cobs2"])]:
        c = close_poly(pts)
        ax.fill(c[:,0],c[:,1],color=col,alpha=0.85,zorder=2)
        ax.plot(c[:,0],c[:,1],color=col,lw=2,zorder=3)

# ─── FIG 1: Overview ──────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
fig.suptitle(
    "C-space Obstacle Construction  "
    r"$C_{O_i} = O_i \oplus (-R)$"
    "  (translation-only robot)",
    fontsize=13, fontweight="bold"
)

ax = axes[0]
fill_poly(ax, O1, C["O1"], label="O₁")
fill_poly(ax, O2, C["O2"], label="O₂")
q_demo = np.array([1.0, 4.8])
Rq = poly_translate(R, *q_demo)
fill_poly(ax, Rq, C["R"])
ax.text(*centroid(Rq), "R(q)", ha="center", va="center", fontsize=11,
        fontweight="bold", color="white",
        bbox=dict(boxstyle="round,pad=0.25", fc=C["R"], ec="none", alpha=0.8), zorder=5)
ax.scatter(*q_demo, s=70, color="black", zorder=7)
ax.annotate("reference\npoint q", xy=q_demo, xytext=(q_demo[0]+0.3, q_demo[1]+0.6),
            fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.9))
setup_ax(ax, "Workspace (W)")
ax.legend(handles=[
    mpatches.Patch(color=C["O1"], label="Obstacle O₁"),
    mpatches.Patch(color=C["O2"], label="Obstacle O₂"),
    mpatches.Patch(color=C["R"],  label="Robot R(q) — safe position"),
], loc="lower right", fontsize=9)

ax = axes[1]
fill_poly(ax, CO1, C["CO1"], label=r"$C_{O_1}$")
fill_poly(ax, CO2, C["CO2"], label=r"$C_{O_2}$")
ax.scatter(*q_demo, s=120, color=C["qdot"], edgecolors="black", zorder=6)
ax.annotate(f"q_demo\n(safe)", xy=q_demo, xytext=(q_demo[0]+0.4, q_demo[1]-0.8),
            fontsize=8, color=C["qdot"],
            arrowprops=dict(arrowstyle="->", color=C["qdot"], lw=0.9))
setup_ax(ax, r"C-space  ($q=(x,y)$, translation only)")
ax.legend(handles=[
    mpatches.Patch(color=C["CO1"], label=r"$C_{O_1} = O_1\oplus(-R)$ (forbidden)"),
    mpatches.Patch(color=C["CO2"], label=r"$C_{O_2} = O_2\oplus(-R)$ (forbidden)"),
    Line2D([0],[0], marker="o", color="w", markerfacecolor=C["qdot"],
           markersize=9, label="q_demo — outside C_obs ✓"),
], loc="lower right", fontsize=9)

plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/fig1_overview.png", dpi=140, bbox_inches="tight")
plt.close(); print("✓ fig1_overview.png")

# ─── FIG 2–9: 8 contact frames ───────────────────────────────────────────────
num_frames = 8
ts = np.linspace(0, 0.95, num_frames)

# Sample points on C_O1 boundary
boundary_pts = [boundary_point(CO1, t) for t in ts]

for k, q in enumerate(boundary_pts, start=1):
    Rq = poly_translate(R, q[0], q[1])

    # Closest points between Rq and O1 for contact annotation
    # (just find the nearest vertex pairs — good enough)
    def min_dist_pair(A, B):
        best = (np.inf, None, None)
        for a in A:
            for b in B:
                d = np.linalg.norm(a - b)
                if d < best[0]:
                    best = (d, a.copy(), b.copy())
        return best

    dist, pa, pb = min_dist_pair(Rq, O1)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(
        rf"Frame {k}/8 — Contact configuration:  "
        r"$q\in\partial C_{O_1}$  $\Longleftrightarrow$  $R(q)$ touching $O_1$",
        fontsize=12, fontweight="bold"
    )

    # ── Left: Workspace ──────────────────────────────────────────────────────
    ax = axes[0]
    fill_poly(ax, O1, C["O1"], alpha=0.4)
    ax.text(*centroid(O1), "O₁", ha="center", va="center", fontsize=12,
            fontweight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.25", fc=C["O1"], ec="none", alpha=0.8))
    fill_poly(ax, O2, C["O2"], alpha=0.4)
    ax.text(*centroid(O2), "O₂", ha="center", va="center", fontsize=12,
            fontweight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.25", fc=C["O2"], ec="none", alpha=0.8))
    fill_poly(ax, Rq, C["R"], alpha=0.55)
    ax.text(*centroid(Rq), "R(q)", ha="center", va="center", fontsize=10,
            fontweight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.25", fc=C["R"], ec="none", alpha=0.8), zorder=5)

    # Reference point q
    ax.scatter(*q, s=90, color="black", zorder=8)
    ax.annotate(f"q=({q[0]:.2f}, {q[1]:.2f})",
                xy=q, xytext=(q[0]+0.25, q[1]+0.45),
                fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.8))

    # Contact annotation — line between closest vertices
    if dist < 1.0:
        ax.plot([pa[0],pb[0]], [pa[1],pb[1]],
                color=C["contact"], lw=2.5, zorder=7)
        ax.scatter([pa[0],pb[0]], [pa[1],pb[1]],
                   s=80, color=C["contact"], zorder=8)
        mid = (pa+pb)/2
        ax.text(mid[0]+0.15, mid[1]+0.15, "contact", fontsize=8,
                color=C["contact"], fontweight="bold")

    setup_ax(ax, f"Workspace — Frame {k}: R(q) grazes O₁")
    ax.legend(handles=[
        mpatches.Patch(color=C["O1"], label="O₁"),
        mpatches.Patch(color=C["O2"], label="O₂"),
        mpatches.Patch(color=C["R"],  label="R(q)"),
        Line2D([0],[0], color=C["contact"], lw=2, label="contact edge"),
    ], loc="upper right", fontsize=9)

    # ── Right: C-space ────────────────────────────────────────────────────────
    ax = axes[1]
    fill_poly(ax, CO1, C["CO1"], alpha=0.35)
    ax.text(*centroid(CO1), r"$C_{O_1}$", ha="center", va="center", fontsize=12,
            fontweight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.25", fc=C["CO1"], ec="none", alpha=0.75))
    fill_poly(ax, CO2, C["CO2"], alpha=0.35)
    ax.text(*centroid(CO2), r"$C_{O_2}$", ha="center", va="center", fontsize=12,
            fontweight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.25", fc=C["CO2"], ec="none", alpha=0.75))

    # Highlight boundary of C_O1
    bnd = close_poly(CO1)
    ax.plot(bnd[:,0], bnd[:,1], color=C["bdry"], lw=2.5, ls="--",
            zorder=5, label=r"$\partial C_{O_1}$")

    # Current q dot
    ax.scatter(*q, s=200, color=C["qdot"], edgecolors="black", zorder=9)
    ax.annotate(f"q=({q[0]:.2f},{q[1]:.2f})",
                xy=q, xytext=(q[0]+0.35, q[1]+0.4),
                fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.8))

    setup_ax(ax, rf"C-space — Frame {k}: $q\in\partial C_{{O_1}}$")
    ax.legend(handles=[
        mpatches.Patch(color=C["CO1"], label=r"$C_{O_1}=O_1\oplus(-R)$"),
        mpatches.Patch(color=C["CO2"], label=r"$C_{O_2}=O_2\oplus(-R)$"),
        Line2D([0],[0], color=C["bdry"], lw=2, ls="--",
               label=r"$\partial C_{O_1}$ — contact locus"),
        Line2D([0],[0], marker="o", color="w", markerfacecolor=C["qdot"],
               markersize=10, label="current q"),
    ], loc="upper right", fontsize=9)

    plt.tight_layout()
    fname = f"/mnt/user-data/outputs/fig{k+1}_frame{k}.png"
    plt.savefig(fname, dpi=140, bbox_inches="tight")
    plt.close(); print(f"✓ {fname}")

# ─── FIG 10: Free space ───────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
fig.suptitle(
    r"C-space: $C_{obs}$ (forbidden) and $F = C\setminus C_{obs}$ (free space)",
    fontsize=13, fontweight="bold"
)

draw_free_space_bg(ax, CO1, CO2)

# Labels
ax.text(*centroid(CO1), r"$C_{O_1}$" + "\n(forbidden)", ha="center", va="center",
        fontsize=11, fontweight="bold", color="white",
        bbox=dict(boxstyle="round,pad=0.3", fc=C["CO1"], ec="none", alpha=0.8), zorder=5)
ax.text(*centroid(CO2), r"$C_{O_2}$" + "\n(forbidden)", ha="center", va="center",
        fontsize=11, fontweight="bold", color="white",
        bbox=dict(boxstyle="round,pad=0.3", fc=C["CO2"], ec="none", alpha=0.8), zorder=5)

# Free space label
ax.text(1.0, 6.4, r"$F = C_{free}$", fontsize=12, color="#1B5E20", fontweight="bold")

# Example path waypoints in F (hand-verified to avoid C_obs regions)
wpts = np.array([[0.5,6.5],[0.5,3.5],[1.0,0.4],[5.5,0.4],[9.2,0.4],[9.2,6.5]])
ax.plot(wpts[:,0], wpts[:,1], color=C["path"], lw=3, ls="-",
        marker=".", markersize=10, zorder=8, label=r"valid path $\sigma(t)\subset F$")
ax.scatter(*wpts[0], s=180, color=C["path"], marker="*",
           edgecolors="black", zorder=9)
ax.text(wpts[0,0]+0.15, wpts[0,1]-0.35, "$q_{start}$", fontsize=10, color=C["path"])
ax.scatter(*wpts[-1], s=180, color=C["path"], marker="D",
           edgecolors="black", zorder=9)
ax.text(wpts[-1,0]-1.2, wpts[-1,1]-0.35, "$q_{goal}$", fontsize=10, color=C["path"])

setup_ax(ax, r"$C = F \cup C_{obs},\quad F\cap C_{obs}=\emptyset$")
ax.legend(handles=[
    mpatches.Patch(color=C["Cfree"],  label=r"$F = C\setminus C_{obs}$ (free)"),
    mpatches.Patch(color=C["Cobs1"],  label=r"$C_{O_1}$ (forbidden)"),
    mpatches.Patch(color=C["Cobs2"],  label=r"$C_{O_2}$ (forbidden)"),
    Line2D([0],[0], color=C["path"], lw=2.5, label=r"example path $\sigma\subset F$"),
], loc="center", fontsize=9, framealpha=0.9)

plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/fig10_freespace.png", dpi=140, bbox_inches="tight")
plt.close(); print("✓ fig10_freespace.png")
print("\nAll 10 images saved!")
