# Moving Objects & Multi‑Robot Systems — CT‑space + Coordination Diagram (A* demo)

Package này minh họa **2 cách xử lý “moving obstacles” và “multi‑robot”** bằng cách *nâng bài toán lên không gian cấu hình mở rộng* rồi chạy **A\***:

- **Moving obstacle:** dùng **CT‑space** = $(s, t)$, với `s` là **tiến độ trên quỹ đạo** và `t` là **thời gian**.
- **Multi‑robot:** dùng **coordination diagram** = $(s_1, s_2)$, với $s_1, s_2$ là **tiến độ của robot 1/2**.

Điểm quan trọng: **không dùng greedy “đợi nếu sắp va chạm”**. Thay vào đó:
1) dựng **forbidden region** (vùng cấm va chạm) **offline** trên toàn không gian,  
2) chạy **A\*** để tìm đường **vòng qua** vùng cấm (lời giải toàn cục, nhất quán).

---

## Nội dung trong zip

- `1_moving_obstacle_ctspace.gif`  
  GIF 1 — Robot + **moving obstacle** (CT‑space planning).

- `2_multirobot_coordination.gif`  
  GIF 2 — **Two‑robot coordination** (coordination diagram planning).

- `run_astar_ctspace_and_coordination.py`  
  Script Python tạo ra 2 GIF (numpy + matplotlib + imageio).

---

## GIF 1 — Moving obstacle → CT‑space (s × t)

**Panel trái (Workspace):**
- Robot đi trên **đường ngang** từ start -> goal.
- Một obstacle hình tròn **quét theo trục y**, cắt ngang đường robot trong một “cửa sổ thời gian” (khoảng giữa).

**Panel phải (CT‑space):**
- Trục **x = thời gian t**, trục **y = tiến độ s**.
- Vùng **FORBIDDEN (collision)** là tập tất cả $(s,t)$ mà robot sẽ va chạm với obstacle.
- Đường nét đứt (A* plan) là **lời giải tối ưu rời rạc**: robot **tăng s nhanh trước khi obstacle tới** (hoặc có thể “đợi” — tùy hình forbidden).
- Chấm/đường màu xanh mô tả tiến trình thực thi theo thời gian, luôn **nằm ngoài vùng cấm**.

**Ý nghĩa:**  
Trong không gian $(s,t)$, “đợi” tương đương với **đi thẳng theo t** (tăng t, s giữ nguyên).  
“chạy nhanh” tương đương với **tăng s nhiều hơn mỗi bước t** (giới hạn bởi `MAX_SPEED`).

---

## GIF 2 — Multi‑robot → Coordination diagram (s1 × s2)

**Panel trái (Workspace):**
- Robot 1 đi ngang, robot 2 đi dọc -> hai đường đi **cắt nhau**.
- Vùng tròn nét đứt biểu diễn **khoảng cách an toàn D_SAFE** quanh điểm giao nhau.

**Panel phải (Coordination diagram):**
- Trục **x = s1**, trục **y = s2**.
- Vùng **FORBIDDEN (collision)** là tập $(s_1,s_2)$ sao cho $\|r_1(s_1)-r_2(s_2)\| < D_{\text{SAFE}}$.
- Đường nét đứt là **A\* schedule** đi từ $(0,0)$ -> $(1,1)$ **vòng quanh** vùng cấm.
  - Nếu đường đi **nằm trên đường chéo** ($s_2 > s_1$) -> robot 1 “chờ”, robot 2 đi trước.
  - Nếu đường đi **nằm dưới đường chéo** ($s_1 > s_2$) -> robot 2 “chờ”, robot 1 đi trước.

**Ý nghĩa:**  
Multi‑robot collision tránh bằng **điều phối tốc độ/tiến độ** (ai chờ, ai đi) — chính là “scheduling” trên $(s_1,s_2)$.

---

## Ghi chú (giới hạn mô hình)

- Đây là demo 2D đơn giản, robot đi theo **quỹ đạo cố định** (chỉ điều khiển tốc độ/tiến độ).
- Không xét động lực học chi tiết; chỉ có ràng buộc **monotone** (thời gian/tiến độ tăng) và giới hạn bước (tốc độ).
- Forbidden region được rời rạc hóa theo lưới, nên hình biên là “pixelated” (đúng về ý tưởng).

---

## Cách chạy lại script

```bash
pip install numpy matplotlib imageio
python run_astar_ctspace_and_coordination.py
```

Script sẽ tạo 2 GIF ở thư mục `./outputs/`.
