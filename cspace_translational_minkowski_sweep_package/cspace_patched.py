import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

OUT = "/mnt/user-data/outputs"
os.makedirs(OUT, exist_ok=True)

# ── helpers ────────────────────────────────────────────────────────────────────
def close_poly(P):
    P = np.asarray(P, dtype=float)
    return np.vstack([P, P[0]])

def reflect(P):
    return -np.asarray(P, dtype=float)

def convex_hull(points):
    pts = np.unique(np.asarray(points, dtype=float), axis=0)
    if len(pts) <= 1:
        return pts
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]

    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(tuple(p))
    for p in pts[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(tuple(p))
    return np.array(lower[:-1] + upper[:-1], dtype=float)

def minkowski_sum_convex(A, B):
    A, B = np.asarray(A, dtype=float), np.asarray(B, dtype=float)
    sums = (A[:, None, :] + B[None, :, :]).reshape(-1, 2)
    return convex_hull(sums), sums

def polygon_edges(P):
    P = np.asarray(P, dtype=float)
    return list(zip(P, np.roll(P, -1, axis=0)))

def sample_boundary(P, k_per_edge=10):
    samples = []
    for a, b in polygon_edges(P):
        for t in np.linspace(0, 1, k_per_edge, endpoint=False):
            samples.append(a*(1-t) + b*t)
    return np.asarray(samples)

def centroid(P):
    P = np.asarray(P, dtype=float)
    return P.mean(axis=0)

def save(fig, name):
    path = f"{OUT}/{name}"
    fig.savefig(path, dpi=130, bbox_inches='tight')
    plt.close(fig)
    print(f"  saved → {path}")

# ── shapes ─────────────────────────────────────────────────────────────────────
O = np.array([[2.0, 1.0], [6.0, 1.0], [6.0, 4.0], [2.0, 4.0]])
R = np.array([[0.0, 0.0], [1.2, 0.2], [0.4, 1.3]])
Rneg = reflect(R)
Cobs_hull, all_sums = minkowski_sum_convex(O, Rneg)

# palette
C_O    = "#2196F3"   # obstacle  – blue
C_R0   = "#FF9800"   # R at origin – orange
C_Rneg = "#9C27B0"   # -R        – purple
C_Cobs = "#4CAF50"   # C_obs     – green
C_q1   = "#F44336"   # q1 (no collision) – red
C_q2   = "#E91E63"   # q2 (collision)    – pink/magenta
C_q3   = "#00BCD4"   # q3 (collision)    – cyan

STYLE = dict(fontsize=10)

# ══════════════════════════════════════════════════════════════════════════════
# PLOT 1 — Workspace với legend phân biệt rõ ràng
# FIX: thêm legend, label từng q, tô màu vùng O, ghi rõ collision / free
# ══════════════════════════════════════════════════════════════════════════════
Qs = np.array([[1.0, 0.8], [2.5, 2.0], [5.6, 3.7]])
Q_labels  = ["q₁  (free – không va chạm)", "q₂  (collision – va chạm)", "q₃  (collision – va chạm)"]
Q_colors  = [C_q1, C_q2, C_q3]
Q_collide = [False, True, True]

fig, ax = plt.subplots(figsize=(7, 6))
ax.set_aspect('equal')

# fill obstacle
from matplotlib.patches import Polygon as MplPoly
ax.add_patch(MplPoly(O, closed=True, facecolor="#BBDEFB", edgecolor=C_O, lw=2, label="Vật cản O"))

# R at origin (reference, no fill)
ax.plot(*close_poly(R).T, color=C_R0, lw=1.8, ls='--', label="Robot R (gốc, reference)")
ax.scatter(*centroid(R), color=C_R0, zorder=5, s=40)

# R at each q
for q, lbl, col, coll in zip(Qs, Q_labels, Q_colors, Q_collide):
    Rq = R + q
    hatch = '///' if coll else ''
    ax.add_patch(MplPoly(Rq, closed=True, facecolor=col+'33', edgecolor=col, lw=2, hatch=hatch))
    ax.plot(*close_poly(Rq).T, color=col, lw=2)
    # reference point dot
    ax.scatter(*q, color=col, s=60, zorder=6)
    # label near centroid
    cx, cy = centroid(Rq)
    suffix = " ✗" if coll else " ✓"
    ax.annotate(f"q=({q[0]},{q[1]}){suffix}", xy=(cx, cy),
                fontsize=8.5, ha='center', color=col,
                bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7))
    # invisible proxy for legend
    ax.plot([], [], color=col, lw=2, label=lbl)

