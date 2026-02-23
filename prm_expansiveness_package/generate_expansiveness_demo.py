#!/usr/bin/env python3
"""Generate didactic images for PRM expansiveness (Question 16).

Images focus on clear visual diagrams with minimal in-image text.
Detailed explanations belong in README.md.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

OUT = Path(__file__).resolve().parent
W, H = 1400, 900
BG = (248, 250, 252)
PANEL_BG = (255, 255, 255)
OBST = (64, 85, 117)
BORDER = (120, 144, 156)
BLUE = (41, 128, 185)
GREEN = (46, 204, 113)
ORANGE = (230, 126, 34)
RED = (192, 57, 43)
PURPLE = (142, 68, 173)
TEXT = (33, 37, 41)
MUTED = (93, 109, 126)
LIGHT_BLUE = (245, 251, 255)
BLUE_LINE = (52, 152, 219)


def load_font(size, bold=False):
    candidates = []
    if bold:
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        ])
    else:
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ])
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT_H1 = load_font(38, bold=True)
FONT_H2 = load_font(28, bold=True)
FONT_H3 = load_font(20, bold=True)
FONT_BODY = load_font(18)
FONT_SMALL = load_font(16)


def text_width(draw, txt, font):
    return draw.textbbox((0, 0), txt, font=font)[2]


def draw_centered(draw, x0, x1, y, txt, font, fill=TEXT):
    tw = text_width(draw, txt, font)
    draw.text((x0 + (x1 - x0 - tw) / 2, y), txt, font=font, fill=fill)


def rounded_rect(draw, xy, r=14, fill=None, outline=None, width=2):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def draw_workspace_box(draw, x0, y0, x1, y1, title):
    """Draw a rounded panel with a short title that fits inside."""
    rounded_rect(draw, (x0, y0, x1, y1), r=14, fill=(252, 253, 255),
                 outline=BORDER, width=2)
    draw_centered(draw, x0, x1, y0 + 8, title, FONT_H3)


# ── Image 1: Three geometry cases ──────────────────────────────────────

def _draw_convex_room(draw, x0, y0, x1, y1):
    """Convex free-space room with scattered samples."""
    draw.rectangle((x0, y0, x1, y1), fill=LIGHT_BLUE, outline=BLUE_LINE,
                   width=2)
    w, h = x1 - x0, y1 - y0
    offsets_x = [15, -10, 20, -15, 8, -12, 5, -8, 18, -5, 10, -18]
    offsets_y = [10, -15, 8, 20, -10, 5, -12, 15, -8, 18, -5, 12]
    for row in range(4):
        for col in range(3):
            cx = x0 + int(w * (col + 0.5) / 3)
            cy = y0 + int(h * (row + 0.5) / 4)
            idx = row * 3 + col
            px = max(x0 + 6, min(x1 - 6, cx + offsets_x[idx]))
            py = max(y0 + 6, min(y1 - 6, cy + offsets_y[idx]))
            draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=BLUE)


def _draw_narrow_room(draw, x0, y0, x1, y1):
    """Room divided by a wall with a single narrow passage."""
    draw.rectangle((x0, y0, x1, y1), fill=LIGHT_BLUE, outline=BLUE_LINE,
                   width=2)
    mid = (x0 + x1) // 2
    h = y1 - y0
    gap_top = y0 + int(h * 0.42)
    gap_bot = gap_top + int(h * 0.08)
    draw.rectangle((mid - 14, y0 + 2, mid + 14, gap_top), fill=OBST)
    draw.rectangle((mid - 14, gap_bot, mid + 14, y1 - 2), fill=OBST)
    draw.rectangle((mid - 17, gap_top - 2, mid + 17, gap_bot + 2),
                   outline=RED, width=2)
    # Samples in left chamber
    for frac in [0.15, 0.35, 0.55, 0.75, 0.90]:
        cx = x0 + (mid - x0) // 2 + [-15, 20, -10, 15, -8][int(frac * 20) % 5]
        cy = y0 + int(h * frac)
        draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=BLUE)
    # Samples in right chamber
    for frac in [0.20, 0.45, 0.70, 0.85]:
        cx = mid + (x1 - mid) // 2 + [12, -18, 10, -14][int(frac * 20) % 4]
        cy = y0 + int(h * frac)
        draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=BLUE)


def _draw_multi_room(draw, x0, y0, x1, y1):
    """Room with multiple moderate passages."""
    draw.rectangle((x0, y0, x1, y1), fill=LIGHT_BLUE, outline=BLUE_LINE,
                   width=2)
    mid = (x0 + x1) // 2
    h = y1 - y0
    seg = h // 5
    draw.rectangle((mid - 14, y0 + 2, mid + 14, y0 + seg), fill=OBST)
    draw.rectangle((mid - 14, y0 + 2 * seg, mid + 14, y0 + 3 * seg),
                   fill=OBST)
    draw.rectangle((mid - 14, y0 + 4 * seg, mid + 14, y1 - 2), fill=OBST)
    # Green dots at passage centres
    for gap_y in [y0 + int(1.5 * seg), y0 + int(3.5 * seg)]:
        draw.ellipse((mid - 5, gap_y - 5, mid + 5, gap_y + 5), fill=GREEN)
    # Samples in each half
    for frac in [0.12, 0.35, 0.58, 0.80]:
        for sign in [-1, 1]:
            cx = mid + sign * (x1 - mid) // 2
            ox = [10, -8, 14, -12][int(frac * 10) % 4] * sign
            cy = y0 + int(h * frac)
            draw.ellipse((cx + ox - 4, cy - 4, cx + ox + 4, cy + 4),
                         fill=BLUE)


def make_img1():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_centered(draw, 0, W, 24, "Expansiveness: Three Geometry Cases",
                  FONT_H1)

    pad, gap = 40, 24
    top, bottom = 86, H - 40
    pw = (W - 2 * pad - 2 * gap) // 3

    for i, (title, fn) in enumerate([
        ("A: Convex", _draw_convex_room),
        ("B: Narrow passage", _draw_narrow_room),
        ("C: Multiple passages", _draw_multi_room),
    ]):
        x0 = pad + i * (pw + gap)
        x1 = x0 + pw
        draw_workspace_box(draw, x0, top, x1, bottom, title)
        fn(draw, x0 + 20, top + 44, x1 - 20, bottom - 20)

    out = OUT / "img1_expansiveness_cases.png"
    img.save(out)
    return out


# ── Image 2: epsilon-good and beta-lookout (full-width) ────────────────

def make_img2():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_centered(draw, 0, W, 20, "Lookout Definition", FONT_H1)
    draw_centered(draw, 0, W, 68,
                  "Subset S with its beta-lookout near the doorway",
                  FONT_BODY, fill=MUTED)

    x0, y0, x1, y1 = 80, 120, W - 80, H - 60
    draw_workspace_box(draw, x0, y0, x1, y1,
                       "Two chambers connected by a doorway")

    mx0, my0 = x0 + 20, y0 + 50
    mx1, my1 = x1 - 20, y1 - 20
    draw.rectangle((mx0, my0, mx1, my1), fill=LIGHT_BLUE,
                   outline=BLUE_LINE, width=2)

    wall_x = (mx0 + mx1) // 2
    door_top = my0 + int((my1 - my0) * 0.35)
    door_bot = door_top + int((my1 - my0) * 0.14)
    draw.rectangle((wall_x - 20, my0 + 2, wall_x + 20, door_top), fill=OBST)
    draw.rectangle((wall_x - 20, door_bot, wall_x + 20, my1 - 2), fill=OBST)

    # Shade S (left chamber)
    draw.rectangle((mx0 + 2, my0 + 2, wall_x - 20, my1 - 2),
                   fill=(217, 237, 255))
    draw.text((mx0 + 30, my0 + 18), "S", font=FONT_H2, fill=(22, 84, 150))

    # F\S label (right chamber)
    draw.text((wall_x + 60, my0 + 18), "F \\ S", font=FONT_H2,
              fill=(22, 84, 150))

    # Lookout region near doorway
    lookout = (wall_x - 130, door_top - 30, wall_x - 30, door_bot + 30)
    rounded_rect(draw, lookout, r=12, fill=(197, 246, 216),
                 outline=(39, 174, 96), width=2)
    draw.text((lookout[0] + 10, lookout[1] + 10), "lookout",
              font=FONT_SMALL, fill=(28, 120, 72))

    # Arrows from lookout into F\S
    for dy in [10, 35, 60]:
        sx = lookout[2] - 6
        sy = lookout[1] + 20 + dy
        tx = wall_x + 80
        ty = door_top + 10 + dy
        draw.line((sx, sy, tx, ty), fill=GREEN, width=3)
        draw.polygon([(tx, ty), (tx - 10, ty - 5), (tx - 10, ty + 5)],
                     fill=GREEN)

    # Sample points in both chambers
    left_pts = [(mx0 + 80, my0 + 100), (mx0 + 150, my0 + 250),
                (mx0 + 60, my0 + 400), (mx0 + 200, my0 + 350),
                (mx0 + 120, my0 + 500)]
    right_pts = [(wall_x + 120, my0 + 120), (wall_x + 250, my0 + 280),
                 (wall_x + 180, my0 + 420), (wall_x + 320, my0 + 350)]
    for px, py in left_pts + right_pts:
        if mx0 + 4 < px < mx1 - 4 and my0 + 4 < py < my1 - 4:
            draw.ellipse((px - 4, py - 4, px + 4, py + 4), fill=BLUE)

    out = OUT / "img2_lookout_definition.png"
    img.save(out)
    return out


# ── Image 3: failure probability curves (full-width) ──────────────────

def _plot_pt(x, y, ax0, ay0, ax1, ay1, x_max=700, y_max=1.0):
    px = ax0 + (x / x_max) * (ax1 - ax0)
    py = ay1 - (y / y_max) * (ay1 - ay0)
    return int(px), int(py)


def make_img3():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_centered(draw, 0, W, 20,
                  "PRM Failure Probability vs Milestones", FONT_H1)
    draw_centered(draw, 0, W, 68,
                  "Better expansiveness leads to faster exponential decay",
                  FONT_BODY, fill=MUTED)

    cx0, cy0, cx1, cy1 = 80, 110, W - 80, H - 60
    rounded_rect(draw, (cx0, cy0, cx1, cy1), r=14, fill=PANEL_BG,
                 outline=BORDER, width=2)

    ax0, ay0 = cx0 + 80, cy0 + 40
    ax1, ay1 = cx1 - 50, cy1 - 70

    # Axes
    draw.line((ax0, ay1, ax1, ay1), fill=TEXT, width=2)
    draw.line((ax0, ay0, ax0, ay1), fill=TEXT, width=2)

    # X ticks
    for m in range(0, 701, 100):
        px, _ = _plot_pt(m, 0, ax0, ay0, ax1, ay1)
        draw.line((px, ay1, px, ay1 + 6), fill=TEXT, width=2)
        draw.text((px - 14, ay1 + 10), str(m), font=FONT_SMALL, fill=MUTED)

    # Y ticks and grid
    for yv in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        _, py = _plot_pt(0, yv, ax0, ay0, ax1, ay1)
        draw.line((ax0 - 6, py, ax0, py), fill=TEXT, width=2)
        draw.text((ax0 - 48, py - 8), f"{yv:.1f}", font=FONT_SMALL,
                  fill=MUTED)
        if 0 < yv < 1:
            draw.line((ax0, py, ax1, py), fill=(230, 233, 238), width=1)

    # Axis labels
    draw_centered(draw, ax0, ax1, ay1 + 34, "milestones (m)", FONT_BODY)
    draw.text((ax0 - 40, ay0 - 28), "P_fail", font=FONT_BODY, fill=TEXT)

    # Curves
    curves = [
        (0.012, GREEN, "good"),
        (0.006, ORANGE, "medium"),
        (0.0025, RED, "poor"),
    ]
    for k, color, label in curves:
        pts = []
        for m in range(0, 701, 4):
            pts.append(_plot_pt(m, math.exp(-k * m), ax0, ay0, ax1, ay1))
        draw.line(pts, fill=color, width=3)
        lx, ly = _plot_pt(580, math.exp(-k * 580), ax0, ay0, ax1, ay1)
        draw.text((lx + 8, ly - 14), label, font=FONT_SMALL, fill=color)

    out = OUT / "img3_failure_probability_curves.png"
    img.save(out)
    return out


# ── Image 4: milestones bar chart (no overflow notes) ─────────────────

def make_img4():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_centered(draw, 0, W, 20,
                  "Milestones for 99% Success (toy model)", FONT_H1)
    draw_centered(draw, 0, W, 68,
                  "n >= ln(1/delta) / k,  delta = 0.01",
                  FONT_BODY, fill=MUTED)

    cx0, cy0, cx1, cy1 = 120, 110, W - 120, H - 80
    rounded_rect(draw, (cx0, cy0, cx1, cy1), r=14, fill=PANEL_BG,
                 outline=BORDER, width=2)

    delta = 0.01
    bars = [
        ("Good", 0.012, GREEN),
        ("Medium", 0.006, ORANGE),
        ("Poor", 0.0025, RED),
    ]
    vals = [(nm, math.ceil(math.log(1 / delta) / k), c)
            for nm, k, c in bars]
    max_n = max(n for _, n, _ in vals)

    bx0, by0 = cx0 + 100, cy0 + 50
    bx1, by1 = cx1 - 60, cy1 - 70

    draw.line((bx0, by1, bx1, by1), fill=TEXT, width=2)
    draw.line((bx0, by0, bx0, by1), fill=TEXT, width=2)

    # Y ticks
    for tick in range(0, max_n + 1, 400):
        py = by1 - int((tick / max_n) * (by1 - by0))
        draw.line((bx0 - 6, py, bx0, py), fill=TEXT, width=2)
        draw.text((bx0 - 56, py - 8), str(tick), font=FONT_SMALL,
                  fill=MUTED)

    # Bars
    group_w = (bx1 - bx0) // len(vals)
    bar_w = min(120, group_w - 40)
    for i, (name, n, color) in enumerate(vals):
        h = int((n / max_n) * (by1 - by0))
        cx = bx0 + group_w * i + group_w // 2
        left = cx - bar_w // 2
        top = by1 - h
        draw.rectangle((left, top, left + bar_w, by1), fill=color,
                       outline=(40, 40, 40), width=2)
        draw_centered(draw, left, left + bar_w, by1 + 10, name, FONT_H3)
        draw_centered(draw, left, left + bar_w, top - 28, f"n={n}",
                      FONT_H3, fill=color)

    draw_centered(draw, bx0, bx1, by1 + 42, "expansiveness quality",
                  FONT_BODY)

    out = OUT / "img4_milestones_vs_expansiveness.png"
    img.save(out)
    return out


# ── Extra GIF frames ──────────────────────────────────────────────────

def _make_title_frame():
    """Title frame for the GIF animation."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_centered(draw, 0, W, H // 2 - 80, "PRM Expansiveness",
                  FONT_H1)
    draw_centered(draw, 0, W, H // 2 - 20, "Visual Overview",
                  FONT_H2)
    draw_centered(draw, 0, W, H // 2 + 40,
                  "Why roadmap quality depends on free-space geometry",
                  FONT_BODY, fill=MUTED)
    return img


