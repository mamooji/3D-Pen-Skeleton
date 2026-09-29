"""Cut the inflated body into flat pieces.

All coordinates are in work-mask pixels:
  x: left -> right in the photo, y: top -> bottom in the photo,
  w: depth (perpendicular to the photo), 0 = the profile plane.
"""
from __future__ import annotations

import numpy as np
from skimage.measure import find_contours

from .curves import area

W_STEP = 0.5


def profile_loops(sdf: np.ndarray) -> list[np.ndarray]:
    """Silhouette outline(s) as (x, y) loops, including real holes."""
    return [c[:, ::-1] for c in find_contours(sdf, 0.0) if len(c) >= 8]


def _column(field: np.ndarray, x: float) -> np.ndarray:
    x0 = int(np.clip(np.floor(x), 0, field.shape[1] - 1))
    x1 = min(x0 + 1, field.shape[1] - 1)
    t = x - x0
    return field[:, x0] * (1 - t) + field[:, x1] * t


def _row(field: np.ndarray, y: float) -> np.ndarray:
    return _column(field.T, y)


def _section(line: np.ndarray, thickness: float) -> list[np.ndarray]:
    """Closed loops of {(s, w) : |w| < h(s)} for a 1D signed height line.

    Returns loops as (s, w) arrays where s is the index along `line`.
    """
    h = np.where(line > 0, line * thickness, line)
    wmax = max(float(h.max()), 1.0) + 3.0
    ws = np.arange(-wmax, wmax + W_STEP, W_STEP)
    field = h[:, None] - np.abs(ws)[None, :]
    loops = []
    for c in find_contours(field, 0.0):
        if len(c) < 8:
            continue
        s = c[:, 0]
        w = ws[0] + c[:, 1] * W_STEP
        loops.append(np.column_stack([s, w]))
    return loops


def rib_loops(signed: np.ndarray, x: float, thickness: float) -> list[np.ndarray]:
    """Front-view cross section at column x, as (w, y) loops."""
    return [l[:, ::-1] for l in _section(_column(signed, x), thickness)]


def ring_loops(signed: np.ndarray, y: float, thickness: float) -> list[np.ndarray]:
    """Top-view cross section at row y, as (x, w) loops."""
    return _section(_row(signed, y), thickness)


def intervals(values: np.ndarray) -> list[tuple[float, float]]:
    """Sub-pixel [start, end] index ranges where values > 0."""
    pos = values > 0
    out = []
    n = len(values)
    i = 0
    while i < n:
        if not pos[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and pos[j + 1]:
            j += 1
        a = float(i) if i == 0 else i - 1 + (-values[i - 1]) / (values[i] - values[i - 1])
        b = float(j) if j == n - 1 else j + values[j] / (values[j] - values[j + 1])
        out.append((a, b))
        i = j + 1
    return out


def column_intervals(sdf: np.ndarray, x: float):
    return intervals(_column(sdf, x))


def row_intervals(sdf: np.ndarray, y: float):
    return intervals(_row(sdf, y))


def depth_at(signed: np.ndarray, x: float, y: float, thickness: float) -> float:
    """Half thickness of the body at photo point (x, y); 0 outside."""
    v = float(np.interp(y, np.arange(signed.shape[0]), _column(signed, x)))
    return max(v, 0.0) * thickness


def slice_positions(lo: float, hi: float, n: int) -> list[float]:
    """n evenly spaced cuts strictly inside [lo, hi]."""
    return [lo + (i + 1) * (hi - lo) / (n + 1) for i in range(n)]


def drop_small(loops: list[np.ndarray], min_area: float) -> list[np.ndarray]:
    return [l for l in loops if area(l) >= min_area]