ax.set_xlim(-0.5, 8); ax.set_ylim(-0.5, 5.5)
ax.set_title("Workspace: robot R ở 3 cấu hình q\n"
             "(✓ = free / không va chạm,  ✗ = collision / va chạm)", fontsize=11)
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.legend(fontsize=8, loc='upper left')
ax.grid(True, alpha=0.3)
save(fig, "img1_workspace.png")

# ══════════════════════════════════════════════════════════════════════════════
# PLOT 2 — R và -R (phản xạ)
# FIX: fill cả hai, đánh dấu các đỉnh, thêm annotation giải thích phép phản xạ
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 6))
ax.set_aspect('equal')

ax.add_patch(MplPoly(R,    closed=True, facecolor="#2196F333", edgecolor=C_O,    lw=2, label="Robot R"))
ax.add_patch(MplPoly(Rneg, closed=True, facecolor="#FF980033", edgecolor=C_R0,   lw=2, label="−R  (phản xạ qua gốc)"))

# label vertices
for i, (r, rn) in enumerate(zip(R, Rneg)):
    ax.annotate(f"r{i+1}=({r[0]:.1f},{r[1]:.1f})", r,
                textcoords="offset points", xytext=(6, 4), fontsize=8, color=C_O)
    ax.annotate(f"−r{i+1}=({rn[0]:.1f},{rn[1]:.1f})", rn,
                textcoords="offset points", xytext=(6, -12), fontsize=8, color=C_R0)
    ax.scatter(*r, color=C_O, s=50, zorder=5)
    ax.scatter(*rn, color=C_R0, s=50, zorder=5)
    # arrow
    ax.annotate("", xy=rn, xytext=r,
                arrowprops=dict(arrowstyle="-|>", color='gray', lw=0.8))

ax.axhline(0, color='k', lw=0.8, ls=':'); ax.axvline(0, color='k', lw=0.8, ls=':')
ax.scatter(0, 0, color='k', s=80, zorder=6)
ax.annotate("origin (0,0)", (0, 0), textcoords="offset points", xytext=(5, 5), fontsize=8)

ax.set_title("Robot R  và  −R = {−r | r ∈ R}\n(phản xạ qua gốc tọa độ)", fontsize=11)
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
save(fig, "img2_reflect.png")

# ══════════════════════════════════════════════════════════════════════════════
# PLOT 3 — Minkowski sum: điểm tổng + hull
# FIX: tô vùng C_obs, label các điểm góc, thêm legend + chú thích Minkowski sum
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 6))
ax.set_aspect('equal')

# fill C_obs
ax.add_patch(MplPoly(Cobs_hull, closed=True, facecolor="#4CAF5022", edgecolor=C_Cobs, lw=2.5,
                     label="$C_{obs}$ = O ⊕ (−R)  [hull]"))
# fill O
ax.add_patch(MplPoly(O, closed=True, facecolor="#2196F322", edgecolor=C_O, lw=2, label="Vật cản O"))

# all sum points
ax.scatter(all_sums[:, 0], all_sums[:, 1], color='gray', s=25, alpha=0.7, label="Điểm tổng o+(−r)")

# label hull vertices
for v in Cobs_hull:
    ax.scatter(*v, color=C_Cobs, s=50, zorder=5)
    ax.annotate(f"({v[0]:.1f},{v[1]:.1f})", v,
                textcoords="offset points", xytext=(4, 4), fontsize=7.5, color=C_Cobs)

# annotation box
ax.text(0.02, 0.97,
        "$C_{obs} = O \\oplus (-R)$\n"
        "$= \\{o - r \\mid o \\in O,\\ r \\in R\\}$\n"
        "Robot (điểm) trong vùng xanh → va chạm",
        transform=ax.transAxes, va='top', fontsize=9,
        bbox=dict(boxstyle='round', fc='white', alpha=0.85))

ax.set_xlim(-0.5, 7.5); ax.set_ylim(-1, 5)
ax.set_title("$C_{obs} = O \\oplus (-R)$: Minkowski sum → C-space obstacle", fontsize=11)
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.legend(fontsize=8.5); ax.grid(True, alpha=0.3)
save(fig, "img3_cobs_hull.png")