def _make_summary_frame():
    """Summary / takeaway frame for the GIF animation."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_centered(draw, 0, W, 60, "Key Takeaways", FONT_H1)
    points = [
        "1.  Expansiveness = how well subsets see outside themselves",
        "2.  Higher (epsilon, alpha, beta) = easier PRM connectivity",
        "3.  Narrow passages lower expansiveness, need more milestones",
        "4.  Motivates Gaussian / Bridge / OBPRM sampling strategies",
    ]
    y = 180
    for line in points:
        tw = text_width(draw, line, FONT_BODY)
        draw.text(((W - tw) // 2, y), line, font=FONT_BODY, fill=TEXT)
        y += 60
    return img


# ── GIF assembly ──────────────────────────────────────────────────────

def make_gif(png_paths):
    title = _make_title_frame()
    summary = _make_summary_frame()

    frames = [title]
    for p in png_paths:
        frames.append(Image.open(p))
    frames.append(summary)

    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE) for f in frames]
    out = OUT / "expansiveness_overview.gif"
    pal[0].save(
        out,
        save_all=True,
        append_images=pal[1:],
        duration=[2500, 2500, 2500, 2500, 2500, 3000],
        loop=0,
        optimize=False,
    )
    return out


# ── Main ──────────────────────────────────────────────────────────────

def main():
    pngs = [make_img1(), make_img2(), make_img3(), make_img4()]
    gif = make_gif(pngs)
    print("Generated files:")
    for p in pngs + [gif]:
        print(" -", p.name)


if __name__ == "__main__":
    main()
