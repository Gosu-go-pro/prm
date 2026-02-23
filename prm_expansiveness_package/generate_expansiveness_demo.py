#!/usr/bin/env python3
"""Generate didactic images for PRM expansiveness (Question 16)."""

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


FONT_H1 = load_font(46, bold=True)
FONT_H2 = load_font(30, bold=True)
FONT_H3 = load_font(24, bold=True)
FONT_BODY = load_font(21)
FONT_SMALL = load_font(18)


def text_width(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)[2]


def draw_centered(draw, x0, x1, y, text, font, fill=TEXT):
    tw = text_width(draw, text, font)
    draw.text((x0 + (x1 - x0 - tw) / 2, y), text, font=font, fill=fill)


def rounded_rect(draw, xy, r=16, fill=None, outline=None, width=2):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def draw_workspace_box(draw, x0, y0, x1, y1, title):
    rounded_rect(draw, (x0, y0, x1, y1), r=16, fill=(252, 253, 255), outline=BORDER, width=2)
    draw_centered(draw, x0, x1, y0 + 10, title, FONT_H3)


def draw_room_convex(draw, x0, y0, x1, y1):
    draw_workspace_box(draw, x0, y0, x1, y1, "Case A: Convex free space")
    mx0, my0 = x0 + 28, y0 + 68
    mx1, my1 = x1 - 28, y1 - 28
    draw.rectangle((mx0, my0, mx1, my1), fill=(245, 251, 255), outline=(52, 152, 219), width=3)

    samples = [
        (mx0 + 80, my0 + 80), (mx0 + 180, my0 + 120), (mx0 + 320, my0 + 85),
        (mx0 + 480, my0 + 140), (mx0 + 120, my0 + 230), (mx0 + 260, my0 + 260),
        (mx0 + 430, my0 + 220), (mx0 + 540, my0 + 280), (mx0 + 330, my0 + 340),
    ]
    for x, y in samples:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=BLUE)

    draw.text((mx0 + 18, my1 - 42), "epsilon, alpha, beta are high", font=FONT_SMALL, fill=GREEN)


def draw_room_narrow_single(draw, x0, y0, x1, y1):
    draw_workspace_box(draw, x0, y0, x1, y1, "Case B: Single narrow passage")
    mx0, my0 = x0 + 28, y0 + 68
    mx1, my1 = x1 - 28, y1 - 28
    draw.rectangle((mx0, my0, mx1, my1), fill=(245, 251, 255), outline=(52, 152, 219), width=3)

    mid = (mx0 + mx1) // 2
    gap_top = my0 + 190
    gap_bottom = gap_top + 48
    draw.rectangle((mid - 20, my0 + 2, mid + 20, gap_top), fill=OBST)
    draw.rectangle((mid - 20, gap_bottom, mid + 20, my1 - 2), fill=OBST)

    left_pts = [(mx0 + 70, my0 + 90), (mx0 + 130, my0 + 200), (mx0 + 180, my0 + 280), (mx0 + 110, my0 + 330)]
    right_pts = [(mx1 - 90, my0 + 110), (mx1 - 130, my0 + 220), (mx1 - 180, my0 + 310)]
    for x, y in left_pts + right_pts:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=BLUE)

    draw.rectangle((mid - 23, gap_top - 2, mid + 23, gap_bottom + 2), outline=RED, width=2)
    draw.text((mid - 135, gap_top - 36), "tiny choke", font=FONT_SMALL, fill=RED)


