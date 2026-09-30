"""Generate the landing page's example images from the real pipeline.

Run from backend/ after changing the name or headline in frontend/src/site.ts:
    .venv/Scripts/python.exe -m pip install -r requirements-dev.txt   # once
    .venv/Scripts/python.exe scripts/landing_assets.py
Writes frontend/public/landing/duck-{photo,template,frame}.svg, og.png (link previews) and apple-touch-icon.png.
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

import cv2
import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.pipeline import build_template, prepare_mask  # noqa: E402
from app.render import Path as SvgPath, page_svg  # noqa: E402

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
OUT = FRONTEND / "public" / "landing"
PUBLIC = FRONTEND / "public"
FONT = FRONTEND / "node_modules/@fontsource-variable/geist/files/geist-latin-wght-normal.woff2"
W, H = 760, 600

# A rubber duck, side view, as simple shapes: (kind, geometry, fill).
BODY = ("ellipse", ((360, 390), (240, 150)), "#ffd23f")
HEAD = ("circle", ((520, 210), 105), "#ffd23f")
BEAK = ("poly", [(600, 195), (700, 225), (610, 250)], "#ff8c42")
TAIL = ("poly", [(130, 340), (70, 250), (180, 300)], "#ffd23f")
SHAPES = [TAIL, BODY, HEAD, BEAK]


def duck_mask() -> np.ndarray:
    m = np.zeros((H, W), np.uint8)
    for kind, g, _ in SHAPES:
        if kind == "ellipse":
            cv2.ellipse(m, g[0], g[1], 0, 0, 360, 1, -1)
        elif kind == "circle":
            cv2.circle(m, g[0], g[1], 1, -1)
        else:
            cv2.fillPoly(m, [np.array(g)], 1)
    return m.astype(bool)


def photo_svg() -> str:
    """A flat illustration standing in for the uploaded photo."""
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">', f'<rect width="{W}" height="{H}" fill="#e8eef3"/>']
    parts.append(f'<ellipse cx="380" cy="548" rx="260" ry="18" fill="#000" opacity="0.08"/>')
    for kind, g, fill in SHAPES:
        if kind == "ellipse":
            (cx, cy), (rx, ry) = g
            parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}"/>')
        elif kind == "circle":
            (cx, cy), r = g
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>')
        else:
            parts.append(f'<polygon points="{" ".join(f"{x},{y}" for x, y in g)}" fill="{fill}"/>')
    parts.append('<ellipse cx="330" cy="370" rx="120" ry="60" fill="#f5b700" opacity="0.55"/>')  # wing
    parts.append('<circle cx="550" cy="185" r="13" fill="#1f1a17"/><circle cx="554" cy="181" r="4" fill="#fff"/>')
    parts.append("</svg>")
    return "".join(parts)


def frame_svg(model: list[dict], yaw=-35.0, pitch=22.0, pad=8.0):
    """The 3D model (profile, ribs, rings) seen from above and to the side, like a finished build."""
    a, b = np.radians(yaw), np.radians(pitch)
    rot_y = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    rot_x = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    R = rot_x @ rot_y
    flip = np.array([1.0, -1.0, 1.0])  # model y points up; SVG y points down
    lines = [(m["color"], (np.asarray(m["pts"], float) @ R.T) * flip) for m in model]
    allp = np.concatenate([p for _, p in lines])
    lo, hi = allp[:, :2].min(0) - pad, allp[:, :2].max(0) + pad
    w, h = hi - lo
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}">']
    # Draw back to front so nearer strands overlap farther ones.
    for color, p in sorted(lines, key=lambda cp: -cp[1][:, 2].mean()):
        xy = p[:, :2] - lo
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in xy)
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>')
    out.append("</svg>")
    return "".join(out), [(c, p[:, :2] - lo) for c, p in lines], (w, h)


def cropped_page_svg(page, pad=6.0) -> str:
    """A template page cropped to its pieces, so they aren't lost in a mostly blank sheet."""
    pts = np.concatenate([np.asarray(it.pts, float) for it in page.items if isinstance(it, SvgPath) and len(it.pts)])
    x0, y0 = np.maximum(pts.min(0) - pad, 0)
    x1, y1 = np.minimum(pts.max(0) + pad, (page.w, page.h))
    svg = page_svg(page)
    return re.sub(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"', f'viewBox="{x0:.1f} {y0:.1f} {x1 - x0:.1f} {y1 - y0:.1f}"', svg, count=1)


def site_text(key: str) -> str:
    m = re.search(rf'^\s*{key}:\s*"([^"]+)"', (FRONTEND / "src" / "site.ts").read_text(), re.M)
    if not m:
        raise SystemExit(f"{key} not found in site.ts")
    return m.group(1)


def geist(size: int, weight: int) -> ImageFont.FreeTypeFont:
    """The site's font (a woff2 web font, so convert it for Pillow)."""
    if not FONT.exists():
        raise SystemExit(f"{FONT} not found; run `npm ci` in frontend/ first")
    font = TTFont(FONT)
    font.flavor = None
    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    f = ImageFont.truetype(buf, size)
    f.set_variation_by_axes([weight])
    return f


def draw_lines(draw: ImageDraw.ImageDraw, lines, scale: float, offset, width: int):
    for color, xy in lines:
        pts = [(float(x) * scale + offset[0], float(y) * scale + offset[1]) for x, y in xy]
        draw.line(pts, fill=color, width=width, joint="curve")


def wrap(draw, text: str, font, max_w: float) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and draw.textlength(trial, font=font) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def og_image(lines, size, ss=2) -> Image.Image:
    """1200x630 link-preview card: name, headline, and the duck frame. Drawn at `ss`x and downsampled."""
    W, H = 1200 * ss, 630 * ss
    img = Image.new("RGB", (W, H), "#fafafa")
    d = ImageDraw.Draw(img)
    # The frame, on the right.
    w, h = size
    box = (560 * ss, 70 * ss, 580 * ss, 490 * ss)  # x, y, width, height
    scale = min(box[2] / w, box[3] / h)
    off = (box[0] + (box[2] - w * scale) / 2, box[1] + (box[3] - h * scale) / 2)
    draw_lines(d, lines, scale, off, 5 * ss)
    # Text, on the left.
    x = 72 * ss
    name_font, head_font, sub_font = geist(34 * ss, 600), geist(64 * ss, 650), geist(30 * ss, 450)
    mark = 44 * ss
    y = 72 * ss
    d.rounded_rectangle((x, y, x + mark, y + mark), radius=10 * ss, fill="#171717")
    cx, cy, r = x + mark / 2, y + mark / 2, mark * 0.36
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline="#fafafa", width=3 * ss)
    d.ellipse((cx - r * 0.45, cy - r, cx + r * 0.45, cy + r), outline="#00a651", width=3 * ss)
    d.line((cx - r, cy, cx + r, cy), fill="#ef4136", width=3 * ss)
    d.text((x + mark + 16 * ss, y + mark / 2), site_text("name"), font=name_font, fill="#171717", anchor="lm")
    y = 200 * ss
    for line in wrap(d, site_text("headline"), head_font, 500 * ss):
        d.text((x, y), line, font=head_font, fill="#171717")
        y += 76 * ss
    d.text((x, y + 24 * ss), "Free. No sign-up.", font=sub_font, fill="#737373")
    return img.resize((1200, 630), Image.LANCZOS)


