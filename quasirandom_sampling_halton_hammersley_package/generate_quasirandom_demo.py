import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# Core sequences
# ============================================================

def van_der_corput(n, base=2):
    """Van der Corput sequence element: reverse digits of n in given base."""
    result = 0.0
    denom = 1.0
    val = n
    while val > 0:
        denom *= base
        result += (val % base) / denom
        val //= base
    return result


def halton_point(n, bases=(2, 3)):
    """Single Halton point in len(bases) dimensions."""
    return [van_der_corput(n, b) for b in bases]


def halton_sequence(N, bases=(2, 3)):
    """First N points of Halton sequence (skip index 0)."""
    pts = np.array([halton_point(i, bases) for i in range(1, N + 1)])
    return pts


def hammersley_sequence(N, base=2):
    """Hammersley set: first dim = i/N, second dim = Van der Corput base."""
    pts = np.zeros((N, 2))
    for i in range(N):
        pts[i, 0] = i / N
        pts[i, 1] = van_der_corput(i, base)
    return pts


# ============================================================
# Metrics
# ============================================================

def star_discrepancy_approx(pts, n_test=800):
    """Approximate star discrepancy D* over random test rectangles [0,a]x[0,b]."""
    N = len(pts)
    max_d = 0.0
    # test on a grid of anchor corners
    test_a = np.linspace(0.01, 1.0, n_test)
    test_b = np.linspace(0.01, 1.0, n_test)
    for a in test_a:
        inside = pts[:, 0] <= a
        for b in test_b:
            count = np.sum(inside & (pts[:, 1] <= b))
            d = abs(a * b - count / N)
            if d > max_d:
                max_d = d
    return max_d


def star_discrepancy_fast(pts, n_test=200):
    """Faster approximate star discrepancy using vectorised grid."""
    N = len(pts)
    test_a = np.linspace(0.01, 1.0, n_test)
    test_b = np.linspace(0.01, 1.0, n_test)
    aa, bb = np.meshgrid(test_a, test_b)
    max_d = 0.0
    for i in range(n_test):
        a = test_a[i]
        mask_x = pts[:, 0] <= a
        for j in range(n_test):
            b = test_b[j]
            count = np.sum(mask_x & (pts[:, 1] <= b))
            d = abs(a * b - count / N)
            if d > max_d:
                max_d = d
    return max_d


def dispersion(pts, n_grid=150):
    """Approximate dispersion: max min-distance from grid queries to point set."""
    gx = np.linspace(0, 1, n_grid)
    gy = np.linspace(0, 1, n_grid)
    qx, qy = np.meshgrid(gx, gy)
    queries = np.column_stack([qx.ravel(), qy.ravel()])
    max_min_d = 0.0
    for q in queries:
        dists = np.sqrt(np.sum((pts - q) ** 2, axis=1))
        md = np.min(dists)
        if md > max_min_d:
            max_min_d = md
    return max_min_d


def dispersion_with_center(pts, n_grid=150):
    """Return dispersion value and the query point achieving it."""
    gx = np.linspace(0, 1, n_grid)
    gy = np.linspace(0, 1, n_grid)
    qx, qy = np.meshgrid(gx, gy)
    queries = np.column_stack([qx.ravel(), qy.ravel()])
    max_min_d = 0.0
    best_q = queries[0]
    for q in queries:
        dists = np.sqrt(np.sum((pts - q) ** 2, axis=1))
        md = np.min(dists)
        if md > max_min_d:
            max_min_d = md
            best_q = q
    return max_min_d, best_q


# ============================================================
# Image 1: Pseudorandom vs Grid
# ============================================================
print("Generating Image 1...")
np.random.seed(42)
rand_pts = np.random.rand(64, 2)

side = int(np.sqrt(64))
gx = np.linspace(0, 1, side, endpoint=False) + 0.5 / side
gy = np.linspace(0, 1, side, endpoint=False) + 0.5 / side
grid_x, grid_y = np.meshgrid(gx, gy)
grid_pts = np.column_stack([grid_x.ravel(), grid_y.ravel()])

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].scatter(rand_pts[:, 0], rand_pts[:, 1], s=20, c='steelblue', edgecolors='k', linewidths=0.3)
axes[0].set_title("64 Pseudorandom points\n(numpy seed=42)", fontsize=11)
axes[0].set_xlim(0, 1); axes[0].set_ylim(0, 1)
axes[0].set_aspect('equal')
axes[0].set_xlabel("x"); axes[0].set_ylabel("y")

axes[1].scatter(grid_pts[:, 0], grid_pts[:, 1], s=20, c='tomato', edgecolors='k', linewidths=0.3)
axes[1].set_title("64 Uniform grid points\n(8×8 centered grid)", fontsize=11)
axes[1].set_xlim(0, 1); axes[1].set_ylim(0, 1)
axes[1].set_aspect('equal')
axes[1].set_xlabel("x"); axes[1].set_ylabel("y")

fig.suptitle("Pseudorandom vs Uniform Grid — neither is ideal for sampling",
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUT, "img1_pseudorandom_vs_grid.png"), dpi=130)
plt.close()
print("  Image 1 saved.")