def draw_room_multi_passage(draw, x0, y0, x1, y1):
    draw_workspace_box(draw, x0, y0, x1, y1, "Case C: Multiple moderate passages")
    mx0, my0 = x0 + 28, y0 + 68
    mx1, my1 = x1 - 28, y1 - 28
    draw.rectangle((mx0, my0, mx1, my1), fill=(245, 251, 255), outline=(52, 152, 219), width=3)

    mid = (mx0 + mx1) // 2
    draw.rectangle((mid - 20, my0 + 2, mid + 20, my0 + 120), fill=OBST)
    draw.rectangle((mid - 20, my0 + 175, mid + 20, my0 + 250), fill=OBST)
    draw.rectangle((mid - 20, my0 + 305, mid + 20, my1 - 2), fill=OBST)

    points = [
        (mx0 + 70, my0 + 90), (mx0 + 120, my0 + 190), (mx0 + 170, my0 + 300),
        (mx1 - 90, my0 + 95), (mx1 - 140, my0 + 205), (mx1 - 180, my0 + 290),
        (mid - 34, my0 + 145), (mid + 34, my0 + 145),
        (mid - 34, my0 + 275), (mid + 34, my0 + 275),
    ]
    for x, y in points:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=BLUE)

    draw.text((mid - 150, my1 - 42), "better lookout than single choke", font=FONT_SMALL, fill=GREEN)


def make_img1():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_centered(draw, 0, W, 26, "Expansiveness Intuition for PRM", FONT_H1)
    draw_centered(draw, 0, W, 86, "Connectivity is easier when free space has wide visibility and many lookouts", FONT_BODY, fill=MUTED)

    pad = 40
    top = 140
    bottom = H - 60
    pw = (W - 2 * pad - 2 * 24) // 3
    x0 = pad

    draw_room_convex(draw, x0, top, x0 + pw, bottom)
    x1 = x0 + pw + 24
    draw_room_narrow_single(draw, x1, top, x1 + pw, bottom)
    x2 = x1 + pw + 24
    draw_room_multi_passage(draw, x2, top, x2 + pw, bottom)

    out = OUT / "img1_expansiveness_cases.png"
    img.save(out)
    return out


def make_img2():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_centered(draw, 0, W, 24, "epsilon-good and beta-lookout", FONT_H1)
    draw_centered(draw, 0, W, 82, "A subset S needs enough points that can see into F\\S", FONT_BODY, fill=MUTED)

    x0, y0, x1, y1 = 90, 140, 980, 760
    draw_workspace_box(draw, x0, y0, x1, y1, "Two chambers with one doorway")

    mx0, my0 = x0 + 24, y0 + 65
    mx1, my1 = x1 - 24, y1 - 24
    draw.rectangle((mx0, my0, mx1, my1), fill=(245, 251, 255), outline=(52, 152, 219), width=3)

    wall_x = (mx0 + mx1) // 2
    door_top = my0 + 230
    door_bottom = door_top + 95
    draw.rectangle((wall_x - 24, my0 + 2, wall_x + 24, door_top), fill=OBST)
    draw.rectangle((wall_x - 24, door_bottom, wall_x + 24, my1 - 2), fill=OBST)

    draw.rectangle((mx0 + 2, my0 + 2, wall_x - 24, my1 - 2), fill=(217, 237, 255), outline=None)
    draw.text((mx0 + 24, my0 + 20), "S", font=FONT_H2, fill=(22, 84, 150))

    lookout = (wall_x - 150, door_top - 35, wall_x - 38, door_bottom + 35)
    rounded_rect(draw, lookout, r=14, fill=(197, 246, 216), outline=(39, 174, 96), width=2)
    draw.text((lookout[0] + 14, lookout[1] + 12), "beta-lookout(S)", font=FONT_SMALL, fill=(28, 120, 72))

    for dy in [8, 34, 60]:
        sx = lookout[2] - 8
        sy = lookout[1] + 22 + dy
        tx = wall_x + 90
        ty = door_top + 12 + dy
        draw.line((sx, sy, tx, ty), fill=GREEN, width=3)
        draw.polygon([(tx, ty), (tx - 12, ty - 6), (tx - 12, ty + 6)], fill=GREEN)

    draw.text((wall_x + 70, my0 + 22), "F\\S", font=FONT_H2, fill=(22, 84, 150))

    tx0, ty0, tx1, ty1 = 1030, 160, 1330, 740
    rounded_rect(draw, (tx0, ty0, tx1, ty1), r=16, fill=PANEL_BG, outline=BORDER, width=2)
    draw.text((tx0 + 18, ty0 + 18), "Definitions", font=FONT_H3, fill=TEXT)

    lines = [
        "V(q) = {q' in F | segment qq' subset F}",
        "epsilon-good: mu(V(q))/mu(F) >= epsilon",
        "for every q in F",
        "",
        "beta-lookout(S) = {q in S |",
        "  mu(V(q) intersect (F\\S))/mu(F\\S) >= beta }",
        "",
        "(epsilon, alpha, beta)-expansive:",
        "  F is epsilon-good and",
        "  mu(beta-lookout(S))/mu(S) >= alpha",
        "  for every measurable S subset F",
    ]
    y = ty0 + 68
    for line in lines:
        draw.text((tx0 + 18, y), line, font=FONT_SMALL, fill=MUTED if line else TEXT)
        y += 34

    out = OUT / "img2_lookout_definition.png"
    img.save(out)
    return out


