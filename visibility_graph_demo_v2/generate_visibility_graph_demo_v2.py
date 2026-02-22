#!/usr/bin/env python3
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

EPS = 1e-9

def poly_area(poly):
    s = 0.0
    n = len(poly)
    for i in range(n):
        x1,y1 = poly[i]
        x2,y2 = poly[(i+1)%n]
        s += x1*y2 - x2*y1
    return 0.5*s

def ensure_ccw(poly):
    return poly if poly_area(poly) > 0 else list(reversed(poly))

def orient(p,q,r):
    return (q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0])

def on_segment(a,p,b):
    return (min(a[0],b[0]) - 1e-8 <= p[0] <= max(a[0],b[0]) + 1e-8 and
            min(a[1],b[1]) - 1e-8 <= p[1] <= max(a[1],b[1]) + 1e-8 and
            abs(orient(a,p,b)) <= 1e-8)

def seg_intersect(a,b,c,d):
    o1 = orient(a,b,c)
    o2 = orient(a,b,d)
    o3 = orient(c,d,a)
    o4 = orient(c,d,b)
    if (o1*o2 < -1e-12) and (o3*o4 < -1e-12):
        return True
    if abs(o1) <= 1e-8 and on_segment(a,c,b): return True
    if abs(o2) <= 1e-8 and on_segment(a,d,b): return True
    if abs(o3) <= 1e-8 and on_segment(c,a,d): return True
    if abs(o4) <= 1e-8 and on_segment(c,b,d): return True
    return False

def point_on_poly_boundary(pt, poly):
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i+1)%n]
        if on_segment(a, pt, b):
            return True
    return False

def point_in_poly_strict(pt, poly):
    if point_on_poly_boundary(pt, poly):
        return False
    x,y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1,y1 = poly[i]
        x2,y2 = poly[(i+1)%n]
        if (y1 > y) != (y2 > y):
            xinters = (x2-x1)*(y-y1) / (y2-y1 + 1e-30) + x1
            if x < xinters:
                inside = not inside
    return inside

def is_vertex(pt, poly):
    for v in poly:
        if np.allclose(pt, v, atol=1e-8):
            return True
    return False

def visible(p, q, obstacles):
    mid = ((p[0]+q[0])/2.0, (p[1]+q[1])/2.0)
    for poly in obstacles:
        if point_in_poly_strict(mid, poly):
            return False
        n = len(poly)
        for i in range(n):
            a = poly[i]
            b = poly[(i+1)%n]
            if seg_intersect(p, q, a, b):
                allow = False
                if is_vertex(p, poly) and on_segment(a, p, b):
                    allow = True
                if is_vertex(q, poly) and on_segment(a, q, b):
                    allow = True
                if (point_on_poly_boundary(p, poly) and on_segment(a, p, b)) or (point_on_poly_boundary(q, poly) and on_segment(a, q, b)):
                    allow = True
                if not allow:
                    return False
    return True

def turning_vertices_for_shortest_paths(poly_ccw):
    n = len(poly_ccw)
    keep = []
    concave = []
    for i in range(n):
        prev = np.array(poly_ccw[(i-1)%n], float)
        curr = np.array(poly_ccw[i], float)
        nxt  = np.array(poly_ccw[(i+1)%n], float)
        v1 = curr - prev
        v2 = nxt - curr
        cross = v1[0]*v2[1] - v1[1]*v2[0]
        if cross > 1e-8:
            keep.append(i)      # convex obstacle vertex = free-space reflex
        elif cross < -1e-8:
            concave.append(i)   # concave obstacle vertex
    return keep, concave

