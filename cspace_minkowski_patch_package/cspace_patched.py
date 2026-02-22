"""
Patched C-space visualization.
Key fix: C-obstacle(θ) = Obstacle ⊕ (−Robot rotated by θ)
         NOT Obstacle ⊕ Robot  ← GPT got this wrong (missing negation/reflection).
"""

import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import FancyArrowPatch
import matplotlib.gridspec as gridspec

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# ─────────────────────────── Geometry helpers ───────────────────────────────

def polygon_area(pts):
    x, y = pts[:, 0], pts[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - y * np.roll(x, -1))

def ensure_ccw(pts):
    pts = np.asarray(pts, dtype=float)
    if polygon_area(pts) < 0:
        pts = pts[::-1]
    return pts

def rotate_pts(pts, theta):
    c, s = math.cos(theta), math.sin(theta)
    R = np.array([[c, -s], [s, c]])
    return pts @ R.T

def shift_to_lowest(pts):
    pts = np.asarray(pts)
    idx = np.lexsort((pts[:, 0], pts[:, 1]))[0]
    return np.roll(pts, -idx, axis=0)

def edge_vectors(pts):
    return np.roll(pts, -1, axis=0) - pts

def angle(v):
    return math.atan2(v[1], v[0])

def convex_minkowski_sum(P, Q):
    """Minkowski sum of convex polygons P and Q (CCW)."""
    P = ensure_ccw(shift_to_lowest(P))
    Q = ensure_ccw(shift_to_lowest(Q))
    eP, eQ = edge_vectors(P), edge_vectors(Q)
    i = j = 0
    R = [P[0] + Q[0]]
    while i < len(eP) or j < len(eQ):
        if i == len(eP):
            R.append(R[-1] + eQ[j]); j += 1
        elif j == len(eQ):
            R.append(R[-1] + eP[i]); i += 1
        else:
            aP, aQ = angle(eP[i]), angle(eQ[j])
            if abs(aP - aQ) < 1e-12:
                R.append(R[-1] + eP[i] + eQ[j]); i += 1; j += 1
            elif aP < aQ:
                R.append(R[-1] + eP[i]); i += 1
            else:
                R.append(R[-1] + eQ[j]); j += 1
    R = np.asarray(R)
    if np.linalg.norm(R[-1] - R[0]) < 1e-9:
        R = R[:-1]
    return R

def closed(pts):
    return np.vstack([pts, pts[0]])

def plot_poly(ax, pts, **kw):
    c = closed(np.asarray(pts))
    ax.plot(c[:, 0], c[:, 1], **kw)

def plot_circle(ax, center, r, n=200, **kw):
    t = np.linspace(0, 2*np.pi, n)
    ax.plot(center[0] + r*np.cos(t), center[1] + r*np.sin(t), **kw)

def fill_poly(ax, pts, **kw):
    from matplotlib.patches import Polygon
    ax.add_patch(Polygon(pts, **kw))

# ─────────────────────────── Shapes ─────────────────────────────────────────

obstacle = ensure_ccw(np.array([
    [2.0, 1.0], [4.5, 1.3], [4.0, 3.6], [2.4, 3.8], [1.7, 2.4]
], dtype=float))

r = 0.45
k = 64
angles_k = np.linspace(0, 2*np.pi, k, endpoint=False)
circle_poly = ensure_ccw(np.c_[r*np.cos(angles_k), r*np.sin(angles_k)])
c_obstacle = convex_minkowski_sum(obstacle, circle_poly)

obstacle2 = ensure_ccw(np.array([
    [2.2, 1.2], [4.8, 1.0], [5.2, 3.2], [3.7, 4.2], [2.0, 3.4]
], dtype=float))

w, h = 1.2, 0.6
rect = ensure_ccw(np.array([
    [-w/2, -h/2], [w/2, -h/2], [w/2, h/2], [-w/2, h/2]
], dtype=float))

robot_positions = [(1.0, 1.0), (1.5, 2.4), (2.1, 2.8), (3.3, 2.2)]
pos_colors = ['#e67e22', '#e74c3c', '#8e44ad', '#7f8c8d']

thetas_deg  = [0, 30, 60, 90]
theta_colors = ['#2980b9', '#27ae60', '#e74c3c', '#f39c12']

