"""Polyline utilities: resample, smooth, simplify."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import LineString


def resample(pts: np.ndarray, step: float, closed: bool) -> np.ndarray:
    pts = np.asarray(pts, float)
    if closed and not np.allclose(pts[0], pts[-1]):
        pts = np.vstack([pts, pts[:1]])
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    pts = pts[np.concatenate([[True], seg > 1e-9])]
    seg = seg[seg > 1e-9]
    length = seg.sum()
    if length == 0:
        return pts[:1]
    s = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(int(np.ceil(length / step)), 8 if closed else 2)
    t = np.linspace(0.0, length, n + 1 if closed else n)
    if closed:
        t = t[:-1]
    return np.column_stack([np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])])


def length(pts: np.ndarray, closed: bool) -> float:
    pts = np.asarray(pts, float)
    if closed:
        pts = np.vstack([pts, pts[:1]])
    return float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())


def smooth(pts: np.ndarray, sigma: float, closed: bool, step: float = 0.5) -> np.ndarray:
    r = resample(pts, step, closed)
    if sigma <= 0 or len(r) < 5:
        return r
    # Heavy smoothing would collapse tiny loops; cap it relative to their size.
    sigma = min(sigma, length(r, closed) / 12.0)
    mode = "wrap" if closed else "nearest"
    return np.column_stack(
        [gaussian_filter1d(r[:, k], sigma / step, mode=mode) for k in (0, 1)]
    )


def simplify(pts: np.ndarray, tol: float, closed: bool) -> np.ndarray:
    if tol <= 0 or len(pts) < 4:
        return pts
    if closed:
        ring = np.vstack([pts, pts[:1]])
        out = np.asarray(LineString(ring).simplify(tol, preserve_topology=False).coords)
        return out[:-1] if len(out) > 4 else pts
    out = np.asarray(LineString(pts).simplify(tol, preserve_topology=False).coords)
    return out if len(out) >= 2 else pts


def clean(pts: np.ndarray, sigma: float, tol: float, closed: bool) -> np.ndarray:
    return simplify(smooth(pts, sigma, closed), tol, closed)


def area(pts: np.ndarray) -> float:
    x, y = pts[:, 0], pts[:, 1]
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2.0)