def touch_icon(ss=4) -> Image.Image:
    """180x180 home-screen icon: the favicon's mark on white."""
    S = 180 * ss
    img = Image.new("RGB", (S, S), "#ffffff")
    d = ImageDraw.Draw(img)
    c, r, w = S / 2, S * 0.36, int(S * 0.06)
    d.ellipse((c - r, c - r, c + r, c + r), outline="#1f1a17", width=w)
    d.ellipse((c - r * 0.46, c - r, c + r * 0.46, c + r), outline="#00a651", width=w)
    d.line((c - r, c, c + r, c), fill="#ef4136", width=w)
    return img.resize((180, 180), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t = build_template(prepare_mask(duck_mask()), {"detail": 3})
    (OUT / "duck-photo.svg").write_text(photo_svg(), encoding="utf-8")
    (OUT / "duck-template.svg").write_text(cropped_page_svg(t.pages[0]), encoding="utf-8")
    svg, lines, size = frame_svg(t.model)
    (OUT / "duck-frame.svg").write_text(svg, encoding="utf-8")
    og_image(lines, size).save(PUBLIC / "og.png", optimize=True)
    touch_icon().save(PUBLIC / "apple-touch-icon.png", optimize=True)
    print("wrote duck-{photo,template,frame}.svg, og.png, apple-touch-icon.png")


if __name__ == "__main__":
    main()
