"""Inner detail lines (eyes, mouth, seams) traced from edges inside the object."""
from __future__ import annotations

import cv2
import numpy as np
from skimage.morphology import skeletonize

_NBRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]


def _trace(skel: np.ndarray) -> list[np.ndarray]:
    """Walk a 1-px skeleton into polylines of (x, y) points."""
    pts = set(zip(*np.nonzero(skel)))

    def nbrs(p):
        return [(p[0] + dy, p[1] + dx) for dy, dx in _NBRS if (p[0] + dy, p[1] + dx) in pts]

    ends = [p for p in pts if len(nbrs(p)) == 1]
    visited: set = set()
    lines = []
    for start in ends + sorted(pts):
        if start in visited:
            continue
        line = [start]
        visited.add(start)
        cur = start
        while True:
            nxt = [q for q in nbrs(cur) if q not in visited]
            if not nxt:
                break
            # Prefer straight (4-connected) steps so we don't skip corners.
            cur = min(nxt, key=lambda q: abs(q[0] - cur[0]) + abs(q[1] - cur[1]))
            visited.add(cur)
            line.append(cur)
        if len(line) >= 2:
            lines.append(np.array([(x, y) for y, x in line], float))
    return lines


def feature_lines(rgb: np.ndarray, mask: np.ndarray, min_len: float) -> list[np.ndarray]:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (0, 0), 1.5)
    edges = cv2.Canny(gray, 40, 120) > 0
    # Stay away from the silhouette edge; that is already the profile outline.
    band = max(5, int(round(max(mask.shape) * 0.015)))
    inner = cv2.erode(mask.astype(np.uint8), np.ones((band, band), np.uint8)) > 0
    edges &= inner
    if not edges.any():
        return []
    skel = skeletonize(edges)
    return [l for l in _trace(skel) if len(l) >= min_len]
