"""Group drawing items into pieces and pack them onto printable pages."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .render import Page, Path, Text

PAPER = {"a4": (210.0, 297.0), "letter": (215.9, 279.4)}
MARGIN = 10.0
GAP = 6.0
HEADER = 8.0


@dataclass
class Piece:
    name: str
    items: list = field(default_factory=list)
    _boxes: list = field(default_factory=list)

    def add(self, item):
        self.items.append(item)
        return item

    def label(self, x, y, s, size=4.0, color="#1f1a17", anchor="middle"):
        """Add a text label, nudging it right until it doesn't overlap another label."""
        t = Text(x, y, s, size, color, anchor)
        for _ in range(30):
            b = t.box()
            if not any(b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3] for o in self._boxes):
                break
            t.x += 0.7 * size
        self._boxes.append(t.box())
        return self.add(t)

    def bbox(self):
        xs, ys = [], []
        for it in self.items:
            if isinstance(it, Path) and len(it.pts):
                xs += [it.pts[:, 0].min(), it.pts[:, 0].max()]
                ys += [it.pts[:, 1].min(), it.pts[:, 1].max()]
            elif isinstance(it, Text):
                x0, y0, x1, y1 = it.box()
                xs += [x0, x1]
                ys += [y0, y1]
        return min(xs), min(ys), max(xs), max(ys)

    @property
    def size(self):
        x0, y0, x1, y1 = self.bbox()
        return x1 - x0, y1 - y0

    def moved(self, dx, dy) -> list:
        out = []
        for it in self.items:
            if isinstance(it, Path):
                out.append(Path(it.pts + [dx, dy], it.closed, it.color, it.width, it.dash))
            else:
                out.append(Text(it.x + dx, it.y + dy, it.s, it.size, it.color, it.anchor, it.bold))
        return out

    def normalized(self) -> "Piece":
        x0, y0, _, _ = self.bbox()
        return Piece(self.name, self.moved(-x0, -y0))

    def rotated(self) -> "Piece":
        """Rotate a normalized piece 90 degrees; labels stay upright."""
        w, _ = self.size
        out = []
        for it in self.items:
            if isinstance(it, Path):
                pts = np.column_stack([it.pts[:, 1], w - it.pts[:, 0]])
                out.append(Path(pts, it.closed, it.color, it.width, it.dash))
            else:
                out.append(Text(it.y, w - it.x, it.s, it.size, it.color, it.anchor, it.bold))
        return Piece(self.name, out).normalized()


@dataclass
class _Shelf:
    y: float
    h: float
    x: float = 0.0


def pack(pieces: list[Piece], paper: str, title: str):
    """First-fit shelf packing. Returns (pages, oversize) where oversize
    lists (piece name, shrink factor needed to fit a page)."""
    pw, ph = PAPER[paper]
    aw, ah = pw - 2 * MARGIN, ph - 2 * MARGIN - HEADER
    pages: list[list] = []
    shelves: list[list[_Shelf]] = []
    oversize = []

    def find_spot(bw, bh):
        for p, page_shelves in enumerate(shelves):
            for k, sh in enumerate(page_shelves):
                last = k == len(page_shelves) - 1
                if sh.x + bw <= aw and (bh <= sh.h or (last and sh.y + bh <= ah)):
                    return p, sh
            top = page_shelves[-1].y + page_shelves[-1].h + GAP if page_shelves else 0.0
            if top + bh <= ah:
                page_shelves.append(_Shelf(top, 0.0))
                return p, page_shelves[-1]
        return None

    for piece in pieces:
        piece = piece.normalized()
        bw, bh = piece.size
        if (bw > aw or bh > ah) and bh <= aw and bw <= ah:
            piece = piece.rotated()
            bw, bh = piece.size
        if bw > aw or bh > ah:
            fit = max(min(aw / bw, ah / bh), min(aw / bh, ah / bw))
            oversize.append((piece.name, fit))
        spot = find_spot(bw, bh)
        if spot is None:
            pages.append([])
            shelves.append([_Shelf(0.0, 0.0)])
            spot = len(pages) - 1, shelves[-1][0]
        p, sh = spot
        pages[p] += piece.moved(MARGIN + sh.x, MARGIN + HEADER + sh.y)
        sh.x += bw + GAP
        sh.h = max(sh.h, bh)

    out = []
    for i, items in enumerate(pages):
        head = Text(
            MARGIN, MARGIN + 4, f"{title}  ·  page {i + 1}/{len(pages)}  ·  print at 100% (Actual size)",
            3.0, "#777777", "start", False,
        )
        out.append(Page(pw, ph, [head] + items))
    return out, oversize
