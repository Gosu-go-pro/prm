# Explain the concept of expansiveness (Question 16) -- PRM-oriented package

This package answers:

> **Question 16: explain the concept of expansiveness and discuss pros/cons.**

It is aligned with the PRM lecture discussion of **(epsilon, alpha, beta)-expansive free spaces** and why roadmap connectivity/coverage becomes easier in expansive spaces.

---

## Core definitions

Let $F$ be free space, and let $\mu(\cdot)$ denote volume (measure).

### 1. Visibility set of a configuration

$$
V(q) = \lbrace q' \in F \mid \overline{qq'} \subset F \rbrace
$$

$V(q)$ is the set of free configurations directly visible from $q$ via a collision-free straight-line path.

### 2. Epsilon-good free space

$$
\frac{\mu(V(q))}{\mu(F)} \ge \epsilon, \quad \forall q \in F
$$

Interpretation: every point can "see" at least an $\epsilon$ fraction of free space.
A convex free space is maximally $\epsilon$-good ($\epsilon = 1$).

### 3. Beta-lookout of a subset $S \subset F$

$$
\beta\text{-lookout}(S)
= \left\lbrace q \in S \mid
\frac{\mu\big(V(q) \cap (F \setminus S)\big)}{\mu(F \setminus S)} \ge \beta
\right\rbrace
$$

Interpretation: points in $S$ that can see a significant ($\ge \beta$) fraction of the outside region $F \setminus S$.
These are the "gateway" points near passage openings.

### 4. (epsilon, alpha, beta)-expansive

$F$ is $(\epsilon,\alpha,\beta)$-expansive if:

- $F$ is epsilon-good, and
- for every measurable $S \subset F$:

$$
\frac{\mu(\beta\text{-lookout}(S))}{\mu(S)} \ge \alpha
$$

Interpretation: each subset contains at least an $\alpha$ fraction of "gateway" points (lookouts) that see into the complement.

---

## Why expansiveness matters for PRM

Lecture intuition: in expansive spaces, roadmap quality improves quickly as milestones increase.

- Larger $\epsilon, \alpha, \beta$ &rarr; easier connectivity and coverage.
- Narrow passages reduce these volumetric ratios, making it harder for a random roadmap to capture the connectivity.
- Then PRM needs more milestones (or smarter sampling) to achieve similar success probability.

**Probabilistic completeness:** in an $(\epsilon,\alpha,\beta)$-expansive free space, the probability that a PRM planner fails to find a path (when one exists) decreases **exponentially** with the number of milestones $m$:

$$
P_{\mathrm{fail}}(m) \le c \cdot e^{-\gamma \, m}
$$

where the decay rate $\gamma$ grows with better expansiveness parameters. A didactic simplification used in the figures is:

$$
P_{\mathrm{fail}}(m) \approx e^{-k \, m}
$$

where larger $k$ corresponds to more expansive spaces.

---

## Pros and cons of the expansiveness concept

### Pros

| Advantage | Explanation |
|-----------|-------------|
| **Geometric intuition** | Gives a clear picture of why some C-spaces are easy/hard for PRM — wide visibility means better roadmap coverage. |
| **Probabilistic completeness** | Proves that PRM success probability converges to 1 exponentially in expansive settings. |
| **Motivates PRM variants** | Explains *why* narrow-passage sampling strategies (Gaussian, Bridge, OBPRM) help — they increase the effective lookout volume. |

### Cons / limitations

| Limitation | Explanation |
|------------|-------------|
| **Hard to compute** | $(\epsilon,\alpha,\beta)$ are nearly impossible to calculate exactly in real high-dimensional C-spaces. |
| **No stopping rule** | The theory gives asymptotic trends, but does not tell a planner when to stop adding milestones. |
| **Implementation gap** | Real PRM performance depends heavily on local planner quality, collision-checking cost, and connection strategy — not just expansiveness. |

---

