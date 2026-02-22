"""Proper Motion Planning Demo
============================
GIF 1 – Moving Obstacle → A* in CT-space (configuration × time)
GIF 2 – Multi-Robot     → A* in Coordination Diagram (s1 × s2)

Key difference from naive "greedy wait":
  - Build the full forbidden region FIRST (offline).
  - Run A* to find a globally optimal trajectory AROUND the forbidden region.
  - The resulting path is collision-free and monotone (time/progress never goes backwards).
"""

import numpy as np
import heapq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import imageio.v2 as imageio

# =========================
# helpers
# =========================
def fig_to_rgb(fig):
    fig.canvas.draw()
    buf = fig.canvas.buffer_rgba()
    img = np.asarray(buf)
    return img[:, :, :3].copy()

# =============================================================================
# PART 1 — MOVING OBSTACLE  →  A* in CT-space
# =============================================================================
T_END   = 10.0
R_OBS   = 0.12    # obstacle radius
R_ROBOT = 0.015   # robot footprint
N_S     = 150     # grid resolution in s
N_T     = 200     # grid resolution in t

def robot_pos(s: float) -> np.ndarray:
    """Robot follows a fixed horizontal path, left→right."""
    return np.array([0.1 + 0.8*s, 0.50])

def obs_center(t: float) -> np.ndarray:
    """Obstacle sweeps vertically; crosses path near t≈5."""
    frac = np.clip((t - 2.0) / 6.0, 0.0, 1.0)   # 0→1 over t ∈ [2,8]
    return np.array([0.50, 0.10 + 0.80*frac])

def astar_ct(forbidden: np.ndarray, n_s: int, n_t: int, max_ds: int):
    """A* on CT grid. State (i_s, i_t) with time increasing by 1 each step."""
    INF = float('inf')

    def heuristic(i_s: int) -> float:
        return max(0.0, (n_s - 1 - i_s) / max_ds)

    heap = [(heuristic(0), 0.0, 0, 0)]   # (f, g, i_s, i_t)
    g_best = {(0, 0): 0.0}
    came_from = {}
    visited = set()

    while heap:
        f, g, i_s, i_t = heapq.heappop(heap)
        if (i_s, i_t) in visited:
            continue
        visited.add((i_s, i_t))

        if i_s == n_s - 1:
            path = []
            node = (i_s, i_t)
            while node in came_from:
                path.append(node)
                node = came_from[node]
            path.append((0, 0))
            return list(reversed(path))

        if i_t + 1 >= n_t:
            continue

        # Try faster moves first (larger d)
        for d in range(max_ds, -1, -1):
            ni_s = min(i_s + d, n_s - 1)
            ni_t = i_t + 1
            if forbidden[ni_s, ni_t]:
                continue
            step_cost = 1.0 + (max_ds - d) * 0.01  # small wait penalty
            ng = g + step_cost
            node = (ni_s, ni_t)
            if ng < g_best.get(node, INF):
                g_best[node] = ng
                came_from[node] = (i_s, i_t)
                heapq.heappush(heap, (ng + heuristic(ni_s), ng, ni_s, ni_t))

    return None