# ══════════════════════════════════════════════════════════════════════════════
# PLOT 4–7 — Incremental construction
# FIX: hiển thị những đỉnh O đang dùng, label điểm tổng partial, màu nhất quán
# ══════════════════════════════════════════════════════════════════════════════
for i in range(len(O)):
    partial = O[:i+1]
    hull_i, sums_i = minkowski_sum_convex(partial, Rneg)

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.set_aspect('equal')

    # full O (mờ)
    ax.add_patch(MplPoly(O, closed=True, facecolor="#2196F311", edgecolor=C_O, lw=1.5, ls='--'))

    # highlight active vertices of O
    ax.scatter(partial[:, 0], partial[:, 1], color=C_O, s=80, zorder=6, label=f"Đỉnh O đang dùng ({i+1})")
    for j, v in enumerate(partial):
        ax.annotate(f"o{j+1}=({v[0]:.0f},{v[1]:.0f})", v,
                    textcoords="offset points", xytext=(5, 5), fontsize=8, color=C_O)

    # sum points
    ax.scatter(sums_i[:, 0], sums_i[:, 1], color='gray', s=22, alpha=0.7, label="Điểm tổng partial")

    # hull
    if len(hull_i) >= 3:
        ax.add_patch(MplPoly(hull_i, closed=True, facecolor=C_Cobs+'22', edgecolor=C_Cobs, lw=2.2,
                             label=f"Hull partial (iter {i+1})"))

    # final C_obs for reference (ghost)
    ax.plot(*close_poly(Cobs_hull).T, color=C_Cobs, lw=1, ls=':', alpha=0.4, label="C_obs cuối (tham chiếu)")

    ax.set_xlim(-0.5, 7.5); ax.set_ylim(-1, 5)
    ax.set_title(f"Iteration {i+1}/4: hull( O[:{i+1}] ⊕ (−R) )\n"
                 f"— thêm đỉnh o{i+1} của O, build lại hull", fontsize=10)
    ax.set_xlabel("x"); ax.set_ylabel("y")
    ax.legend(fontsize=8, loc='upper right'); ax.grid(True, alpha=0.3)
    save(fig, f"img{i+4}_iter{i+1}.png")

# ══════════════════════════════════════════════════════════════════════════════
# PLOT 8–16 (10 sweep frames)
# FIX: tô vùng C_obs rõ hơn, annotation giải thích từng frame, thêm trail
# ══════════════════════════════════════════════════════════════════════════════
boundary_samples = sample_boundary(O, k_per_edge=8)
idx = np.linspace(0, len(boundary_samples)-1, 10, dtype=int)
chosen = boundary_samples[idx]

for j, tpoint in enumerate(chosen, start=1):
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.set_aspect('equal')

    # C_obs filled
    ax.add_patch(MplPoly(Cobs_hull, closed=True, facecolor="#4CAF5018", edgecolor=C_Cobs, lw=2.2,
                         label="$C_{obs}$ (biên vật cản C-space)"))
    # O
    ax.add_patch(MplPoly(O, closed=True, facecolor="#2196F322", edgecolor=C_O, lw=1.8, label="Vật cản O"))

    # trail: -R tại tất cả các vị trí trước (mờ)
    for prev in chosen[:j-1]:
        ax.plot(*close_poly(Rneg + prev).T, color=C_Rneg, lw=0.8, alpha=0.18)

    # -R tại tpoint hiện tại
    Rneg_here = Rneg + tpoint
    ax.add_patch(MplPoly(Rneg_here, closed=True, facecolor=C_Rneg+'44', edgecolor=C_Rneg, lw=2,
                         label="−R tại điểm biên hiện tại"))
    ax.scatter(*tpoint, color='black', s=70, zorder=7, label=f"Điểm biên q=({tpoint[0]:.2f},{tpoint[1]:.2f})")
    ax.annotate(f"  q=({tpoint[0]:.1f},{tpoint[1]:.1f})", tpoint,
                fontsize=8.5, color='black',
                bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.8))

    # annotation
    ax.text(0.02, 0.97,
            f"Frame {j}/10\n"
            "Khi −R trượt theo biên O,\n"
            "tập hợp vị trí origin của −R\n"
            "tạo thành biên của $C_{{obs}}$",
            transform=ax.transAxes, va='top', fontsize=8.5,
            bbox=dict(boxstyle='round', fc='white', alpha=0.88))

    ax.set_xlim(-0.5, 7.5); ax.set_ylim(-1.5, 5.5)
    ax.set_title(f"Sweep frame {j}/10: trượt (−R) theo biên O\n"
                 f"→ minh họa vì sao C_obs = O ⊕ (−R) 'nở' vật cản", fontsize=10)
    ax.set_xlabel("x"); ax.set_ylabel("y")
    ax.legend(fontsize=8, loc='upper right'); ax.grid(True, alpha=0.3)
    save(fig, f"img{j+7}_sweep{j:02d}.png")

print("\nAll images saved to", OUT)