## Visual walkthrough

### Image 1 — Three geometry cases

**File:** `img1_expansiveness_cases.png`

![Three geometry cases](img1_expansiveness_cases.png)

This figure shows three qualitative scenarios for PRM expansiveness:

- **Case A (Convex free space):** Every point sees the entire free space, so $\epsilon = \alpha = \beta = 1$ — this is the maximally expansive case. PRM builds a connected roadmap very quickly.
- **Case B (Single narrow passage):** A thin wall with a tiny opening divides the space into two large chambers. The lookout region near the choke point is very small, dramatically lowering $\alpha$ and $\beta$. PRM needs many milestones to sample inside the narrow passage.
- **Case C (Multiple moderate passages):** The same wall has *two* wider openings. Although the space is still divided, the lookout volume is larger than Case B, so expansiveness is better. PRM has a higher chance of discovering at least one passage.

### Image 2 — Epsilon-good and beta-lookout

**File:** `img2_lookout_definition.png`

![Lookout definition](img2_lookout_definition.png)

A two-chamber environment illustrates the key definitions:

- The **left chamber** is designated as subset $S$ (shaded blue).
- The **right chamber** is $F \setminus S$.
- The **green region** near the doorway is the $\beta$-lookout of $S$: points inside $S$ that have line-of-sight into $F \setminus S$ covering at least a $\beta$ fraction of $F \setminus S$.
- Green **arrows** show visibility lines from lookout points through the doorway into $F \setminus S$.

For the space to be $(\epsilon,\alpha,\beta)$-expansive, the $\beta$-lookout must occupy at least an $\alpha$ fraction of $S$ for every possible subset $S$.

### Image 3 — Failure probability curves

**File:** `img3_failure_probability_curves.png`

![Failure probability curves](img3_failure_probability_curves.png)

Three exponential decay curves $P_{\mathrm{fail}}(m) \approx e^{-k\,m}$ for different expansiveness levels:

| Curve | $k$ value | Meaning |
|-------|-----------|---------|
| **Green** (good) | $k = 0.012$ | Highly expansive — failure drops rapidly. A few hundred milestones suffice. |
| **Orange** (medium) | $k = 0.006$ | Moderate expansiveness — needs roughly twice as many milestones. |
| **Red** (poor) | $k = 0.0025$ | Narrow passages — failure stays high much longer; many milestones required. |

The chart highlights the **exponential** relationship: in expansive spaces, adding a modest number of milestones drastically improves reliability. In poorly expansive spaces, the same number of milestones barely helps.

### Image 4 — Milestones needed for target reliability

**File:** `img4_milestones_vs_expansiveness.png`

![Milestones vs expansiveness](img4_milestones_vs_expansiveness.png)

A bar chart based on the toy model $n \ge \frac{\ln(1/\delta)}{k}$ with target failure $\delta = 0.01$ (99\% success):

| Quality | $k$ | Milestones $n$ |
|---------|-----|----------------|
| Good | 0.012 | 384 |
| Medium | 0.006 | 768 |
| Poor | 0.0025 | 1843 |

Lower expansiveness requires **roughly 5× more milestones** to achieve the same reliability. In practice, $\epsilon$, $\alpha$, $\beta$ are hard to compute exactly, but this trend explains why narrow-passage worlds are fundamentally harder for PRM — and why smarter sampling strategies (Gaussian PRM, Bridge test, OBPRM) are needed.

### GIF summary

**File:** `expansiveness_overview.gif`

![Expansiveness overview](expansiveness_overview.gif)

An animated walkthrough cycling through a title card, all four figures above, and a summary of key takeaways. The animation has six frames with approximately 2.5 seconds per frame.

---

## Re-generate assets

Requirements:

- Python 3.9+
- `Pillow`

Install and run:

```bash
pip install pillow
python generate_expansiveness_demo.py
```

This regenerates all four PNGs and the overview GIF in this folder.
