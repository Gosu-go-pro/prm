#!/usr/bin/env python3
"""Generate GVD gap sensitivity visualization (3 panels).

Demonstrates how GVD branches behave with different obstacle gaps:
  - Gap > 0  →  GVD branch exists between obstacles
  - Gap = 0  →  GVD branch disappears (no free space between them)

Output: gvd_gap_three_cases.png
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from scipy.ndimage import distance_transform_edt, binary_dilation
from pathlib import Path

# ── Output directory ───────────────────────────────────────────
OUT_DIR = Path(__file__).resolve().parent

# ── Workspace bounds ───────────────────────────────────────────
X_MIN, X_MAX = 0.0, 7.5
Y_MIN, Y_MAX = 0.0, 5.0
RES = 0.01  # grid cell size (world units)

# ── Rectangle obstacle (bottom-left corner, width, height) ────
RECT_X, RECT_Y = 2.0, 2.0
RECT_W, RECT_H = 2.2, 1.6
RECT_RIGHT = RECT_X + RECT_W                # 4.2

# ── Circle obstacle ───────────────────────────────────────────
CIRCLE_R  = 0.9
CIRCLE_CY = RECT_Y + RECT_H / 2             # 2.8 (vertically centred on rect)

# ── Three gap cases ───────────────────────────────────────────
# circle_center_x = RECT_RIGHT + CIRCLE_R + gap
CASES = [
    ("Gap ≈ 0.6 units",         0.60),
    ("Gap ≈ 0.1 units",         0.10),
    ("Gap = 0 (touching)",      0.00),
]

# ── Colours ────────────────────────────────────────────────────
OBS_FACE  = "#c0c0c0"
OBS_EDGE  = "black"
GVD_COLOR = (0.84, 0.15, 0.16) # red
GAP_COLOR = "#1f77b4"           # blue


# ── helpers ────────────────────────────────────────────────────

def _circle_cx(gap):
    """Circle centre-x that yields the given horizontal gap."""
    return RECT_RIGHT + CIRCLE_R + gap


def _build_label_grid(cx):
    """Create labelled obstacle grid.

    Labels: 0 = free, 1 = boundary, 2 = rectangle, 3 = circle.
    """
    nx = int(round((X_MAX - X_MIN) / RES))
    ny = int(round((Y_MAX - Y_MIN) / RES))
    xs = np.linspace(X_MIN, X_MAX, nx)
    ys = np.linspace(Y_MIN, Y_MAX, ny)
    XX, YY = np.meshgrid(xs, ys)

    grid = np.zeros((ny, nx), dtype=np.int32)

    # 1 — workspace boundary (thin border)
    bw = 2
    grid[:bw, :] = 1
    grid[-bw:, :] = 1
    grid[:, :bw] = 1
    grid[:, -bw:] = 1

    # 2 — rectangle
    rect_mask = (
        (XX >= RECT_X) & (XX <= RECT_X + RECT_W) &
        (YY >= RECT_Y) & (YY <= RECT_Y + RECT_H)
    )
    grid[rect_mask] = 2

    # 3 — circle
    circle_mask = (XX - cx) ** 2 + (YY - CIRCLE_CY) ** 2 <= CIRCLE_R ** 2
    grid[circle_mask] = 3

    return grid, xs, ys


def _compute_gvd(grid):
    """GVD = free-space boundary between Voronoi regions of different obstacles."""
    free = grid == 0
    obs_ids = np.unique(grid[grid > 0])
    if len(obs_ids) < 2:
        return np.zeros_like(free)

    # Distance from every cell to each obstacle label
    dists = np.empty((len(obs_ids),) + grid.shape)
    for k, oid in enumerate(obs_ids):
        dists[k] = distance_transform_edt(grid != oid)

    # Nearest obstacle label for each cell
    nearest = np.argmin(dists, axis=0)

    # GVD: free cells whose 4-neighbour has a different nearest obstacle
    ny, nx = grid.shape
    gvd = np.zeros((ny, nx), dtype=bool)
    gvd[:-1, :] |= nearest[:-1, :] != nearest[1:, :]
    gvd[1:, :]  |= nearest[1:, :] != nearest[:-1, :]
    gvd[:, :-1] |= nearest[:, :-1] != nearest[:, 1:]
    gvd[:, 1:]  |= nearest[:, 1:] != nearest[:, :-1]
    gvd &= free

    # Thicken for visibility
    gvd = binary_dilation(gvd, iterations=2) & free
    return gvd


def _draw_panel(ax, gap, xs, ys, gvd):
    """Draw obstacles, GVD overlay, and gap annotation on one Axes."""
    cx = _circle_cx(gap)

    # Obstacles
    ax.add_patch(Rectangle(
        (RECT_X, RECT_Y), RECT_W, RECT_H,
        fc=OBS_FACE, ec=OBS_EDGE, lw=1.4, zorder=2,
    ))
    ax.add_patch(Circle(
        (cx, CIRCLE_CY), CIRCLE_R,
        fc=OBS_FACE, ec=OBS_EDGE, lw=1.4, zorder=2,
    ))

    # GVD as semi-transparent image overlay
    overlay = np.zeros((*gvd.shape, 4), dtype=np.float32)
    overlay[gvd] = [*GVD_COLOR, 0.85]
    ax.imshow(
        overlay,
        extent=[xs[0], xs[-1], ys[0], ys[-1]],
        origin="lower", aspect="equal",
        interpolation="nearest", zorder=3,
    )

    # Gap annotation (double-headed arrow for gap > 0)
    arr_y = CIRCLE_CY
    left_x = RECT_RIGHT
    right_x = cx - CIRCLE_R
    if gap >= 0.05:
        ax.annotate(
            "", xy=(right_x, arr_y), xytext=(left_x, arr_y),
            arrowprops=dict(arrowstyle="<->", color=GAP_COLOR, lw=1.8),
            zorder=4,
        )
        ax.text(
            (left_x + right_x) / 2, arr_y + 0.22,
            f"gap = {gap:.1f}",
            ha="center", va="bottom", fontsize=10,
            color=GAP_COLOR, fontweight="bold", zorder=4,
        )

    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.15)


# ── main ───────────────────────────────────────────────────────

def main():
    print("Generating GVD gap sensitivity visualization …")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    for idx, (title, gap) in enumerate(CASES):
        cx = _circle_cx(gap)
        print(f"  [{idx + 1}/3] {title}  (circle cx = {cx:.2f})")

        grid, xs, ys = _build_label_grid(cx)
        gvd = _compute_gvd(grid)

        _draw_panel(axes[idx], gap, xs, ys, gvd)
        axes[idx].set_title(title, fontsize=13, fontweight="bold")

    fig.suptitle(
        "GVD Branch Sensitivity to Obstacle Gap",
        fontsize=15, fontweight="bold", y=0.98,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])

    out_path = OUT_DIR / "gvd_gap_three_cases.png"
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out_path}")


if __name__ == "__main__":
    main()