def plot_point(x, y, x0, y0, x1, y1, x_max=700, y_max=1.0):
    px = x0 + (x / x_max) * (x1 - x0)
    py = y1 - (y / y_max) * (y1 - y0)
    return int(px), int(py)


def draw_curve(draw, area, k, color, label):
    x0, y0, x1, y1 = area
    pts = []
    for m in range(0, 701, 5):
        fail = math.exp(-k * m)
        pts.append(plot_point(m, fail, x0, y0, x1, y1))
    draw.line(pts, fill=color, width=4)

    lx, ly = plot_point(620, math.exp(-k * 620), x0, y0, x1, y1)
    draw.text((lx + 12, ly - 12), label, font=FONT_SMALL, fill=color)


def make_img3():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_centered(draw, 0, W, 26, "Expansiveness vs PRM Failure Probability", FONT_H1)
    draw_centered(draw, 0, W, 86, "Lecture intuition: in expansive spaces, failure probability drops exponentially with milestones", FONT_BODY, fill=MUTED)

    x0, y0, x1, y1 = 120, 170, 980, 760
    rounded_rect(draw, (x0, y0, x1, y1), r=16, fill=PANEL_BG, outline=BORDER, width=2)

    # axes
    ax0, ay0, ax1, ay1 = x0 + 70, y0 + 50, x1 - 45, y1 - 65
    draw.line((ax0, ay1, ax1, ay1), fill=TEXT, width=3)
    draw.line((ax0, ay0, ax0, ay1), fill=TEXT, width=3)

    for m in [0, 100, 200, 300, 400, 500, 600, 700]:
        px, py = plot_point(m, 0.0, ax0, ay0, ax1, ay1)
        draw.line((px, ay1, px, ay1 + 8), fill=TEXT, width=2)
        draw.text((px - 18, ay1 + 14), str(m), font=FONT_SMALL, fill=MUTED)

    for y in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        px, py = plot_point(0, y, ax0, ay0, ax1, ay1)
        draw.line((ax0 - 8, py, ax0, py), fill=TEXT, width=2)
        draw.text((ax0 - 58, py - 10), f"{y:.1f}", font=FONT_SMALL, fill=MUTED)
        if y not in (0.0, 1.0):
            draw.line((ax0, py, ax1, py), fill=(228, 232, 238), width=1)

    draw.text((ax0 + 290, ay1 + 42), "number of milestones", font=FONT_BODY, fill=TEXT)
    draw.text((ax0 - 42, ay0 - 30), "P_fail", font=FONT_BODY, fill=TEXT)

    draw_curve(draw, (ax0, ay0, ax1, ay1), 0.012, GREEN, "good expansiveness")
    draw_curve(draw, (ax0, ay0, ax1, ay1), 0.006, ORANGE, "medium")
    draw_curve(draw, (ax0, ay0, ax1, ay1), 0.0025, RED, "poor (narrow passages)")

    # right notes
    tx0, ty0, tx1, ty1 = 1030, 190, 1330, 740
    rounded_rect(draw, (tx0, ty0, tx1, ty1), r=16, fill=PANEL_BG, outline=BORDER, width=2)
    draw.text((tx0 + 18, ty0 + 18), "Interpretation", font=FONT_H3, fill=TEXT)
    notes = [
        "- Larger epsilon/alpha/beta",
        "  means easier roadmap growth.",
        "",
        "- Narrow passages reduce",
        "  lookout volume ratios.",
        "",
        "- More milestones are needed",
        "  to keep connectivity high.",
        "",
        "- This is why PRM variants",
        "  target hard regions",
        "  (Gaussian, Bridge, OBPRM).",
    ]
    y = ty0 + 72
    for t in notes:
        draw.text((tx0 + 18, y), t, font=FONT_SMALL, fill=MUTED)
        y += 36

    out = OUT / "img3_failure_probability_curves.png"
    img.save(out)
    return out


