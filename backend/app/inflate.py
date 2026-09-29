"""Turn a flat silhouette into a rounded 3D body.

We solve the Poisson equation  lap(u) = -1  inside the mask with u = 0 on the
edge, then take  h = sqrt(4u).  For a disk of radius R this gives exactly a
sphere (h = sqrt(R^2 - r^2)); for long strips it gives near-round tubes. Unlike
a plain distance transform, thin parts (legs, ears) stay thin and big parts
stay fat, because the solution adapts to the local width.

The object is assumed mirror-symmetric front-to-back, so h is the half
thickness: the body occupies |depth| <= h(x, y).
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve

SOLVE_SIZE = 300


def half_thickness(mask: np.ndarray, solve_size: int = SOLVE_SIZE) -> np.ndarray:
    H, W = mask.shape
    s = max(H, W) / solve_size if max(H, W) > solve_size else 1.0
    size = (max(1, round(W / s)), max(1, round(H / s)))
    small = cv2.resize(mask.astype(np.float32), size, interpolation=cv2.INTER_AREA) > 0.5
    h, w = small.shape

    ys, xs = np.nonzero(small)
    n = len(ys)
    if n == 0:
        return np.zeros(mask.shape, np.float32)
    idx = -np.ones(small.shape, np.int64)
    idx[ys, xs] = np.arange(n)

    rows, cols, vals = [np.arange(n)], [np.arange(n)], [np.full(n, 4.0)]
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = ys + dy, xs + dx
        ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        j = np.full(n, -1)
        j[ok] = idx[ny[ok], nx[ok]]
        inside = j >= 0
        rows.append(np.nonzero(inside)[0])
        cols.append(j[inside])
        vals.append(np.full(int(inside.sum()), -1.0))
    A = csr_matrix(
        (np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)
    )
    u = spsolve(A, np.ones(n))

    U = np.zeros(small.shape, np.float32)
    U[ys, xs] = u
    # Upsample u (smooth) rather than h (sqrt-steep at the edge), then convert
    # from coarse-pixel units to work-pixel units.
    U = cv2.resize(U, (W, H), interpolation=cv2.INTER_LINEAR)
    hfull = s * np.sqrt(4.0 * np.maximum(U, 0.0))
    hfull[~mask] = 0.0
    return hfull.astype(np.float32)


def signed_fields(mask: np.ndarray, height: np.ndarray):
    """Return (sdf, signed_height).

    sdf: signed distance to the silhouette edge, > 0 inside.
    signed_height: half thickness inside, minus the distance to the object
    outside. Its zero level is the silhouette, so slicing it gives cross
    sections whose extent matches the profile outline.
    """
    m = mask.astype(np.uint8)
    dt_in = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    dt_out = cv2.distanceTransform(1 - m, cv2.DIST_L2, 5)
    sdf = dt_in - dt_out
    signed = np.where(mask, np.maximum(height, 0.5), -dt_out).astype(np.float32)
    return sdf.astype(np.float32), signed
