# Visibility Graph vs Reduced Visibility Graph — Legacy Demo Notes

Gói này chứa bộ ảnh minh hoạ sớm cho **Visibility Graph (VG)** và một bản **Reduced VG**.
Nội dung vẫn hữu ích để xem trực quan, nhưng **không nên dùng làm kết luận cuối** cho RVG vì phiên bản này có giảm đồ thị quá mạnh và có thể mất tính liên thông.

Nếu cần bản đã kiểm chứng theo đúng ý bài giảng, dùng `visibility_graph_demo_v2/README.md`.

## Ký hiệu chung trong ảnh

- Vật cản: đa giác viền (không tô)
- **S**: start, **G**: goal
- Edge (cạnh đồ thị): các đoạn thẳng nối hai nút có line-of-sight
- Dấu **x** ở ảnh world: tập đỉnh được chọn trong bản thử nghiệm RVG của package này

## Các ảnh trong gói

### World layout with marked vertices

**File:** `01_world_reflex_vertices.png`

![World layout with marked vertices](01_world_reflex_vertices.png)

Môi trường gồm 2 obstacle đa giác, điểm start/goal, và các đỉnh được chọn cho thử nghiệm reduced graph.

### Full visibility graph

**File:** `02_visibility_graph_full.png`

![Full visibility graph](02_visibility_graph_full.png)

VG đầy đủ: nút $= \{S,G\} \cup V_{\text{obs}}$, nối cạnh khi đoạn thẳng giữa hai nút không đi vào nội thất obstacle.

### Reduced visibility graph (legacy attempt)

**File:** `03_visibility_graph_reduced.png`

![Reduced visibility graph](03_visibility_graph_reduced.png)

Đây là bản reduced graph theo heuristic cũ. Trong lần sinh ảnh này, reduced graph bị rỗng cạnh (không usable để tìm path), nên không đại diện cho RVG đúng theo lý thuyết.

### Shortest path on full VG (Dijkstra)

**File:** `04_shortest_path_full.png`

![Shortest path on full VG (Dijkstra)](04_shortest_path_full.png)

Dijkstra trên VG đầy đủ cho đường đi hợp lệ trong free space.

### Shortest path on reduced graph (legacy attempt)

**File:** `05_shortest_path_reduced.png`

![Shortest path on reduced graph (legacy attempt)](05_shortest_path_reduced.png)

Do reduced graph không đủ liên thông trong bản này, kết quả không dùng để so sánh tối ưu với full VG.

## Số liệu nhanh (ảnh legacy này)

- Full VG: nodes = 14, edges = 17
- Reduced graph: nodes = 4, edges = 0
- Không có cơ sở kết luận độ dài đường đi giữa full và reduced từ bộ ảnh này.

## Ghi chú học thuật

Theo lecture về reduced visibility graph, tập đỉnh giữ lại phải được chọn theo điều kiện hình học của đường tiếp xúc/supporting lines trong free space. Chọn sai tập đỉnh có thể làm đồ thị giảm quá mức và mất đường đi.