def run_ctspace_gif(out_path="outputs/1_moving_obstacle_ctspace.gif"):
    s_vals = np.linspace(0, 1, N_S)
    t_vals = np.linspace(0, T_END, N_T)
    dt = T_END / N_T
    ds = 1.0 / N_S
    MAX_SPEED = 1.2
    max_ds_ct = max(1, int(np.ceil(MAX_SPEED * dt / ds)))

    # build forbidden region
    robot_pts = np.stack([robot_pos(s) for s in s_vals])
    forbidden_ct = np.zeros((N_S, N_T), dtype=bool)
    for j, t in enumerate(t_vals):
        c = obs_center(t)
        d = np.linalg.norm(robot_pts - c[None, :], axis=1)
        forbidden_ct[:, j] = d < (R_OBS + R_ROBOT)

    ct_path = astar_ct(forbidden_ct, N_S, N_T, max_ds_ct)
    if ct_path is None:
        raise RuntimeError("No CT-space path found!")

    ct_s_traj = np.array([s_vals[p[0]] for p in ct_path])
    ct_t_traj = np.array([t_vals[p[1]] for p in ct_path])

    FRAMES = 160
    anim_t = np.linspace(0, T_END, FRAMES)
    ct_s_anim = np.interp(anim_t, ct_t_traj, ct_s_traj)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True, dpi=100)
    axW, axCT = axes

    # workspace
    axW.set_xlim(0, 1); axW.set_ylim(0, 1); axW.set_aspect('equal', 'box')
    axW.set_facecolor('#f0f4f8')
    axW.set_title("Workspace — Robot + Moving Obstacle", fontsize=10, weight='bold')
    axW.set_xlabel("x  [m]"); axW.set_ylabel("y  [m]")
    path_line = np.stack([robot_pos(s) for s in np.linspace(0, 1, 300)])
    axW.plot(path_line[:, 0], path_line[:, 1], '-', color='steelblue', lw=2.0, label='robot path', zorder=2)
    axW.plot(*robot_pos(0), 'go', ms=9, zorder=5, label='start')
    axW.plot(*robot_pos(1), 'r*', ms=12, zorder=5, label='goal')
    obs_patch = Circle(obs_center(0), R_OBS, fc='#f4a0a0', ec='firebrick', lw=1.5, alpha=0.80, zorder=3)
    axW.add_patch(obs_patch)
    robot_dot, = axW.plot([], [], 'o', color='steelblue', ms=8, zorder=6)
    axW.legend(fontsize=8, loc='upper right')
    txt = axW.text(0.03, 0.05, '', transform=axW.transAxes, fontsize=8,
                   bbox=dict(fc='white', alpha=0.7, boxstyle='round'))

    # CT-space
    axCT.set_xlim(0, T_END); axCT.set_ylim(0, 1)
    axCT.set_facecolor('#f0f4f8')
    axCT.set_title("CT-space: forbidden region  +  A* trajectory", fontsize=10, weight='bold')
    axCT.set_xlabel("time  t  [s]"); axCT.set_ylabel("path progress  s")
    axCT.imshow(forbidden_ct.astype(float), extent=[0, T_END, 0, 1],
                origin='lower', aspect='auto', cmap='RdYlGn_r', alpha=0.50, vmin=0, vmax=1, zorder=1)
    axCT.text(5.0, 0.50, 'FORBIDDEN\n(collision)', ha='center', va='center',
              fontsize=9, color='#8b0000', weight='bold', zorder=2)
    axCT.plot(ct_t_traj, ct_s_traj, '--', color='navy', lw=1.8, label='A* plan', zorder=3)
    ct_dot, = axCT.plot([], [], 'o', color='navy', ms=6, zorder=5)
    ct_traj_anim, = axCT.plot([], [], '-', color='royalblue', lw=2.5, alpha=0.9, zorder=4)
    axCT.legend(fontsize=8, loc='upper left')

    os.makedirs("outputs", exist_ok=True)
    with imageio.get_writer(out_path, mode='I', fps=20) as writer:
        for i in range(FRAMES):
            t_now = anim_t[i]
            s_now = ct_s_anim[i]
            p_now = robot_pos(s_now)
            c_now = obs_center(t_now)

            robot_dot.set_data([p_now[0]], [p_now[1]])
            obs_patch.center = (float(c_now[0]), float(c_now[1]))
            txt.set_text(f"t = {t_now:.2f}s\ns = {s_now:.3f}")

            mask = ct_t_traj <= t_now
            ct_traj_anim.set_data(ct_t_traj[mask], ct_s_traj[mask])
            ct_dot.set_data([t_now], [s_now])

            writer.append_data(fig_to_rgb(fig))

    plt.close(fig)

# =============================================================================
# PART 2 — MULTI-ROBOT → A* in coordination diagram
# =============================================================================
D_SAFE = 0.12
N_S1 = 180
N_S2 = 180

def r1_pos(s: float) -> np.ndarray:
    return np.array([0.1 + 0.8*s, 0.35])

def r2_pos(s: float) -> np.ndarray:
    return np.array([0.55, 0.1 + 0.8*s])

def astar_coord(forbidden: np.ndarray, n1: int, n2: int):
    INF = float('inf')
    def h(i1, i2):
        return max(n1-1-i1, n2-1-i2)
    start = (0, 0)
    goal  = (n1-1, n2-1)
    heap = [(h(0,0), 0.0, 0, 0)]
    g_best = {start: 0.0}
    came_from = {}
    visited = set()

    while heap:
        f, g, i1, i2 = heapq.heappop(heap)
        if (i1, i2) in visited:
            continue
        visited.add((i1, i2))
        if (i1, i2) == goal:
            path = []
            node = (i1, i2)
            while node in came_from:
                path.append(node); node = came_from[node]
            path.append(start)
            return list(reversed(path))

        for d1 in (0, 1, 2):
            for d2 in (0, 1, 2):
                if d1 == 0 and d2 == 0:
                    continue
                ni1 = min(i1 + d1, n1-1)
                ni2 = min(i2 + d2, n2-1)
                if forbidden[ni1, ni2]:
                    continue
                cost = max(d1, d2) + 0.04 * abs(d1 - d2)
                ng = g + cost
                node = (ni1, ni2)
                if ng < g_best.get(node, INF):
                    g_best[node] = ng
                    came_from[node] = (i1, i2)
                    heapq.heappush(heap, (ng + h(ni1,ni2), ng, ni1, ni2))
    return None