# ═══════════════════════════════════════════════════════════════════════
# FIGURE 1 — Workspace: Circle robot
# ═══════════════════════════════════════════════════════════════════════
fig1, ax = plt.subplots(figsize=(7.5, 6.5))
fill_poly(ax, obstacle, alpha=0.18, color='steelblue', zorder=1)
plot_poly(ax, obstacle, color='steelblue', linewidth=2.5, zorder=2, label='Obstacle')
for p, col in zip(robot_positions, pos_colors):
    plot_circle(ax, p, r, color=col, linewidth=1.6, linestyle='-', zorder=3)
    ax.plot(*p, 'o', color=col, markersize=6, zorder=4)

# Annotate collision vs free
ax.annotate('Free (no overlap)', xy=(1.0, 1.0), xytext=(0.3, 0.4),
            fontsize=8.5, color=pos_colors[0],
            arrowprops=dict(arrowstyle='->', color=pos_colors[0], lw=1.2))
ax.annotate('Touching boundary\n→ COLLISION', xy=(1.5, 2.4), xytext=(0.2, 3.2),
            fontsize=8.5, color=pos_colors[1],
            arrowprops=dict(arrowstyle='->', color=pos_colors[1], lw=1.2))
ax.annotate('Partially inside\n→ COLLISION', xy=(2.1, 2.8), xytext=(0.2, 4.2),
            fontsize=8.5, color=pos_colors[2],
            arrowprops=dict(arrowstyle='->', color=pos_colors[2], lw=1.2))
ax.annotate('Center inside obstacle\n→ COLLISION', xy=(3.3, 2.2), xytext=(3.6, 4.0),
            fontsize=8.5, color=pos_colors[3],
            arrowprops=dict(arrowstyle='->', color=pos_colors[3], lw=1.2))

ax.set_aspect('equal', 'box')
ax.set_title("Figure 1 — Workspace: Circular robot (radius r = 0.45)\nmoving among a polygonal obstacle", fontsize=11, fontweight='bold')
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9)
plt.tight_layout()
fig1.savefig('/mnt/user-data/outputs/fig1_workspace_circle.png', dpi=150, bbox_inches='tight')

# ═══════════════════════════════════════════════════════════════════════
# FIGURE 2 — C-space: Translation only (Minkowski Sum with circle)
# ═══════════════════════════════════════════════════════════════════════
fig2, ax = plt.subplots(figsize=(7.5, 6.5))
fill_poly(ax, obstacle, alpha=0.15, color='steelblue', zorder=1)
plot_poly(ax, obstacle, color='steelblue', linewidth=1.5, zorder=2,
          linestyle='--', label='Original obstacle (workspace)')
fill_poly(ax, c_obstacle, alpha=0.20, color='crimson', zorder=2)
plot_poly(ax, c_obstacle, color='crimson', linewidth=2.5, zorder=3,
          label=f'C-obstacle = Obstacle ⊕ Circle(r={r})')

for p, col in zip(robot_positions, pos_colors):
    ax.plot(*p, 'o', color=col, markersize=8, zorder=5, markeredgecolor='white', markeredgewidth=0.8)

# Formula box
ax.text(0.02, 0.98,
        "C_obs = Obstacle ⊕ Robot\n"
        "(robot → point, obstacle expanded by r)\n"
        "Collision ⟺ robot_center inside C_obs",
        transform=ax.transAxes, fontsize=8.5, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.85))

ax.set_aspect('equal', 'box')
ax.set_title("Figure 2 — C-space (2D, translation only)\n"
             "C-obstacle = Obstacle ⊕ Circle(r)  [Minkowski Sum]", fontsize=11, fontweight='bold')
ax.set_xlabel("x (= robot position x)"); ax.set_ylabel("y (= robot position y)")
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9, loc='lower right')
plt.tight_layout()
fig2.savefig('/mnt/user-data/outputs/fig2_cspace_translation.png', dpi=150, bbox_inches='tight')

# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3 — KEY FIX: Robot shape vs its REFLECTION (−Robot)
# ═══════════════════════════════════════════════════════════════════════
fig3, axes = plt.subplots(1, 3, figsize=(13, 5))

