#!/usr/bin/env python3
"""Generate potential-field method demonstration images.

Illustrates:
  1. Attractive potential (quadratic bowl)
  2. Repulsive potential around one obstacle
  3. Total potential surface (attractive + repulsive, 2 obstacles)
  4. Negative-gradient vector field  F(q) = -∇U(q)
  5. Gradient-descent path on contour plot
  6. Local-minimum trap (key weakness)
  7. Wavefront / brushfire grid propagation

Output: img1–img7 PNG files in the same directory as this script.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from pathlib import Path
from collections import deque

# ── Output directory ───────────────────────────────────────────
OUT = Path(__file__).resolve().parent


# ══════════════════════════════════════════════════════════════
#  Potential helpers
# ══════════════════════════════════════════════════════════════

def attractive_potential(X, Y, q_goal, xi=1.0):
    """U_att(q) = 0.5 * xi * ||q - q_goal||^2"""
    return 0.5 * xi * ((X - q_goal[0]) ** 2 + (Y - q_goal[1]) ** 2)


def repulsive_potential_single(X, Y, obs_center, obs_radius, eta=1.0, Q_star=2.0):
    """U_rep for one circular obstacle."""
    d = np.sqrt((X - obs_center[0]) ** 2 + (Y - obs_center[1]) ** 2) - obs_radius
    d = np.maximum(d, 1e-4)
    U = np.where(d <= Q_star, 0.5 * eta * (1.0 / d - 1.0 / Q_star) ** 2, 0.0)
    # inside obstacle → very high
    inside = np.sqrt((X - obs_center[0]) ** 2 + (Y - obs_center[1]) ** 2) < obs_radius
    U[inside] = np.nan
    return U


def total_potential(X, Y, q_goal, obstacles, xi=1.0, eta=1.0, Q_star=2.0):
    U = attractive_potential(X, Y, q_goal, xi)
    for cx, cy, r in obstacles:
        U += repulsive_potential_single(X, Y, (cx, cy), r, eta, Q_star)
    return U


def numerical_gradient(U, dx, dy):
    """Return (dU/dx, dU/dy) via central differences."""
    Uy, Ux = np.gradient(U, dy, dx)
    return Ux, Uy


def gradient_descent(q_start, q_goal, obstacles, xi=1.0, eta=1.0,
                     Q_star=2.0, alpha=0.05, max_iter=3000, tol=0.1):
    """Run gradient descent on potential field, return path as (N,2) array."""
    path = [np.array(q_start, dtype=float)]
    q = path[0].copy()
    for _ in range(max_iter):
        if np.linalg.norm(q - q_goal) < tol:
            break
        # attractive gradient
        g_att = xi * (q - np.array(q_goal))
        # repulsive gradient (analytical)
        g_rep = np.zeros(2)
        for cx, cy, r in obstacles:
            diff = q - np.array([cx, cy])
            dist_center = np.linalg.norm(diff)
            d = dist_center - r
            if d < 1e-4:
                d = 1e-4
            if d <= Q_star:
                mag = -eta * (1.0 / d - 1.0 / Q_star) / (d ** 2)
                direction = diff / dist_center
                g_rep += mag * direction
        grad = g_att + g_rep
        q = q - alpha * grad
        path.append(q.copy())
    return np.array(path)


# ══════════════════════════════════════════════════════════════
#  Image 1 — Attractive potential (3-D bowl)
# ══════════════════════════════════════════════════════════════

def img1():
    print("  [1/7] Attractive potential …")
    q_goal = (5.0, 5.0)
    xi = 1.0
    x = np.linspace(0, 10, 200)
    y = np.linspace(0, 10, 200)
    X, Y = np.meshgrid(x, y)
    U = attractive_potential(X, Y, q_goal, xi)

    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(X, Y, U, cmap="viridis", alpha=0.9, edgecolor="none")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel(r"$U_{att}(q)$")
    ax.set_title(
        r"Attractive Potential: $U_{att}(q)=\frac{1}{2}\xi\,\|q-q_{goal}\|^2$"
        f"\n($\\xi={xi}$, $q_{{goal}}$=({q_goal[0]},{q_goal[1]}))",
        fontsize=12, fontweight="bold",
    )
    ax.scatter(*q_goal, 0, color="red", s=80, zorder=5, label=r"$q_{goal}$")
    ax.legend(loc="upper right")

    fig.savefig(OUT / "img1_attractive_potential.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
#  Image 2 — Repulsive potential around one obstacle
# ══════════════════════════════════════════════════════════════

def img2():
    print("  [2/7] Repulsive potential …")
    obs = (3.0, 3.0)
    r = 1.0
    eta = 1.0
    Q_star = 2.0

    x = np.linspace(0, 7, 300)
    y = np.linspace(0, 7, 300)
    X, Y = np.meshgrid(x, y)
    U = repulsive_potential_single(X, Y, obs, r, eta, Q_star)
    U_clip = np.clip(U, 0, 8)  # clip for nicer visual

    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(X, Y, U_clip, cmap="inferno", alpha=0.9, edgecolor="none")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel(r"$U_{rep}(q)$")
    ax.set_title(
        r"Repulsive Potential: $U_{rep}=\frac{1}{2}\eta"
        r"\left(\frac{1}{d}-\frac{1}{Q^*}\right)^2$  when $d\leq Q^*$"
        f"\n($\\eta={eta}$, $Q^*={Q_star}$, obstacle at ({obs[0]},{obs[1]}), r={r})",
        fontsize=11, fontweight="bold",
    )
    ax.legend(["Repulsive surface"], loc="upper right")

    fig.savefig(OUT / "img2_repulsive_potential.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
#  Image 3 — Total potential surface (2 obstacles)
# ══════════════════════════════════════════════════════════════

Q_GOAL = (8.0, 8.0)
OBSTACLES = [(3.0, 3.0, 1.0), (6.0, 4.0, 0.8)]  # (cx, cy, radius)
XI, ETA, Q_STAR = 1.0, 1.0, 2.0


def img3():
    print("  [3/7] Total potential surface …")
    x = np.linspace(0, 10, 300)
    y = np.linspace(0, 10, 300)
    X, Y = np.meshgrid(x, y)
    U = total_potential(X, Y, Q_GOAL, OBSTACLES, XI, ETA, Q_STAR)
    U_clip = np.clip(U, 0, 30)

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(X, Y, U_clip, cmap="coolwarm", alpha=0.9, edgecolor="none")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel(r"$U(q)$")
    ax.set_title(
        r"Total Potential: $U(q)=U_{att}+\sum U_{rep}$"
        f"\n$q_{{goal}}$=({Q_GOAL[0]},{Q_GOAL[1]}), "
        "obstacles at (3,3) r=1.0  &  (6,4) r=0.8",
        fontsize=12, fontweight="bold",
    )
    fig.savefig(OUT / "img3_total_potential_surface.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
#  Image 4 — Gradient (force) field quiver plot
# ══════════════════════════════════════════════════════════════

def img4():
    print("  [4/7] Gradient vector field …")
    x = np.linspace(0, 10, 40)
    y = np.linspace(0, 10, 40)
    X, Y = np.meshgrid(x, y)
    dx = x[1] - x[0]
    dy = y[1] - y[0]
    U = total_potential(X, Y, Q_GOAL, OBSTACLES, XI, ETA, Q_STAR)
    Ux, Uy = numerical_gradient(U, dx, dy)
    # Force = -grad(U)
    Fx, Fy = -Ux, -Uy

    mag = np.sqrt(Fx ** 2 + Fy ** 2)
    mag_safe = np.where(mag > 0, mag, 1.0)
    Fx_n = Fx / mag_safe
    Fy_n = Fy / mag_safe

    fig, ax = plt.subplots(figsize=(9, 8))
    q = ax.quiver(X, Y, Fx_n, Fy_n, mag, cmap="plasma", scale=30, width=0.004)
    fig.colorbar(q, ax=ax, label=r"$\|F(q)\|$")

    for cx, cy, r in OBSTACLES:
        ax.add_patch(Circle((cx, cy), r, fc="gray", ec="black", lw=1.5, zorder=3))
    ax.plot(*Q_GOAL, "r*", markersize=18, zorder=4, label=r"$q_{goal}$")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(
        r"Negative-Gradient Field: $F(q)=-\nabla U(q)$"
        "\nArrows point toward goal, away from obstacles",
        fontsize=12, fontweight="bold",
    )
    ax.legend(fontsize=11)
    ax.set_aspect("equal")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    fig.savefig(OUT / "img4_gradient_field.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
#  Image 5 — Gradient-descent path (contour + path)
# ══════════════════════════════════════════════════════════════

def img5():
    print("  [5/7] Gradient descent path …")
    q_start = (1.0, 1.0)
    path = gradient_descent(q_start, Q_GOAL, OBSTACLES, XI, ETA, Q_STAR,
                            alpha=0.05, max_iter=5000)

    x = np.linspace(0, 10, 300)
    y = np.linspace(0, 10, 300)
    X, Y = np.meshgrid(x, y)
    U = total_potential(X, Y, Q_GOAL, OBSTACLES, XI, ETA, Q_STAR)
    U_clip = np.clip(U, 0, 30)

    fig, ax = plt.subplots(figsize=(9, 8))
    cs = ax.contourf(X, Y, U_clip, levels=40, cmap="coolwarm", alpha=0.85)
    fig.colorbar(cs, ax=ax, label=r"$U(q)$")
    ax.contour(X, Y, U_clip, levels=20, colors="k", linewidths=0.3, alpha=0.4)

    for cx, cy, r in OBSTACLES:
        ax.add_patch(Circle((cx, cy), r, fc="gray", ec="black", lw=1.5, zorder=3))

    ax.plot(path[:, 0], path[:, 1], "w-", linewidth=2.2, zorder=4, label="Gradient descent path")
    ax.plot(path[:, 0], path[:, 1], "lime", linewidth=1.4, zorder=5)
    ax.plot(*q_start, "go", markersize=10, zorder=6, label=r"$q_{start}$")
    ax.plot(*Q_GOAL, "r*", markersize=18, zorder=6, label=r"$q_{goal}$")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(
        r"Gradient Descent: $q_{i+1}=q_i - \alpha\,\nabla U(q_i)$"
        f"\n$q_{{start}}$=({q_start[0]},{q_start[1]}), "
        f"$q_{{goal}}$=({Q_GOAL[0]},{Q_GOAL[1]})",
        fontsize=12, fontweight="bold",
    )
    ax.legend(fontsize=10)
    ax.set_aspect("equal")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    fig.savefig(OUT / "img5_gradient_descent_path.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
#  Image 6 — Local-minimum trap
# ══════════════════════════════════════════════════════════════

def img6():
    print("  [6/7] Local minimum trap …")
    q_start = (1.0, 5.0)
    q_goal = (9.0, 5.0)
    obs_trap = [(5.0, 5.0, 1.5)]

    path = gradient_descent(q_start, q_goal, obs_trap, xi=1.0, eta=1.5,
                            Q_star=3.0, alpha=0.03, max_iter=6000, tol=0.15)

    x = np.linspace(0, 10, 300)
    y = np.linspace(0, 10, 300)
    X, Y = np.meshgrid(x, y)
    U = total_potential(X, Y, q_goal, obs_trap, xi=1.0, eta=1.5, Q_star=3.0)
    U_clip = np.clip(U, 0, 20)

    fig, ax = plt.subplots(figsize=(10, 7))
    cs = ax.contourf(X, Y, U_clip, levels=40, cmap="coolwarm", alpha=0.85)
    fig.colorbar(cs, ax=ax, label=r"$U(q)$")
    ax.contour(X, Y, U_clip, levels=20, colors="k", linewidths=0.3, alpha=0.4)

    for cx, cy, r in obs_trap:
        ax.add_patch(Circle((cx, cy), r, fc="gray", ec="black", lw=1.5, zorder=3))

    ax.plot(path[:, 0], path[:, 1], "w-", linewidth=2.5, zorder=4)
    ax.plot(path[:, 0], path[:, 1], "lime", linewidth=1.6, zorder=5, label="Gradient descent path")
    ax.plot(*q_start, "go", markersize=12, zorder=6, label=r"$q_{start}$")
    ax.plot(*q_goal, "r*", markersize=18, zorder=6, label=r"$q_{goal}$")

    # mark stuck point
    stuck = path[-1]
    ax.plot(stuck[0], stuck[1], "yX", markersize=16, zorder=7, label="STUCK (local minimum)")
    ax.annotate(
        f"Local min!\n({stuck[0]:.1f}, {stuck[1]:.1f})",
        xy=(stuck[0], stuck[1]),
        xytext=(stuck[0] + 1.0, stuck[1] + 1.5),
        fontsize=11, fontweight="bold", color="yellow",
        arrowprops=dict(arrowstyle="->", color="yellow", lw=2),
        zorder=8,
    )

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(
        "LOCAL MINIMUM TRAP — Robot gets STUCK!\n"
        r"Obstacle directly between $q_{start}$ and $q_{goal}$"
        f" — gradient = 0 at local min",
        fontsize=12, fontweight="bold", color="darkred",
    )
    ax.legend(fontsize=10)
    ax.set_aspect("equal")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    fig.savefig(OUT / "img6_local_minimum_trap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
#  Image 7 — Wavefront / brushfire grid propagation
# ══════════════════════════════════════════════════════════════

def img7():
    print("  [7/7] Wavefront / brushfire …")
    rows, cols = 15, 20
    grid = np.zeros((rows, cols), dtype=int)

    # obstacles (value = -1)
    grid[3:6, 5:8] = -1
    grid[8:11, 10:14] = -1
    grid[2:5, 14:16] = -1

    goal = (1, 18)
    start = (13, 1)

    # BFS wavefront from goal
    wave = np.full((rows, cols), -1, dtype=int)
    wave[grid == -1] = -2  # obstacle marker
    wave[goal] = 0
    queue = deque([goal])
    while queue:
        r, c = queue.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and wave[nr, nc] == -1:
                wave[nr, nc] = wave[r, c] + 1
                queue.append((nr, nc))

    # trace shortest path from start
    path = [start]
    r, c = start
    while (r, c) != goal:
        best = None
        bval = wave[r, c]
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and 0 <= wave[nr, nc] < bval:
                bval = wave[nr, nc]
                best = (nr, nc)
        if best is None:
            break
        path.append(best)
        r, c = best

    # ── draw ──
    fig, ax = plt.subplots(figsize=(12, 7))
    display = np.where(wave >= 0, wave, np.nan)
    im = ax.imshow(display, cmap="YlGnBu_r", origin="upper", interpolation="nearest")
    fig.colorbar(im, ax=ax, label="Wavefront distance from goal")

    # obstacles in dark gray
    for r_ in range(rows):
        for c_ in range(cols):
            if grid[r_, c_] == -1:
                ax.add_patch(plt.Rectangle((c_ - 0.5, r_ - 0.5), 1, 1,
                             fc="dimgray", ec="black", lw=0.5, zorder=2))
            elif wave[r_, c_] >= 0:
                ax.text(c_, r_, str(wave[r_, c_]), ha="center", va="center",
                        fontsize=6, color="black", zorder=3)

    # path
    pr = [p[0] for p in path]
    pc = [p[1] for p in path]
    ax.plot(pc, pr, "r-o", linewidth=2.5, markersize=5, zorder=4, label="Shortest path")
    ax.plot(goal[1], goal[0], "g*", markersize=18, zorder=5, label="Goal")
    ax.plot(start[1], start[0], "bs", markersize=12, zorder=5, label="Start")

    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    ax.set_title(
        "Wavefront / Brushfire Propagation\n"
        "BFS from goal fills cells with increasing distance → trace back for shortest path",
        fontsize=12, fontweight="bold",
    )
    ax.legend(fontsize=10, loc="lower right")
    ax.set_xticks(range(cols))
    ax.set_yticks(range(rows))
    ax.grid(True, alpha=0.3)

    fig.savefig(OUT / "img7_wavefront_brushfire.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
#  main
# ══════════════════════════════════════════════════════════════

def main():
    print("Generating potential-field demo images …")
    img1()
    img2()
    img3()
    img4()
    img5()
    img6()
    img7()
    print(f"All images saved to {OUT}")


if __name__ == "__main__":
    main()