# ============================================================
# Image 2: Van der Corput sequence
# ============================================================
print("Generating Image 2...")
n_vdc = 16
vdc_vals = [van_der_corput(i, 2) for i in range(1, n_vdc + 1)]

fig, ax = plt.subplots(figsize=(14, 4))
colors = plt.cm.viridis(np.linspace(0, 0.9, n_vdc))
for i, v in enumerate(vdc_vals):
    ax.plot(v, 0, 'o', color=colors[i], markersize=10, zorder=5)
    label = f"{i+1}: {v:.4f}"
    y_offset = 0.15 if (i % 2 == 0) else -0.15
    ax.annotate(label, (v, 0), textcoords="offset points",
                xytext=(0, 18 if y_offset > 0 else -22),
                ha='center', fontsize=7, color=colors[i], fontweight='bold')

ax.axhline(0, color='gray', linewidth=1)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.5, 0.5)
ax.set_yticks([])
ax.set_xlabel("Value on [0, 1]", fontsize=11)
ax.set_title("Van der Corput sequence (base 2) — first 16 elements\n"
             "Each new point subdivides the largest existing gap",
             fontsize=12, fontweight='bold')

# show binary representation for first 8
bin_text = "Binary reversal: "
for i in range(1, 9):
    bits = format(i, 'b')
    rev = bits[::-1]
    val = van_der_corput(i, 2)
    bin_text += f"  {i}→0.{rev}₂={val:.3f}"
ax.text(0.5, -0.35, bin_text, ha='center', fontsize=7.5, style='italic',
        transform=ax.get_xaxis_transform())

plt.tight_layout()
plt.savefig(os.path.join(OUT, "img2_van_der_corput.png"), dpi=130)
plt.close()
print("  Image 2 saved.")

# ============================================================
# Image 3: Halton 2D — 64, 128, 256 points
# ============================================================
print("Generating Image 3...")
counts = [64, 128, 256]
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, N in zip(axes, counts):
    pts = halton_sequence(N, bases=(2, 3))
    colors = np.linspace(0, 1, N)
    sc = ax.scatter(pts[:, 0], pts[:, 1], c=colors, cmap='coolwarm',
                    s=12, edgecolors='k', linewidths=0.2)
    ax.set_title(f"Halton (2,3) — N={N}", fontsize=11)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.set_xlabel("VdC base 2"); ax.set_ylabel("VdC base 3")

cbar = fig.colorbar(sc, ax=axes[-1], shrink=0.7)
cbar.set_label("Point order (red=first, blue=last)")
fig.suptitle("Halton sequence incrementally fills [0,1]² — bases (2,3)",
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUT, "img3_halton_2d.png"), dpi=130)
plt.close()
print("  Image 3 saved.")

# ============================================================
# Image 4: Hammersley vs Halton — 256 points
# ============================================================
print("Generating Image 4...")
N4 = 256
halton_pts = halton_sequence(N4, bases=(2, 3))
hammersley_pts = hammersley_sequence(N4, base=2)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].scatter(halton_pts[:, 0], halton_pts[:, 1], s=8, c='steelblue',
                edgecolors='k', linewidths=0.2)
axes[0].set_title(f"Halton sequence (bases 2,3)\nN={N4}", fontsize=11)
axes[0].set_xlim(0, 1); axes[0].set_ylim(0, 1)
axes[0].set_aspect('equal')
axes[0].set_xlabel("dim 1 (VdC base 2)"); axes[0].set_ylabel("dim 2 (VdC base 3)")

axes[1].scatter(hammersley_pts[:, 0], hammersley_pts[:, 1], s=8, c='tomato',
                edgecolors='k', linewidths=0.2)
axes[1].set_title(f"Hammersley set (base 2)\nN={N4}", fontsize=11)
axes[1].set_xlim(0, 1); axes[1].set_ylim(0, 1)
axes[1].set_aspect('equal')
axes[1].set_xlabel("dim 1 (i/N)"); axes[1].set_ylabel("dim 2 (VdC base 2)")

fig.suptitle("Halton (incremental) vs Hammersley (fixed N) — 256 points",
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUT, "img4_hammersley_vs_halton.png"), dpi=130)
plt.close()
print("  Image 4 saved.")

# ============================================================
# Image 5: Discrepancy explained
# ============================================================
print("Generating Image 5...")
np.random.seed(7)
good_pts = halton_sequence(64, bases=(2, 3))
bad_pts = np.random.rand(64, 2)
# cluster bad points to make discrepancy worse
bad_pts[:32] = bad_pts[:32] * 0.4 + 0.05

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