def make_img4():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_centered(draw, 0, W, 26, "Milestones Needed for 99% Success (toy model)", FONT_H1)
    draw_centered(draw, 0, W, 86, "n >= ln(1/delta)/k with delta=0.01 and larger k for more expansive spaces", FONT_BODY, fill=MUTED)

    x0, y0, x1, y1 = 120, 180, 1260, 760
    rounded_rect(draw, (x0, y0, x1, y1), r=16, fill=PANEL_BG, outline=BORDER, width=2)

    bars = [
        ("Good", 0.012, GREEN),
        ("Medium", 0.006, ORANGE),
        ("Poor", 0.0025, RED),
    ]
    delta = 0.01
    vals = []
    for name, k, _ in bars:
        n = math.ceil(math.log(1.0 / delta) / k)
        vals.append((name, n))

    max_n = max(v for _, v in vals)
    bx0, by0 = x0 + 110, y0 + 60
    bx1, by1 = x1 - 80, y1 - 90

    draw.line((bx0, by1, bx1, by1), fill=TEXT, width=3)
    draw.line((bx0, by0, bx0, by1), fill=TEXT, width=3)

    for tick in [0, 400, 800, 1200, 1600, 2000]:
        py = by1 - int((tick / max_n) * (by1 - by0))
        draw.line((bx0 - 8, py, bx0, py), fill=TEXT, width=2)
        draw.text((bx0 - 64, py - 10), str(tick), font=FONT_SMALL, fill=MUTED)

    group_w = (bx1 - bx0) // len(bars)
    bar_w = 120
    for i, (name, k, color) in enumerate(bars):
        n = math.ceil(math.log(1.0 / delta) / k)
        h = int((n / max_n) * (by1 - by0))
        cx = bx0 + group_w * i + group_w // 2
        left = cx - bar_w // 2
        top = by1 - h
        draw.rectangle((left, top, left + bar_w, by1), fill=color, outline=(40, 40, 40), width=2)
        draw.text((left + 20, by1 + 16), name, font=FONT_H3, fill=TEXT)
        draw.text((left + 14, top - 36), f"n={n}", font=FONT_H3, fill=color)

    draw.text((bx0 + 350, by1 + 58), "expansiveness quality", font=FONT_BODY, fill=TEXT)
    draw.text((x0 + 30, y0 + 20), "Target failure: 1%", font=FONT_H3, fill=PURPLE)

    note = [
        "Lower expansiveness -> more milestones for same reliability.",
        "In practice epsilon, alpha, beta are hard to compute exactly,",
        "but the trend explains why narrow-passage worlds are harder for PRM.",
    ]
    ny = y1 + 20
    for line in note:
        draw.text((x0 + 8, ny), line, font=FONT_SMALL, fill=MUTED)
        ny += 30

    out = OUT / "img4_milestones_vs_expansiveness.png"
    img.save(out)
    return out


def make_gif(frames):
    images = [Image.open(p).convert("P", palette=Image.Palette.ADAPTIVE) for p in frames]
    out = OUT / "expansiveness_overview.gif"
    images[0].save(
        out,
        save_all=True,
        append_images=images[1:] + [images[-1]],
        duration=[1400, 1400, 1400, 1700, 1400],
        loop=0,
        optimize=False,
    )
    return out


def main():
    outputs = [
        make_img1(),
        make_img2(),
        make_img3(),
        make_img4(),
    ]
    outputs.append(make_gif(outputs))

    print("Generated files:")
    for p in outputs:
        print("-", p.name)


if __name__ == "__main__":
    main()
