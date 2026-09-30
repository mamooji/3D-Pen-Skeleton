"""Page primitives (in millimetres, y down) and their SVG / PDF renderers."""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

import numpy as np
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

MM = 72.0 / 25.4
FONT = "Helvetica, Arial, sans-serif"


@dataclass
class Path:
    pts: np.ndarray
    closed: bool = True
    color: str = "#1f1a17"
    width: float = 0.35
    dash: tuple[float, ...] | None = None


@dataclass
class Text:
    x: float
    y: float  # baseline
    s: str
    size: float = 4.0
    color: str = "#1f1a17"
    anchor: str = "middle"  # start | middle | end
    bold: bool = True

    def box(self) -> tuple[float, float, float, float]:
        w = 0.6 * self.size * len(self.s)
        x0 = {"start": self.x, "middle": self.x - w / 2, "end": self.x - w}[self.anchor]
        return x0, self.y - 0.8 * self.size, x0 + w, self.y + 0.2 * self.size


@dataclass
class Page:
    w: float
    h: float
    items: list = field(default_factory=list)


def _fmt(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def page_svg(page: Page) -> str:
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_fmt(page.w)}mm" '
        f'height="{_fmt(page.h)}mm" viewBox="0 0 {_fmt(page.w)} {_fmt(page.h)}">',
        f'<rect width="{_fmt(page.w)}" height="{_fmt(page.h)}" fill="#fff"/>',
    ]
    for it in page.items:
        if isinstance(it, Path):
            if len(it.pts) < 2:
                continue
            d = "M" + " L".join(f"{_fmt(x)} {_fmt(y)}" for x, y in it.pts)
            if it.closed:
                d += " Z"
            dash = f' stroke-dasharray="{" ".join(map(_fmt, it.dash))}"' if it.dash else ""
            out.append(
                f'<path d="{d}" fill="none" stroke="{it.color}" stroke-width="{_fmt(it.width)}" '
                f'stroke-linejoin="round" stroke-linecap="round"{dash}/>'
            )
        elif isinstance(it, Text):
            weight = "bold" if it.bold else "normal"
            out.append(
                f'<text x="{_fmt(it.x)}" y="{_fmt(it.y)}" font-size="{_fmt(it.size)}" '
                f'font-family="{FONT}" font-weight="{weight}" fill="{it.color}" '
                f'text-anchor="{it.anchor}">{escape(it.s)}</text>'
            )
    out.append("</svg>")
    return "".join(out)


def pages_pdf(pages: list[Page]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.setTitle("Trace 3D Pen template")
    for page in pages:
        c.setPageSize((page.w * MM, page.h * MM))
        c.setLineJoin(1)
        c.setLineCap(1)
        for it in page.items:
            if isinstance(it, Path):
                if len(it.pts) < 2:
                    continue
                c.setStrokeColor(HexColor(it.color))
                c.setLineWidth(it.width * MM)
                c.setDash([d * MM for d in it.dash] if it.dash else [])
                p = c.beginPath()
                x, y = it.pts[0]
                p.moveTo(x * MM, (page.h - y) * MM)
                for x, y in it.pts[1:]:
                    p.lineTo(x * MM, (page.h - y) * MM)
                if it.closed:
                    p.close()
                c.drawPath(p, stroke=1, fill=0)
            elif isinstance(it, Text):
                c.setFillColor(HexColor(it.color))
                c.setFont("Helvetica-Bold" if it.bold else "Helvetica", it.size * MM)
                x, y = it.x * MM, (page.h - it.y) * MM
                {"start": c.drawString, "middle": c.drawCentredString, "end": c.drawRightString}[
                    it.anchor
                ](x, y, it.s)
        c.showPage()
    c.save()
    return buf.getvalue()