for ax, pts, title, color in [
    (axes[0], good_pts, "Low discrepancy (Halton 64)", 'steelblue'),
    (axes[1], bad_pts, "High discrepancy (clustered random)", 'tomato'),
]:
    ax.scatter(pts[:, 0], pts[:, 1], s=15, c=color, edgecolors='k', linewidths=0.3, zorder=5)

    # draw example rectangles anchored at origin
    test_rects = [(0.5, 0.5), (0.3, 0.7), (0.8, 0.4)]
    rect_colors = ['#2ca02c', '#9467bd', '#ff7f0e']
    N = len(pts)
    for (a, b), rc in zip(test_rects, rect_colors):
        rect = plt.Rectangle((0, 0), a, b, fill=False, edgecolor=rc,
                              linewidth=2, linestyle='--', zorder=4)
        ax.add_patch(rect)
        count = np.sum((pts[:, 0] <= a) & (pts[:, 1] <= b))
        d = abs(a * b - count / N)
        ax.text(a, b + 0.03, f"|{a*b:.2f}−{count}/{N}|={d:.3f}",
                fontsize=7, color=rc, fontweight='bold', ha='center')

    ax.set_xlim(0, 1); ax.set_ylim(0, 1.12)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("x"); ax.set_ylabel("y")

fig.suptitle("Star Discrepancy: D*(P) = sup |μ(R) − |P∩R|/N|  over all rectangles [0,a]×[0,b]",
             fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUT, "img5_discrepancy_explained.png"), dpi=130)
plt.close()
print("  Image 5 saved.")

# ============================================================
# Image 6: Dispersion explained
# ============================================================
print("Generating Image 6...")

side6 = int(np.sqrt(64))
gx6 = np.linspace(0, 1, side6, endpoint=False) + 0.5 / side6
gy6 = np.linspace(0, 1, side6, endpoint=False) + 0.5 / side6
gxm, gym = np.meshgrid(gx6, gy6)
grid64 = np.column_stack([gxm.ravel(), gym.ravel()])

np.random.seed(123)
rand64 = np.random.rand(64, 2)

fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

for ax, pts, title, color in [
    (axes[0], grid64, "Grid 8×8 — low dispersion", 'steelblue'),
    (axes[1], rand64, "Random 64 — higher dispersion", 'tomato'),
]:
    disp_val, center = dispersion_with_center(pts, n_grid=120)
    ax.scatter(pts[:, 0], pts[:, 1], s=15, c=color, edgecolors='k', linewidths=0.3, zorder=5)
    circle = plt.Circle(center, disp_val, fill=False, edgecolor='red',
                         linewidth=2.5, linestyle='-', zorder=4)
    ax.add_patch(circle)
    ax.plot(center[0], center[1], 'r+', markersize=12, markeredgewidth=2, zorder=6)
    ax.set_title(f"{title}\nδ = {disp_val:.4f}", fontsize=11)
    ax.set_xlim(-0.05, 1.05); ax.set_ylim(-0.05, 1.05)
    ax.set_aspect('equal')
    ax.set_xlabel("x"); ax.set_ylabel("y")

fig.suptitle("Dispersion δ(P) = max distance from any query point to nearest sample\n"
             "(red circle = largest empty ball)",
             fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUT, "img6_dispersion_explained.png"), dpi=130)
plt.close()
print("  Image 6 saved.")

# ============================================================
# Image 7: 4-panel comparison — 256 points each
# ============================================================
print("Generating Image 7 (this may take a moment)...")
N7 = 256

np.random.seed(42)
rand256 = np.random.rand(N7, 2)

side7 = int(np.sqrt(N7))
gx7 = np.linspace(0, 1, side7, endpoint=False) + 0.5 / side7
gy7 = np.linspace(0, 1, side7, endpoint=False) + 0.5 / side7
gxm7, gym7 = np.meshgrid(gx7, gy7)
grid256 = np.column_stack([gxm7.ravel(), gym7.ravel()])

halton256 = halton_sequence(N7, bases=(2, 3))
hammersley256 = hammersley_sequence(N7, base=2)

sets = [
    ("Pseudorandom", rand256, 'steelblue'),
    ("Grid 16×16", grid256, 'forestgreen'),
    ("Halton (2,3)", halton256, 'darkorange'),
    ("Hammersley (base 2)", hammersley256, 'tomato'),
]

fig, axes = plt.subplots(2, 2, figsize=(12, 12))
axes = axes.ravel()

for ax, (name, pts, color) in zip(axes, sets):
    disp_val, center = dispersion_with_center(pts, n_grid=100)
    disc_val = star_discrepancy_fast(pts, n_test=100)

    ax.scatter(pts[:, 0], pts[:, 1], s=8, c=color, edgecolors='k', linewidths=0.2, zorder=5)
    circle = plt.Circle(center, disp_val, fill=False, edgecolor='red',
                         linewidth=2, linestyle='--', zorder=4)
    ax.add_patch(circle)
    ax.plot(center[0], center[1], 'r+', markersize=10, markeredgewidth=2, zorder=6)
    ax.set_title(f"{name}  (N={N7})\nD*≈{disc_val:.4f}   δ≈{disp_val:.4f}",
                 fontsize=10, fontweight='bold')
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel("x"); ax.set_ylabel("y")

fig.suptitle("Comparison: Pseudorandom vs Grid vs Halton vs Hammersley — 256 points\n"
             "Red circle = largest empty ball (dispersion)",
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUT, "img7_comparison_all.png"), dpi=130)
plt.close()
print("  Image 7 saved.")

print("\nAll 7 images generated successfully.")
