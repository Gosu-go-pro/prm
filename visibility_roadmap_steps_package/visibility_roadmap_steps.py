import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from pathlib import Path
import math, heapq
from PIL import Image

np.random.seed(42)

XMIN, XMAX = 0.0, 10.0
YMIN, YMAX = 0.0, 7.0

# ── Environment (C-space obstacles) ──────────────────────────────────────────
obstacles = [
    [(2.0, 1.0), (4.0, 1.0), (4.0, 3.8), (2.0, 3.8)],   # Obs A (left block)
    [(6.0, 3.2), (8.5, 3.2), (8.5, 5.8), (6.0, 5.8)],   # Obs B (right-top)
    [(5.0, 0.6), (6.6, 0.6), (6.6, 2.0), (5.0, 2.0)],   # Obs C (right-bottom)
]
start = (0.9, 0.9)
goal  = (9.2, 6.2)

# ── Geometry helpers ─────────────────────────────────────────────────────────
def orient(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

def on_segment(a, b, c, eps=1e-9):
    return (min(a[0], b[0])-eps <= c[0] <= max(a[0], b[0])+eps and
            min(a[1], b[1])-eps <= c[1] <= max(a[1], b[1])+eps)

def segments_intersect(p1, p2, q1, q2):
    o1,o2,o3,o4 = orient(p1,p2,q1),orient(p1,p2,q2),orient(q1,q2,p1),orient(q1,q2,p2)
    eps = 1e-9
    def sgn(x): return 0 if abs(x)<eps else (1 if x>0 else -1)
    s1,s2,s3,s4 = map(sgn,(o1,o2,o3,o4))
    if s1*s2<0 and s3*s4<0: return True
    if s1==0 and on_segment(p1,p2,q1): return True
    if s2==0 and on_segment(p1,p2,q2): return True
    if s3==0 and on_segment(q1,q2,p1): return True
    if s4==0 and on_segment(q1,q2,p2): return True
    return False

def point_in_poly(pt, poly):
    x,y = pt; inside = False; n=len(poly); eps=1e-9
    for i in range(n):
        a=poly[i]; b=poly[(i+1)%n]
        if abs(orient(a,b,pt))<eps and on_segment(a,b,pt,eps): return True
        (x1,y1),(x2,y2)=a,b
        if (y1>y)!=(y2>y):
            xi = x1+(y-y1)*(x2-x1)/(y2-y1)
            if xi>x: inside=not inside
    return inside

def in_collision(pt):
    return any(point_in_poly(pt,poly) for poly in obstacles)

def segment_free(a, b, steps=20):
    # True if segment a->b is collision-free.
    if in_collision(a) or in_collision(b): return False
    for poly in obstacles:
        n=len(poly)
        for i in range(n):
            if segments_intersect(a,b,poly[i],poly[(i+1)%n]): return False
        # discretized interior check
        for t in np.linspace(0,1,steps+1):
            mid=((a[0]*(1-t)+b[0]*t),(a[1]*(1-t)+b[1]*t))
            if point_in_poly(mid,poly): return False
    return True

def sample_free(n):
    pts=[]; att=0
    while len(pts)<n and att<500000:
        att+=1
        p=(np.random.uniform(XMIN,XMAX),np.random.uniform(YMIN,YMAX))
        if not in_collision(p): pts.append(p)
    return pts

def euclid(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])

# ── Milestones ───────────────────────────────────────────────────────────────
extra = sample_free(18)
V = [start, goal] + extra   # index 0=start, 1=goal

# Output dir (local)
outdir = Path(__file__).resolve().parent / "outputs"
outdir.mkdir(parents=True, exist_ok=True)

# ── Style ────────────────────────────────────────────────────────────────────
OBS_COLOR   = "#4a90d9"
OBS_ALPHA   = 0.30
NODE_COLOR  = "#2c3e50"
START_COLOR = "#27ae60"
GOAL_COLOR  = "#e74c3c"
EDGE_COLOR  = "#7f8c8d"
TESTED_OK   = "#27ae60"
TESTED_BLOCKED = "#e74c3c"
PATH_COLOR  = "#f39c12"
BG_COLOR    = "#fafafa"

