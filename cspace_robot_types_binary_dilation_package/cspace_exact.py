"""
PATCHED: Exact C-space obstacle computation using binary_dilation
Key fix: use proper robot-shaped structuring elements instead of AABB approximation
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.ndimage import binary_dilation

# ─────────────────────────────────────────
# Workspace setup
# ─────────────────────────────────────────
xmin, xmax = 0.0, 10.0
ymin, ymax = 0.0, 10.0

# Obstacles: (x1, y1, x2, y2) lower-left to upper-right
W_obs = [
    (2.0, 2.0, 4.0, 4.0),
    (6.0, 1.5, 8.5, 3.0),
    (5.0, 6.0, 9.0, 8.5),
]

N = 600  # grid resolution
xs = np.linspace(xmin, xmax, N)
ys = np.linspace(ymin, ymax, N)
resolution = (xmax - xmin) / N
XX, YY = np.meshgrid(xs, ys, indexing="xy")


def rect_mask(x1, y1, x2, y2):
    return (XX >= x1) & (XX <= x2) & (YY >= y1) & (YY <= y2)


# Rasterise workspace obstacles
W_mask = np.zeros((N, N), dtype=bool)
for obs in W_obs:
    W_mask |= rect_mask(*obs)


# ─────────────────────────────────────────
# Structuring-element builders (the key fix)
# ─────────────────────────────────────────

def make_disc_struct(r, res):
    """
    EXACT structuring element for disc robot of radius r.
    Each pixel within distance r of centre is True.
    Produces ROUNDED corners in C_obs (GPT had square corners).
    """
    half = int(np.ceil(r / res)) + 1
    size = 2 * half + 1
    cy, cx = half, half
    struct = np.zeros((size, size), dtype=bool)
    for i in range(size):
        for j in range(size):
            dx = (j - cx) * res
            dy = (i - cy) * res
            if dx**2 + dy**2 <= r**2:
                struct[i, j] = True
    return struct


def make_rect_struct(a, b, theta, res):
    """
    EXACT structuring element for rectangle robot (half-sizes a×b) rotated by theta.
    A pixel belongs to the struct iff the workspace point it represents
    lies inside the rotated rectangle.

    For each candidate pixel at offset (dx, dy), rotate by -theta and check
    if the unrotated point falls within [-a,a]×[-b,b].

    This is symmetric (−R = R for rectangles centred at origin), so
    binary_dilation gives the exact Minkowski sum  W_obs ⊕ (−R).
    """
    # Bounding box of rotated rectangle (needed to size the kernel)
    c, s = abs(np.cos(theta)), abs(np.sin(theta))
    hx = a * c + b * s
    hy = a * s + b * c

    half_x = int(np.ceil(hx / res)) + 1
    half_y = int(np.ceil(hy / res)) + 1
    size_x = 2 * half_x + 1
    size_y = 2 * half_y + 1

    struct = np.zeros((size_y, size_x), dtype=bool)
    ct, st = np.cos(theta), np.sin(theta)

    for i in range(size_y):
        for j in range(size_x):
            dx = (j - half_x) * res
            dy = (i - half_y) * res
            # Inverse rotation: check if (dx,dy) is inside unrotated rect
            rx = ct * dx + st * dy
            ry = -st * dx + ct * dy
            if abs(rx) <= a and abs(ry) <= b:
                struct[i, j] = True
    return struct


# ─────────────────────────────────────────
# Compute exact C_obs for each robot type
# ─────────────────────────────────────────

# 1) Point robot — trivially exact
C_point = W_mask.copy()

# 2) Disc robot — EXACT (rounded corners at obstacle edges)
r = 0.5
disc_struct = make_disc_struct(r, resolution)
C_disc_exact = binary_dilation(W_mask, structure=disc_struct)

# GPT approximation for comparison
C_disc_gpt = np.zeros((N, N), dtype=bool)
for (x1, y1, x2, y2) in W_obs:
    C_disc_gpt |= rect_mask(x1 - r, y1 - r, x2 + r, y2 + r)

# 3) Axis-aligned rectangle — already exact in GPT (Minkowski sum of two
#    axis-aligned rectangles is an axis-aligned rectangle), but we confirm
#    with binary_dilation for consistency.
a, b = 0.8, 0.4
rect_struct_0 = make_rect_struct(a, b, 0.0, resolution)
C_box_exact = binary_dilation(W_mask, structure=rect_struct_0)

# 4) Rotating rectangle — EXACT slices (GPT used AABB over-approximation)
thetas_deg = [0, 30, 60, 90]
slices = []
for deg in thetas_deg:
    th = np.radians(deg)
    struct = make_rect_struct(a, b, th, resolution)
    C_th_exact = binary_dilation(W_mask, structure=struct)

    # GPT AABB approximation for the same angle
    c, s = abs(np.cos(th)), abs(np.sin(th))
    hx, hy = a * c + b * s, a * s + b * c
    C_th_gpt = np.zeros((N, N), dtype=bool)
    for (x1, y1, x2, y2) in W_obs:
        C_th_gpt |= rect_mask(x1 - hx, y1 - hy, x2 + hx, y2 + hy)

    slices.append((deg, th, C_th_exact, C_th_gpt, hx, hy))


# ─────────────────────────────────────────
# Plotting helpers
# ─────────────────────────────────────────

CMAP = "plasma"


def show_single(mask, title, ax=None, show=True):
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(mask.astype(int), origin="lower",
              extent=[xmin, xmax, ymin, ymax],
              aspect="equal", cmap=CMAP, vmin=0, vmax=1)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("x"); ax.set_ylabel("y")
    if standalone and show:
        plt.tight_layout(); plt.show()


def show_comparison(mask_approx, mask_exact, title_approx, title_exact, diff_title):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    show_single(mask_approx, f"APPROX (GPT)\n{title_approx}", ax=axes[0])
    show_single(mask_exact,  f"EXACT (patched)\n{title_exact}",  ax=axes[1])
    # Difference: cells in approx but NOT in exact (false obstacles)
    diff = mask_approx & ~mask_exact
    axes[2].imshow(diff.astype(int), origin="lower",
                   extent=[xmin, xmax, ymin, ymax],
                   aspect="equal", cmap="hot", vmin=0, vmax=1)
    axes[2].set_title(f"Difference (orange = false C_obs)\n{diff_title}", fontsize=10)
    axes[2].set_xlabel("x"); axes[2].set_ylabel("y")
    pct = 100 * diff.sum() / max(mask_approx.sum(), 1)
    fig.suptitle(f"Over-approximation: {pct:.1f}% extra blocked cells", fontsize=12, y=1.01)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────
# Generate and save all figures
# ─────────────────────────────────────────

import os
OUT = "/mnt/user-data/outputs"
os.makedirs(OUT, exist_ok=True)

# ── Fig 1: Point robot (exact, no change) ──────────────────────────────────
fig, ax = plt.subplots(figsize=(6, 6))
show_single(C_point,
            "C_obs – Point Robot  q=(x,y)\nC_obs = W_obs  [exact, trivial]",
            ax=ax, show=False)
fig.tight_layout()
fig.savefig(f"{OUT}/fig1_point_robot.png", dpi=130)
plt.close(fig)
print("Saved fig1")

# ── Fig 2: Disc robot comparison ───────────────────────────────────────────
fig = show_comparison(
    C_disc_gpt, C_disc_exact,
    f"Disc r={r}: rect expansion\n(square corners — WRONG)",
    f"Disc r={r}: circular dilation\n(rounded corners — EXACT)",
    "Corners & edges of obstacles"
)
fig.savefig(f"{OUT}/fig2_disc_comparison.png", dpi=130)
plt.close(fig)
print("Saved fig2")

# ── Fig 3: Axis-aligned rect (was already exact, confirm) ──────────────────
fig, ax = plt.subplots(figsize=(6, 6))
show_single(C_box_exact,
            f"C_obs – Axis-Aligned Rectangle  a={a}, b={b}\n"
            "Minkowski sum of rect⊕rect = exact rectangle growth",
            ax=ax, show=False)
fig.tight_layout()
fig.savefig(f"{OUT}/fig3_rect_aligned.png", dpi=130)
plt.close(fig)
print("Saved fig3")

# ── Fig 4: Rotating rectangle — 4-panel exact slices ──────────────────────
fig, axes = plt.subplots(2, 4, figsize=(22, 11))
for col, (deg, th, C_exact, C_gpt, hx, hy) in enumerate(slices):
    diff = C_gpt & ~C_exact
    pct = 100 * diff.sum() / max(C_gpt.sum(), 1)

    axes[0, col].imshow(C_exact.astype(int), origin="lower",
                        extent=[xmin, xmax, ymin, ymax],
                        aspect="equal", cmap=CMAP, vmin=0, vmax=1)
    axes[0, col].set_title(f"EXACT  θ={deg}°\nhalf-extents=({hx:.2f},{hy:.2f})", fontsize=9)
    axes[0, col].set_xlabel("x"); axes[0, col].set_ylabel("y")

    axes[1, col].imshow(diff.astype(int), origin="lower",
                        extent=[xmin, xmax, ymin, ymax],
                        aspect="equal", cmap="hot", vmin=0, vmax=1)
    axes[1, col].set_title(f"Over-approx error  θ={deg}°\n(+{pct:.1f}% false cells)", fontsize=9)
    axes[1, col].set_xlabel("x"); axes[1, col].set_ylabel("y")

fig.suptitle("Rotating Rectangle  q=(x,y,θ)\nTop: exact C_obs slices | Bottom: GPT AABB over-approximation error",
             fontsize=13)
fig.tight_layout()
fig.savefig(f"{OUT}/fig4_rotating_rect_exact.png", dpi=130)
plt.close(fig)
print("Saved fig4")

# ── Fig 5: Side-by-side GPT vs Exact for one interesting angle (45°) ───────
th45 = np.radians(45)
struct45 = make_rect_struct(a, b, th45, resolution)
C_45_exact = binary_dilation(W_mask, structure=struct45)
c45, s45 = abs(np.cos(th45)), abs(np.sin(th45))
hx45, hy45 = a*c45 + b*s45, a*s45 + b*c45
C_45_gpt = np.zeros((N, N), dtype=bool)
for (x1, y1, x2, y2) in W_obs:
    C_45_gpt |= rect_mask(x1-hx45, y1-hy45, x2+hx45, y2+hy45)

fig = show_comparison(
    C_45_gpt, C_45_exact,
    "Rotating rect θ=45°: AABB expansion",
    "Rotating rect θ=45°: exact rotated rect dilation",
    "θ=45° shows maximal AABB error"
)
fig.savefig(f"{OUT}/fig5_rotate45_comparison.png", dpi=130)
plt.close(fig)
print("Saved fig5")

print("\nAll figures saved to", OUT)