def run_coordination_gif(out_path="outputs/2_multirobot_coordination.gif"):
    s1_vals = np.linspace(0, 1, N_S1)
    s2_vals = np.linspace(0, 1, N_S2)
    r1_pts = np.stack([r1_pos(s) for s in s1_vals])
    r2_pts = np.stack([r2_pos(s) for s in s2_vals])

    forbidden = np.zeros((N_S1, N_S2), dtype=bool)
    for i in range(N_S1):
        d = np.linalg.norm(r2_pts - r1_pts[i][None, :], axis=1)
        forbidden[i, :] = d < D_SAFE

    path = astar_coord(forbidden, N_S1, N_S2)
    if path is None:
        raise RuntimeError("No coordination path found!")

    s1_traj = np.array([s1_vals[p[0]] for p in path])
    s2_traj = np.array([s2_vals[p[1]] for p in path])

    FRAMES = 160
    frame_ids = np.linspace(0, len(path)-1, FRAMES).astype(int)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True, dpi=100)
    axW, axCD = axes

    # workspace
    axW.set_xlim(0,1); axW.set_ylim(0,1); axW.set_aspect('equal', 'box')
    axW.set_facecolor('#f0f4f8')
    axW.set_title("Workspace — Two Robots (crossing paths)", fontsize=10, weight='bold')
    axW.set_xlabel("x  [m]"); axW.set_ylabel("y  [m]")

    p1_line = np.stack([r1_pos(s) for s in np.linspace(0,1,300)])
    p2_line = np.stack([r2_pos(s) for s in np.linspace(0,1,300)])
    axW.plot(p1_line[:,0], p1_line[:,1], '-', color='steelblue', lw=2.0, label='robot 1 path')
    axW.plot(p2_line[:,0], p2_line[:,1], '-', color='tomato',    lw=2.0, label='robot 2 path')
    axW.plot(*r1_pos(0), 'go', ms=9, zorder=5); axW.plot(*r1_pos(1), 'g*', ms=12, zorder=5)
    axW.plot(*r2_pos(0), 'o', color='orange', ms=9, zorder=5)
    axW.plot(*r2_pos(1), '*', color='orange', ms=12, zorder=5)
    cross_pt = (0.55, 0.35)
    axW.add_patch(Circle(cross_pt, D_SAFE, fill=True, fc='#ffe0e0', ec='firebrick', lw=1.5, ls='--', alpha=0.6, zorder=1))
    axW.text(0.55, 0.35, 'danger\nzone', ha='center', va='center', fontsize=7, color='firebrick')
    r1_dot, = axW.plot([], [], 'o', color='steelblue', ms=9, zorder=6, label='robot 1')
    r2_dot, = axW.plot([], [], 'o', color='tomato',    ms=9, zorder=6, label='robot 2')
    axW.legend(fontsize=8, loc='upper right')
    txt = axW.text(0.03, 0.05, '', transform=axW.transAxes, fontsize=8,
                   bbox=dict(fc='white', alpha=0.7, boxstyle='round'))

    # coordination diagram
    axCD.set_xlim(0,1); axCD.set_ylim(0,1)
    axCD.set_facecolor('#f0f4f8')
    axCD.set_title("Coordination diagram (s₁ × s₂) + A* schedule", fontsize=10, weight='bold')
    axCD.set_xlabel("s₁ — robot 1 progress"); axCD.set_ylabel("s₂ — robot 2 progress")

    axCD.imshow(forbidden.T.astype(float), extent=[0,1,0,1], origin='lower', aspect='auto',
                cmap='RdYlGn_r', alpha=0.50, vmin=0, vmax=1, zorder=1)
    axCD.text(0.55, 0.32, 'FORBIDDEN\n(collision)', ha='center', va='center',
              fontsize=9, color='#8b0000', weight='bold', zorder=2)

    axCD.plot([0,1],[0,1], ':', color='gray', lw=1.0, label='equal-speed ref', zorder=2)
    axCD.plot(s1_traj, s2_traj, '--', color='navy', lw=1.8, label='A* schedule', zorder=3)

    cd_dot, = axCD.plot([], [], 'o', color='navy', ms=6, zorder=5)
    cd_traj_anim, = axCD.plot([], [], '-', color='royalblue', lw=2.5, alpha=0.9, zorder=4)
    axCD.legend(fontsize=8, loc='upper left')

    os.makedirs("outputs", exist_ok=True)
    with imageio.get_writer(out_path, mode='I', fps=20) as writer:
        for idx in frame_ids:
            s1_now = s1_traj[idx]
            s2_now = s2_traj[idx]
            p1_now = r1_pos(s1_now)
            p2_now = r2_pos(s2_now)
            dist = np.linalg.norm(p1_now - p2_now)
            status = "SAFE ✓" if dist >= D_SAFE else "COLLISION ✗"

            r1_dot.set_data([p1_now[0]], [p1_now[1]])
            r2_dot.set_data([p2_now[0]], [p2_now[1]])
            txt.set_text(f"step {idx}\n|r1−r2| = {dist:.3f}\n{status}")

            cd_dot.set_data([s1_now], [s2_now])
            cd_traj_anim.set_data(s1_traj[:idx+1], s2_traj[:idx+1])

            writer.append_data(fig_to_rgb(fig))
    plt.close(fig)

if __name__ == "__main__":
    run_ctspace_gif()
    run_coordination_gif()
    print("Done. See ./outputs/")