def base_fig(title="", figsize=(9,6)):
    fig, ax = plt.subplots(figsize=figsize, facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    patches = [MplPolygon(np.array(poly), closed=True) for poly in obstacles]
    pc = PatchCollection(patches, facecolor=OBS_COLOR, alpha=OBS_ALPHA, edgecolor="#2980b9", linewidth=1.5)
    ax.add_collection(pc)
    ax.set_xlim(XMIN-0.2, XMAX+0.2)
    ax.set_ylim(YMIN-0.2, YMAX+0.2)
    ax.set_aspect("equal")
    ax.grid(True, linewidth=0.4, alpha=0.4, color="#bdc3c7")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("x (config space)", fontsize=10)
    ax.set_ylabel("y (config space)", fontsize=10)
    return fig, ax

def draw_edges(ax, V, E):
    for (i,j) in E:
        a,b=V[i],V[j]
        ax.plot([a[0],b[0]],[a[1],b[1]], color=EDGE_COLOR, linewidth=1.1, alpha=0.6, zorder=2)

def draw_nodes(ax, V):
    for idx,(x,y) in enumerate(V):
        if idx==0:
            ax.scatter(x,y,s=120,color=START_COLOR,zorder=5,edgecolors="white",linewidths=1.5)
            ax.text(x+0.12,y+0.12,"S",fontsize=11,fontweight="bold",color=START_COLOR,zorder=6)
        elif idx==1:
            ax.scatter(x,y,s=120,color=GOAL_COLOR,zorder=5,edgecolors="white",linewidths=1.5)
            ax.text(x+0.12,y+0.12,"G",fontsize=11,fontweight="bold",color=GOAL_COLOR,zorder=6)
        else:
            ax.scatter(x,y,s=60,color=NODE_COLOR,zorder=5,edgecolors="white",linewidths=1)

def add_legend(ax, extras=None):
    handles = [
        mpatches.Patch(facecolor=OBS_COLOR, alpha=0.5, label="Obstacle (C_obs)"),
        Line2D([0],[0],color=EDGE_COLOR,lw=1.5,label="Collision-free edge"),
        Line2D([0],[0],marker='o',color='w',markerfacecolor=START_COLOR,markersize=9,label="Start (S)"),
        Line2D([0],[0],marker='o',color='w',markerfacecolor=GOAL_COLOR,markersize=9,label="Goal (G)"),
        Line2D([0],[0],marker='o',color='w',markerfacecolor=NODE_COLOR,markersize=8,label="Milestone"),
    ]
    if extras: handles += extras
    ax.legend(handles=handles, loc="upper left", fontsize=8, framealpha=0.85)

saved = []

# Step 1: environment
fig, ax = base_fig("Step 1 — Define C-space Environment\n(C_free = white, C_obs = blue rectangles)")
labels = ["Obs A\n(left block)", "Obs B\n(right-top)", "Obs C\n(right-bottom)"]
centers = [(3.0,2.4),(7.25,4.5),(5.8,1.3)]
for lbl,cen in zip(labels,centers):
    ax.text(cen[0],cen[1],lbl,ha="center",va="center",fontsize=8.5,color="#1a5276",fontweight="bold")
ax.scatter(*start,s=140,color=START_COLOR,zorder=5,edgecolors="white",linewidths=1.5); ax.text(start[0]+0.15,start[1]+0.12,"S",fontsize=12,fontweight="bold",color=START_COLOR)
ax.scatter(*goal, s=140,color=GOAL_COLOR, zorder=5,edgecolors="white",linewidths=1.5); ax.text(goal[0]+0.12, goal[1]+0.12,"G",fontsize=12,fontweight="bold",color=GOAL_COLOR)
add_legend(ax)
p=outdir/"step01_environment.png"; fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig); saved.append(p)