def euclid(a,b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def dijkstra(pts, edges, s_idx=0, g_idx=1):
    n = len(pts)
    adj = [[] for _ in range(n)]
    for i,j in edges:
        w = euclid(pts[i], pts[j])
        adj[i].append((j,w))
        adj[j].append((i,w))
    import heapq
    dist = [float("inf")]*n
    parent = [-1]*n
    dist[s_idx] = 0.0
    pq = [(0.0, s_idx)]
    seen = set()
    while pq:
        d,u = heapq.heappop(pq)
        if u in seen:
            continue
        seen.add(u)
        if u == g_idx:
            break
        for v,w in adj[u]:
            nd = d + w
            if nd + 1e-12 < dist[v]:
                dist[v] = nd
                parent[v] = u
                heapq.heappush(pq, (nd, v))
    if not math.isfinite(dist[g_idx]):
        return None, float("inf")
    path=[]
    cur=g_idx
    while cur!=-1:
        path.append(cur)
        cur=parent[cur]
    path.reverse()
    return path, dist[g_idx]

def idx_to_path(pts, idxs):
    if idxs is None:
        return None
    return [pts[i] for i in idxs]

def save_fig(fig, filename):
    fig.tight_layout()
    fig.savefig(filename, dpi=170)
    plt.close(fig)

def main():
    # Environment
    obs1 = ensure_ccw([(2,1),(4,1),(4,3),(3,2.1),(2,3)])
    obs2 = ensure_ccw([(6,1.2),(8,1.2),(8,3.2),(6,3.2)])
    obstacles = [obs1, obs2]
    S = (1.0, 0.7)
    G = (9.2, 4.1)
    xlim=(0,10); ylim=(0,5.0)

    # Full nodes
    all_vertices=[]
    meta_full=[]
    for oi, poly in enumerate(obstacles):
        for vi, v in enumerate(poly):
            all_vertices.append(tuple(v))
            meta_full.append((oi,vi))
    pts_full=[S,G]+all_vertices
    labels_full=["S","G"]+[f"{oi}:{vi}" for (oi,vi) in meta_full]

    edges_full=[]
    for i in range(len(pts_full)):
        for j in range(i+1, len(pts_full)):
            if visible(pts_full[i], pts_full[j], obstacles):
                edges_full.append((i,j))

    # Reduced nodes (K vertices)
    kept_vertices=[]
    meta_kept=[]
    concave_vertices=[]
    meta_concave=[]
    for oi, poly in enumerate(obstacles):
        keep, conc = turning_vertices_for_shortest_paths(poly)
        for vi in keep:
            kept_vertices.append(tuple(poly[vi]))
            meta_kept.append((oi,vi))
        for vi in conc:
            concave_vertices.append(tuple(poly[vi]))
            meta_concave.append((oi,vi))

    pts_red=[S,G]+kept_vertices
    labels_red=["S","G"]+[f"K{oi}:{vi}" for (oi,vi) in meta_kept]

    edges_red=[]
    for i in range(len(pts_red)):
        for j in range(i+1, len(pts_red)):
            if visible(pts_red[i], pts_red[j], obstacles):
                edges_red.append((i,j))

    # paths
    path_full_idx, len_full = dijkstra(pts_full, edges_full)
    path_red_idx,  len_red  = dijkstra(pts_red,  edges_red)
    path_full = idx_to_path(pts_full, path_full_idx)
    path_red  = idx_to_path(pts_red,  path_red_idx)

    def draw_obstacles(ax):
        for poly in obstacles:
            ax.add_patch(Polygon(poly, closed=True, fill=False, linewidth=2))
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.grid(True, alpha=0.2)

    def plot_world(ax):
        draw_obstacles(ax)
        ax.scatter([S[0]],[S[1]], s=70)
        ax.scatter([G[0]],[G[1]], s=70)
        ax.text(S[0]+0.06, S[1]+0.06, "S", fontsize=10)
        ax.text(G[0]+0.06, G[1]+0.06, "G", fontsize=10)

    def plot_graph(ax, pts, edges, labels, title):
        draw_obstacles(ax)
        for i,j in edges:
            ax.plot([pts[i][0], pts[j][0]], [pts[i][1], pts[j][1]], linewidth=0.8, alpha=0.9)
        ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=40)
        for p,lab in zip(pts, labels):
            ax.text(p[0]+0.06, p[1]+0.06, lab, fontsize=9)
        ax.set_title(title)

    def plot_path(ax, path_pts, title, subtitle=None):
        draw_obstacles(ax)
        if path_pts:
            ax.plot([p[0] for p in path_pts], [p[1] for p in path_pts], linewidth=3.0)
            ax.scatter([p[0] for p in path_pts], [p[1] for p in path_pts], s=55)
        ax.scatter([S[0], G[0]], [S[1], G[1]], s=70)
        ax.text(S[0]+0.06, S[1]+0.06, "S", fontsize=10)
        ax.text(G[0]+0.06, G[1]+0.06, "G", fontsize=10)
        ax.set_title(title)
        if subtitle:
            ax.set_xlabel(subtitle)

    # 01
    fig=plt.figure(figsize=(7.4,4.8))
    ax=plt.gca()
    plot_world(ax)
    if kept_vertices:
        ax.scatter([p[0] for p in kept_vertices], [p[1] for p in kept_vertices], s=70, marker='x')
        for p,(oi,vi) in zip(kept_vertices, meta_kept):
            ax.text(p[0]+0.06, p[1]-0.14, f"K{oi}:{vi}", fontsize=9)
    if concave_vertices:
        ax.scatter([p[0] for p in concave_vertices], [p[1] for p in concave_vertices], s=85, marker='+')
        for p,(oi,vi) in zip(concave_vertices, meta_concave):
            ax.text(p[0]+0.06, p[1]+0.10, f"C{oi}:{vi}", fontsize=9)
    ax.set_title("World: obstacles + S,G + vertex classes (K=kept, C=concave obstacle vertex)")
    save_fig(fig, "01_world_vertex_classes.png")

    # 02
    fig=plt.figure(figsize=(7.4,4.8))
    ax=plt.gca()
    plot_graph(ax, pts_full, edges_full, labels_full, "Full Visibility Graph (S,G + all obstacle vertices)")
    save_fig(fig, "02_full_visibility_graph.png")

    # 03
    fig=plt.figure(figsize=(7.4,4.8))
    ax=plt.gca()
    plot_graph(ax, pts_red, edges_red, labels_red, "Reduced Visibility Graph (S,G + K vertices only)")
    save_fig(fig, "03_reduced_visibility_graph.png")

    # 04
    fig=plt.figure(figsize=(7.4,4.8))
    ax=plt.gca()
    plot_path(ax, path_full, "Shortest path on full VG (Dijkstra)",
              subtitle=f"edges={len(edges_full)} | nodes={len(pts_full)} | length≈{len_full:.3f} | hops={len(path_full_idx) if path_full_idx else 0}")
    save_fig(fig, "04_shortest_path_full.png")

    # 05
    fig=plt.figure(figsize=(7.4,4.8))
    ax=plt.gca()
    plot_path(ax, path_red, "Shortest path on reduced VG (Dijkstra)",
              subtitle=f"edges={len(edges_red)} | nodes={len(pts_red)} | length≈{len_red:.3f} | hops={len(path_red_idx) if path_red_idx else 0}")
    save_fig(fig, "05_shortest_path_reduced.png")

    # 06
    fig=plt.figure(figsize=(7.4,4.8))
    ax=plt.gca()
    draw_obstacles(ax)
    if path_full:
        ax.plot([p[0] for p in path_full], [p[1] for p in path_full], linewidth=3.0, linestyle='-')
    if path_red:
        ax.plot([p[0] for p in path_red], [p[1] for p in path_red], linewidth=2.2, linestyle='--')
    ax.scatter([S[0],G[0]],[S[1],G[1]], s=70)
    ax.text(S[0]+0.06, S[1]+0.06, "S", fontsize=10)
    ax.text(G[0]+0.06, G[1]+0.06, "G", fontsize=10)
    ax.set_title("Path comparison: full VG (solid) vs reduced VG (dashed)")
    ax.set_xlabel(f"length_full≈{len_full:.3f} | length_reduced≈{len_red:.3f}")
    save_fig(fig, "06_path_comparison.png")

    print("Full VG: nodes", len(pts_full), "edges", len(edges_full), "path length", len_full)
    print("Reduced VG: nodes", len(pts_red), "edges", len(edges_red), "path length", len_red)

if __name__ == "__main__":
    main()