for deg, ax, title in zip([0, 45, 90], axes,
                           ['θ = 0°', 'θ = 45°', 'θ = 90°']):
    th = math.radians(deg)
    Rth     = rotate_pts(rect, th)          # Robot rotated by θ
    neg_Rth = -Rth                          # −Robot (reflection through origin)

    fill_poly(ax, Rth,     alpha=0.30, color='#2980b9')
    fill_poly(ax, neg_Rth, alpha=0.30, color='#e74c3c')
    plot_poly(ax, Rth,     color='#2980b9', linewidth=2.2, label='Robot(θ)')
    plot_poly(ax, neg_Rth, color='#e74c3c', linewidth=2.2, label='−Robot(θ)  ← used in\nMinkowski sum')
    ax.plot(0, 0, 'k+', markersize=10, markeredgewidth=2)

    ax.set_xlim(-1.1, 1.1); ax.set_ylim(-1.1, 1.1)
    ax.set_aspect('equal'); ax.grid(True, alpha=0.3)
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.legend(fontsize=7.5, loc='upper right')
    ax.set_xlabel("x"); ax.set_ylabel("y")

fig3.suptitle(
    "Figure 3 — KEY FIX: Why we use −Robot (reflection) in Minkowski sum\n"
    "C-obstacle(θ) = Obstacle ⊕ (−Robot rotated by θ)   ← correct formula\n"
    "ChatGPT wrote: Obstacle ⊕ Robot   ← WRONG (missing negation)",
    fontsize=10.5, fontweight='bold', color='darkred'
)
plt.tight_layout()
fig3.savefig('/mnt/user-data/outputs/fig3_robot_vs_reflection.png', dpi=150, bbox_inches='tight')

# ═══════════════════════════════════════════════════════════════════════
# FIGURE 4 — Workspace: Rectangle robot with rotation
# ═══════════════════════════════════════════════════════════════════════
fig4, ax = plt.subplots(figsize=(7.5, 6.5))
fill_poly(ax, obstacle2, alpha=0.18, color='steelblue', zorder=1)
plot_poly(ax, obstacle2, color='steelblue', linewidth=2.5, zorder=2, label='Obstacle')
poses = [(1.4, 1.8, 0), (3.0, 2.2, math.radians(30)), (4.0, 3.1, math.radians(60))]
pcols = ['#e67e22', '#e74c3c', '#8e44ad']
for (x, y, th), col in zip(poses, pcols):
    Rth = rotate_pts(rect, th) + np.array([x, y])
    fill_poly(ax, Rth, alpha=0.25, color=col, zorder=3)
    plot_poly(ax, Rth, color=col, linewidth=2, zorder=4)
    ax.plot(x, y, 'o', color=col, markersize=7, zorder=5)
    ax.annotate(f'θ={int(math.degrees(th))}°', xy=(x, y),
                xytext=(x - 0.5, y - 0.35), fontsize=9, color=col,
                arrowprops=dict(arrowstyle='->', color=col))
ax.set_aspect('equal', 'box')
ax.set_title("Figure 4 — Workspace: Rectangle robot with rotation θ\n"
             "C-space is 3D: (x, y, θ)", fontsize=11, fontweight='bold')
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9)
plt.tight_layout()
fig4.savefig('/mnt/user-data/outputs/fig4_workspace_rect.png', dpi=150, bbox_inches='tight')

# ═══════════════════════════════════════════════════════════════════════
# FIGURE 5 — C-space slices (CORRECTED formula shown)
# ═══════════════════════════════════════════════════════════════════════
fig5, ax = plt.subplots(figsize=(8.5, 7.5))
cobs_slices = []
for deg, col in zip(thetas_deg, theta_colors):
    th = math.radians(deg)
    Rth     = rotate_pts(rect, th)
    neg_Rth = -Rth                          # ← CORRECT: use NEGATIVE robot
    cobs    = convex_minkowski_sum(obstacle2, neg_Rth)
    cobs_slices.append(cobs)
    fill_poly(ax, cobs, alpha=0.12, color=col, zorder=1)
    plot_poly(ax, cobs, color=col, linewidth=2.2, zorder=2,
              label=f'θ = {deg}°: Obs ⊕ (−Robot rotated {deg}°)')