# Step 2: init graph (S,G)
V2 = [start, goal]
fig, ax = base_fig("Step 2 — Initialise Graph with Mandatory Milestones\nV = {q_start, q_goal},  E = ∅")
draw_nodes(ax, V2)
ax.annotate("Mandatory\nmilestone", xy=start, xytext=(start[0]+0.8,start[1]+1.2), arrowprops=dict(arrowstyle="->",color=START_COLOR), fontsize=9, color=START_COLOR)
ax.annotate("Mandatory\nmilestone", xy=goal,  xytext=(goal[0]-2.5,goal[1]-1.0), arrowprops=dict(arrowstyle="->",color=GOAL_COLOR), fontsize=9, color=GOAL_COLOR)
add_legend(ax)
p=outdir/"step02_init_graph.png"; fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig); saved.append(p)

# Step 3: samples
fig, ax = base_fig(f"Step 3 — Sample {len(extra)} Random Milestones in C_free\nV = {{q_start, q_goal}} ∪ {{q_2,...,q_{len(V)-1}}},  E = ∅")
draw_nodes(ax, V)
rect = plt.Rectangle((XMIN,YMIN),XMAX-XMIN,YMAX-YMIN, fill=False, edgecolor="#27ae60", linewidth=2, linestyle="--", alpha=0.5)
ax.add_patch(rect); ax.text(5,6.6,"Sampling region C_free",ha="center",fontsize=9,color="#27ae60",style="italic")
add_legend(ax)
p=outdir/"step03_sample_milestones.png"; fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig); saved.append(p)

# Step 4a: blocked S-G
fig, ax = base_fig("Step 4a — Visibility Test: Edge BLOCKED\nLine(q_start, q_goal) ∩ C_obs ≠ ∅  →  reject edge")
draw_nodes(ax, V)
ax.plot([start[0],goal[0]],[start[1],goal[1]], color=TESTED_BLOCKED, linewidth=2.5, linestyle="--", zorder=4)
ax.text(5.0,3.8,"✗ BLOCKED\n(passes through obstacle)", ha="center", fontsize=11, color=TESTED_BLOCKED, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3",facecolor="white",edgecolor=TESTED_BLOCKED,alpha=0.85))
add_legend(ax, [Line2D([0],[0],color=TESTED_BLOCKED,lw=2,linestyle="--",label="Tested (BLOCKED)")])
p=outdir/"step04a_blocked_edge.png"; fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig); saved.append(p)

# Step 4b: accepted example pair
clear_pair=None
for i in range(2,len(V)):
    for j in range(i+1,len(V)):
        if euclid(V[i],V[j])<3.0 and segment_free(V[i],V[j]):
            clear_pair=(i,j); break
    if clear_pair: break

fig, ax = base_fig("Step 4b — Visibility Test: Edge ACCEPTED\nLine(qi, qj) ∩ C_obs = ∅  →  add edge")
draw_nodes(ax, V)
if clear_pair:
    a,b=V[clear_pair[0]],V[clear_pair[1]]
    ax.plot([a[0],b[0]],[a[1],b[1]],color=TESTED_OK,linewidth=2.5,zorder=4)
    mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
    ax.text(mid[0]+0.2,mid[1]+0.25,"✓ ACCEPTED\n(collision-free)", fontsize=10, color=TESTED_OK, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3",facecolor="white",edgecolor=TESTED_OK,alpha=0.85))
add_legend(ax, [Line2D([0],[0],color=TESTED_OK,lw=2.5,label="Tested (ACCEPTED)")])
p=outdir/"step04b_accepted_edge.png"; fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig); saved.append(p)

# Step 5: all-pairs roadmap
E=[]
N=len(V)
for i in range(N):
    for j in range(i+1,N):
        if segment_free(V[i],V[j]):
            E.append((i,j))

