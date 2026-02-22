import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ----------------------------
# 1) PRNG example: LCG
# ----------------------------
def lcg(seed: int, a: int, c: int, m: int, n: int):
    x = seed
    out = []
    for _ in range(n):
        x = (a * x + c) % m
        out.append(x)
    return np.array(out, dtype=np.int64)

def to_unit_interval(xs, m):
    return xs / float(m)

m = 2**16   # 65536
a = 1103515245 % m
c = 12345
seed = 4242

N = 5000
xs = lcg(seed, a, c, m, N)
us = to_unit_interval(xs, m)

# ----------------------------
# Image 1: Time series (first 300)
# ----------------------------
plt.figure(figsize=(8, 4))
plt.plot(us[:300], linewidth=0.8, color='steelblue')
plt.title("LCG output (normalized) — first 300 values")
plt.xlabel("n")
plt.ylabel("x_n / m")
plt.tight_layout()
plt.savefig("/home/claude/img1_timeseries.png", dpi=130)
plt.close()
print("Image 1 saved.")

# ----------------------------
# Image 2: Histogram
# ----------------------------
plt.figure(figsize=(7, 4))
plt.hist(us, bins=50, color='steelblue', edgecolor='white', linewidth=0.4)
plt.title("LCG output distribution (normalized) — histogram")
plt.xlabel("x_n / m")
plt.ylabel("count")
plt.tight_layout()
plt.savefig("/home/claude/img2_histogram.png", dpi=130)
plt.close()
print("Image 2 saved.")

# ----------------------------
# Image 3 (PATCHED): Side-by-side lag plots
#   Left  — m=2^16 (large): looks like scatter → "trông random"
#   Right — m=2^8  (small):  lattice clearly visible
# ----------------------------
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Left: large m (original)
axes[0].scatter(us[:-1], us[1:], s=2, alpha=0.4, color='steelblue')
axes[0].set_title(f"Lag plot — m = 2¹⁶ (large)\nLooks random (no obvious pattern)", fontsize=10)
axes[0].set_xlabel("x_n / m")
axes[0].set_ylabel("x_{n+1} / m")

# Right: small m → lattice structure exposed
m_small = 64
a_small = a % m_small
c_small = c % m_small
xs_small = lcg(seed, a_small, c_small, m_small, 500)
us_small = xs_small / float(m_small)

axes[1].scatter(us_small[:-1], us_small[1:], s=40, alpha=0.7, color='tomato')
axes[1].set_title(f"Lag plot — m = 2⁶ (small)\nLattice structure clearly visible!", fontsize=10)
axes[1].set_xlabel("x_n / m")
axes[1].set_ylabel("x_{n+1} / m")

fig.suptitle("LCG Lag Plot: (x_n, x_{{n+1}}) — lattice structure depends on modulus size",
             fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig("/home/claude/img3_lagplot_patched.png", dpi=130)
plt.close()
print("Image 3 (patched) saved.")

# ----------------------------
# 2) Predictability attack
# ----------------------------
def egcd(a, b):
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)

def modinv(a, m):
    g, x, _ = egcd(a % m, m)
    if g != 1:
        return None
    return x % m

def lcg_step(x, a, c, m):
    return (a * x + c) % m

x0 = x1 = x2 = None
idx = None
for i in range(N - 2):
    t0, t1, t2 = int(xs[i]), int(xs[i+1]), int(xs[i+2])
    d = (t1 - t0) % m
    if modinv(d, m) is not None:
        x0, x1, x2 = t0, t1, t2
        idx = i
        break

d1 = (x1 - x0) % m
d2 = (x2 - x1) % m
a_rec = (d2 * modinv(d1, m)) % m
c_rec = (x1 - a_rec * x0) % m

pred = [x0, x1, x2]
for _ in range(5):
    pred.append(lcg_step(pred[-1], a_rec, c_rec, m))
true_seq = [int(xs[idx+j]) for j in range(8)]

print("\n=== LCG parameter recovery demo ===")
print(f"True parameters (mod m): a={a}, c={c}")
print(f"Recovered:               a={a_rec}, c={c_rec}")
print(f"Match: {a==a_rec and c==c_rec}")

window = 200
pred_stream = [x0]
for _ in range(window - 1):
    pred_stream.append(lcg_step(pred_stream[-1], a_rec, c_rec, m))
pred_stream = np.array(pred_stream, dtype=np.int64)
true_stream = xs[idx:idx+window]

# ----------------------------
# Image 4: Predictability demo
# ----------------------------
fig, axes = plt.subplots(2, 1, figsize=(10, 7))

# Top: full overlay
axes[0].plot(true_stream[:200], color='steelblue', linewidth=1.2, label="Actual LCG output")
axes[0].plot(pred_stream[:200], linestyle='--', color='tomato', linewidth=1.2,
             label="Predicted (recovered a, c)")
axes[0].set_title("LCG Predictability Attack — Full 200-step window\n"
                  "Predicted perfectly overlaps Actual (lines are identical)", fontweight='bold')
axes[0].set_xlabel("offset from x₀")
axes[0].set_ylabel("x")
axes[0].legend()

# Bottom: zoom first 30 steps to see overlap clearly
axes[1].plot(true_stream[:30], 'o-', color='steelblue', linewidth=1.5,
             markersize=5, label="Actual")
axes[1].plot(pred_stream[:30], 's--', color='tomato', linewidth=1.5,
             markersize=4, label="Predicted")
axes[1].set_title("Zoom: first 30 steps — dots overlap perfectly (error = 0)")
axes[1].set_xlabel("offset from x₀")
axes[1].set_ylabel("x")
axes[1].legend()

plt.suptitle(f"Attack: only 3 observed values → recovered a={a_rec}, c={c_rec} (true: a={a}, c={c})",
             fontsize=10, color='darkred')
plt.tight_layout()
plt.savefig("/home/claude/img4_predictability.png", dpi=130)
plt.close()
print("Image 4 saved.")