ax.text(0.02, 0.02,
        "✓ Correct formula:\n"
        "C_obs(θ) = Obstacle ⊕ (−Robot(θ))\n\n"
        "✗ GPT's wrong formula:\n"
        "C_obs(θ) = Obstacle ⊕ Robot(θ)",
        transform=ax.transAxes, fontsize=8.5,
        bbox=dict(boxstyle='round', facecolor='#fff3cd', alpha=0.9))

ax.set_aspect('equal', 'box')
ax.set_title("Figure 5 — C-space slices for different θ (CORRECTED)\n"
             "C-obstacle(θ) = Obstacle ⊕ (−Robot rotated by θ)", fontsize=11, fontweight='bold')
ax.set_xlabel("x (robot ref. point x)"); ax.set_ylabel("y (robot ref. point y)")
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9, loc='upper right')
plt.tight_layout()
fig5.savefig('/mnt/user-data/outputs/fig5_cspace_slices_corrected.png', dpi=150, bbox_inches='tight')

# ═══════════════════════════════════════════════════════════════════════
# FIGURE 6 — 3D C-space (cylindrical topology) ← GPT missed this entirely
# ═══════════════════════════════════════════════════════════════════════
fig6 = plt.figure(figsize=(11, 7))
ax3d = fig6.add_subplot(111, projection='3d')

n_theta = 30
theta_range = np.linspace(0, 2*np.pi, n_theta, endpoint=False)

for deg, col in zip(thetas_deg, theta_colors):
    th     = math.radians(deg)
    neg_R  = -rotate_pts(rect, th)
    cobs   = convex_minkowski_sum(obstacle2, neg_R)
    z_val  = th  # actual radian value on θ axis
    cx, cy = closed(cobs)[:, 0], closed(cobs)[:, 1]
    ax3d.plot(cx, cy, z_val, color=col, linewidth=2,
              label=f'θ = {deg}°')
    ax3d.plot_surface(
        cx[np.newaxis, :].repeat(2, axis=0),
        cy[np.newaxis, :].repeat(2, axis=0),
        np.array([[z_val]*len(cx), [z_val]*len(cx)]),
        alpha=0.08, color=col
    )

# θ wrap-around: draw θ=0 again at top (2π) to show cylindrical nature
th     = 0.0
neg_R  = -rotate_pts(rect, th)
cobs   = convex_minkowski_sum(obstacle2, neg_R)
cx, cy = closed(cobs)[:, 0], closed(cobs)[:, 1]
ax3d.plot(cx, cy, 2*np.pi, color=theta_colors[0], linewidth=2,
          linestyle='--', alpha=0.5, label='θ = 360° ≡ θ = 0° (cylindrical!)')

ax3d.set_xlabel("x (robot x)"); ax3d.set_ylabel("y (robot y)")
ax3d.set_zlabel("θ (radians)")
ax3d.set_zticks([0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])
ax3d.set_zticklabels(['0°', '90°', '180°', '270°', '360°≡0°'])
ax3d.set_title(
    "Figure 6 — 3D C-space volume: (x, y, θ)\n"
    "Each slice = C-obstacle at one θ | Topology: (ℝ², S¹) = cylinder\n"
    "θ = 0° and θ = 360° are IDENTICAL (wrap-around) — GPT missed this!",
    fontsize=10, fontweight='bold'
)
ax3d.legend(fontsize=8, loc='upper left')
ax3d.view_init(elev=25, azim=-50)
plt.tight_layout()
fig6.savefig('/mnt/user-data/outputs/fig6_3d_cspace_cylindrical.png', dpi=150, bbox_inches='tight')

print("\nAll 6 figures saved successfully.")
print("\nSummary of patches applied vs ChatGPT:")
print("  [FIX 1] Minkowski Sum formula: Obs ⊕ (-Robot) not Obs ⊕ Robot")
print("  [FIX 2] Figure 3: explicit side-by-side Robot vs -Robot for each θ")
print("  [FIX 3] Figure 6: 3D C-space with cylindrical θ topology (θ=0 ≡ θ=360°)")
print("  [FIX 4] Annotations on all figures showing correct vs wrong formula")