fig, ax = base_fig(f"Step 5 — Build Complete Roadmap (All-Pairs Visibility)\n|V|={N} nodes,  |E|={len(E)} collision-free edges")
draw_edges(ax, V, E); draw_nodes(ax, V); add_legend(ax)
ax.text(5.0,-0.15,f"All {N*(N-1)//2} pairs tested → {len(E)} edges accepted", ha="center", fontsize=9, color="#555", style="italic")
p=outdir/"step05_full_roadmap.png"; fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig); saved.append(p)

# Step 6: Dijkstra
adj=[[] for _ in range(N)]
for i,j in E:
    w=euclid(V[i],V[j]); adj[i].append((j,w)); adj[j].append((i,w))

def dijkstra(src,dst):
    dist=[float("inf")]*N; prev=[-1]*N; dist[src]=0.0
    pq=[(0.0,src)]
    while pq:
        d,u=heapq.heappop(pq)
        if d!=dist[u]: continue
        if u==dst: break
        for v,w in adj[u]:
            nd=d+w
            if nd<dist[v]: dist[v]=nd; prev[v]=u; heapq.heappush(pq,(nd,v))
    if dist[dst]==float("inf"): return None,None
    path=[]; cur=dst
    while cur!=-1: path.append(cur); cur=prev[cur]
    path.reverse()
    return path,dist[dst]

path,cost=dijkstra(0,1)

fig, ax = base_fig(f"Step 6 — Graph Search (Dijkstra): Shortest Path Found\nPath length ≈ {cost:.2f} through {len(path)} waypoints")
draw_edges(ax, V, E); draw_nodes(ax, V)
if path:
    px=[V[n][0] for n in path]; py=[V[n][1] for n in path]
    ax.plot(px,py,color=PATH_COLOR,linewidth=4.5,zorder=6,solid_capstyle="round")
    for step,(xi,yi) in enumerate(zip(px,py)):
        ax.text(xi+0.1,yi+0.15,str(step),fontsize=8,color=PATH_COLOR,fontweight="bold",zorder=7)
add_legend(ax, [Line2D([0],[0],color=PATH_COLOR,lw=4,label=f"Shortest path (≈{cost:.2f})")])
p=outdir/"step06_shortest_path.png"; fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig); saved.append(p)

# Step 7: final summary
fig, ax = base_fig("Final — Visibility Roadmap Summary\nG = (V, E): nodes = safe configs, edges = collision-free LOS")
draw_edges(ax, V, E)
if path:
    px=[V[n][0] for n in path]; py=[V[n][1] for n in path]
    ax.plot(px,py,color=PATH_COLOR,linewidth=5,zorder=6,solid_capstyle="round",alpha=0.9)
draw_nodes(ax, V)
info=(f"Milestones |V| = {N}\n"
      f"Edges      |E| = {len(E)}\n"
      f"Path nodes      = {len(path)}\n"
      f"Path length ≈ {cost:.2f}")
ax.text(0.02,0.02,info, transform=ax.transAxes, fontsize=9, verticalalignment="bottom",
        bbox=dict(boxstyle="round,pad=0.5",facecolor="white",edgecolor="#aaa",alpha=0.9))
add_legend(ax, [Line2D([0],[0],color=PATH_COLOR,lw=4,label=f"Optimal path (≈{cost:.2f})")])
p=outdir/"step07_final_summary.png"; fig.savefig(p,dpi=160,bbox_inches="tight"); plt.close(fig); saved.append(p)

# GIF
frames=[Image.open(p).convert("RGBA") for p in saved]
gif_path=outdir/"visibility_roadmap_steps.gif"
frames[0].save(gif_path, save_all=True, append_images=frames[1:]+[frames[-1],frames[-1]],
               duration=1200, loop=0, optimize=False)

print("Done.")
print("Outputs:", outdir)
print(f"Stats: |V|={N}, |E|={len(E)}, path_len={cost:.2f}, path_nodes={len(path)}")
