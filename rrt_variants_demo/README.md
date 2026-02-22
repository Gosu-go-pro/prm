# RRT Variants — Image Walkthrough (2D demo)

This package contains PNG images generated from a small **2D motion-planning world** (unit square, rectangular obstacles),
showing how different RRT-family planners build trees and find a collision-free path from **start (●)** to **goal (★)**.

## World & symbols used in the images

- **Start**: circular marker (●)
- **Goal**: star marker (★)
- **Obstacles**: filled rectangles (semi-transparent)
- **Tree edges**: line segments from each node to its parent
- **Path** (if found): thick polyline from start -> goal (built by following parent pointers)

### Extra symbols used in “One iteration anatomy” images

- **x_rand**: sampled point (×)
- **x_near**: nearest node in the current tree (■)
- **x_new**: new node produced by `steer(x_near -> x_rand, step)` (◆)

> Note: This demo uses a simple segment collision check by sampling a fixed number of points along each edge.

---

## RRT

- Grows **one tree** from start.
- Fast to find *some* path, but the path is not optimized.

### One iteration anatomy

**File:** `01_rrt_anatomy.png`


![One iteration anatomy](01_rrt_anatomy.png)


Minh hoạ 1 vòng lặp: lấy mẫu $x_{rand}$ (dấu x), chọn nút gần nhất $x_{near}$ (hình vuông), và tạo $x_{new}$ (hình thoi) bằng `steer` với `step` cố định; cạnh mới (đường đậm ngắn) chỉ được thêm nếu không va chạm.


### Snapshot 1 (nodes~100)

**File:** `02_rrt_snapshot_01_n100.png`


![Snapshot 1 (nodes~100)](02_rrt_snapshot_01_n100.png)


Cây RRT lan ra dần từ start. Các cạnh là quan hệ parent -> child (mỗi nút có đúng 1 parent).


### Snapshot 2 (nodes~300)

**File:** `02_rrt_snapshot_02_n300.png`


![Snapshot 2 (nodes~300)](02_rrt_snapshot_02_n300.png)


Cây RRT lan ra dần từ start. Các cạnh là quan hệ parent -> child (mỗi nút có đúng 1 parent).


### Final (tree + found path)

**File:** `03_rrt_final.png`


![Final (tree + found path)](03_rrt_final.png)


Khi có nút mới đủ gần goal (trong `goal_radius`) và nối thẳng đến goal không va chạm, thuật toán dừng và truy vết parent để lấy đường đi (đường đậm).



---

## RRT-Connect

- Grows **two trees** (from start and from goal).
- Tries to `connect` the other tree aggressively -> often finds a solution faster.

### One iteration anatomy (extend)

**File:** `11_rrt_connect_anatomy.png`


![One iteration anatomy (extend)](11_rrt_connect_anatomy.png)


Minh hoạ bước `extend(T_a, x_rand)`: giống RRT, nhưng RRT-Connect sẽ có 2 cây (từ start và từ goal) và cố gắng 'connect' cây còn lại tới điểm vừa mở rộng.


### Final (two trees + path if connected)

**File:** `13_rrt_connect_final.png`


![Final (two trees + path if connected)](13_rrt_connect_final.png)


Khi `connect(T_b, x_new)` đạt trạng thái `reached`, hai cây gặp nhau. Đường đi được ghép bằng cách truy vết parent từ điểm nối về start và về goal.



---

## RRT\*

- Like RRT but adds **cost-to-come** and **rewiring**.
- As nodes increase, the solution tends toward optimal (asymptotically).

### One iteration anatomy

**File:** `21_rrt_star_anatomy.png`


![One iteration anatomy](21_rrt_star_anatomy.png)


Minh hoạ bước tạo $x_{new}$. Khác RRT: sau khi có $x_{new}$, RRT\* sẽ xét tập lân cận (bán kính phụ thuộc số nút) để chọn parent có chi phí nhỏ nhất và sau đó 'rewire' các láng giềng nếu đi qua $x_{new}$ rẻ hơn.


### Snapshot 1 (nodes~150)

**File:** `22_rrt_star_snapshot_01_n150.png`


![Snapshot 1 (nodes~150)](22_rrt_star_snapshot_01_n150.png)


Cấu trúc cây 'thẳng hàng' hơn so với RRT vì có rewiring: nhiều node đổi parent theo thời gian để giảm tổng cost từ start.


### Final (tree + found path)

**File:** `23_rrt_star_final.png`


![Final (tree + found path)](23_rrt_star_final.png)


RRT\* tối ưu hoá dần đường đi nhờ chọn parent tốt hơn và rewiring. Với phiên bản demo này, thuật toán dừng ngay khi nối được goal lần đầu.



---

## Informed RRT\*

- After a first solution, samples are restricted to an **ellipse** defined by the current best path cost.
- Focuses search on regions that can improve the best solution faster.

### One iteration anatomy

**File:** `31_informed_rrt_star_anatomy.png`


![One iteration anatomy](31_informed_rrt_star_anatomy.png)


Giống RRT\*: có chọn parent tốt nhất + rewiring. Khác biệt: sau khi có lời giải, việc lấy mẫu sẽ bị giới hạn trong ellipse (prolate hyperspheroid) dựa trên `c_best` để tập trung vào vùng có thể cải thiện đường đi.


### Snapshot 1 (nodes~250)

**File:** `32_informed_rrt_star_snapshot_01_n250.png`


![Snapshot 1 (nodes~250)](32_informed_rrt_star_snapshot_01_n250.png)


Nếu `c_best` đã hữu hạn (đã có lời giải), bạn sẽ thấy mẫu và cây tập trung hơn quanh 'hành lang' từ start -> goal.


### Snapshot 2 (nodes~900)

**File:** `32_informed_rrt_star_snapshot_02_n900.png`


![Snapshot 2 (nodes~900)](32_informed_rrt_star_snapshot_02_n900.png)


Nếu `c_best` đã hữu hạn (đã có lời giải), bạn sẽ thấy mẫu và cây tập trung hơn quanh 'hành lang' từ start -> goal.


### Snapshot 3 (nodes~2000)

**File:** `32_informed_rrt_star_snapshot_03_n2000.png`


![Snapshot 3 (nodes~2000)](32_informed_rrt_star_snapshot_03_n2000.png)


Nếu `c_best` đã hữu hạn (đã có lời giải), bạn sẽ thấy mẫu và cây tập trung hơn quanh 'hành lang' từ start -> goal.


### Final (tree + best path)

**File:** `33_informed_rrt_star_final.png`


![Final (tree + best path)](33_informed_rrt_star_final.png)


Sau khi có lời giải đầu tiên, informed sampling sẽ cố 'siết' không gian lấy mẫu vào ellipse dựa trên đường đi tốt nhất hiện tại, thường cải thiện chất lượng nhanh hơn RRT\* thuần.



---
