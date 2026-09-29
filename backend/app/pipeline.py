"""Photo -> prepared 3D body -> printable skeleton template."""
from __future__ import annotations

import io
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

from . import curves, slicer
from .features import feature_lines
from .inflate import half_thickness, signed_fields
from .layout import Piece, pack
from .render import Page, Path
from .segment import clean_mask, crop_to_work, extract_mask, load_image

PALETTE = ["#1f1a17", "#00a651", "#ef4136", "#262262", "#8e44ad", "#0077b6", "#d35400", "#2e7d32"]
RING_PALETTE = ["#e6007e", "#0097a7", "#f39c12", "#6d4c41"]
OUTLINE = "#1f1a17"
GUIDE = "#9a9a9a"
FEATURE = "#7a7a7a"
TICK = 1.6  # half length of joint tick marks, mm

# Detail 1..5 -> how many cuts and how much curve cleanup (sizes in work px).
DETAIL = {
    1: dict(ribs=3, rings=0, sigma=6.0, tol=1.5, min_frac=0.02, feat_len=90),
    2: dict(ribs=4, rings=1, sigma=4.0, tol=1.0, min_frac=0.01, feat_len=60),
    3: dict(ribs=6, rings=2, sigma=2.5, tol=0.6, min_frac=0.005, feat_len=40),
    4: dict(ribs=8, rings=2, sigma=1.8, tol=0.4, min_frac=0.0025, feat_len=30),
    5: dict(ribs=11, rings=3, sigma=1.2, tol=0.25, min_frac=0.001, feat_len=20),
}


@dataclass
class Prepared:
    mask: np.ndarray
    rgb: np.ndarray
    sdf: np.ndarray
    signed: np.ndarray

    @property
    def bbox(self):
        ys, xs = np.nonzero(self.mask)
        return float(xs.min()), float(ys.min()), float(xs.max() + 1), float(ys.max() + 1)


def prepare_mask(mask: np.ndarray, rgb: np.ndarray | None = None) -> Prepared:
    if rgb is None:
        rgb = np.where(mask[..., None], 200, 255).astype(np.uint8).repeat(3, axis=2)
    sdf, signed = signed_fields(mask, half_thickness(mask))
    return Prepared(mask, rgb, sdf, signed)


def prepare(data: bytes) -> Prepared:
    img = load_image(data)
    mask = clean_mask(extract_mask(img))
    rgb = np.array(img.convert("RGB"))
    mask, rgb = crop_to_work(mask, rgb)
    return prepare_mask(clean_mask(mask), rgb)


def preview_png(prep: Prepared) -> bytes:
    """The photo with the background faded and the detected outline drawn."""
    rgb = prep.rgb.astype(np.float32)
    faded = np.where(prep.mask[..., None], rgb, rgb * 0.25 + 255 * 0.75).astype(np.uint8)
    contours, _ = cv2.findContours(prep.mask.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(faded, contours, -1, (239, 65, 54), 2, cv2.LINE_AA)
    buf = io.BytesIO()
    Image.fromarray(faded).save(buf, "PNG")
    return buf.getvalue()


def resolve_params(p: dict) -> dict:
    detail = int(np.clip(p.get("detail", 3), 1, 5))
    out = dict(DETAIL[detail])
    out.update(
        detail=detail,
        thickness=float(p.get("thickness", 1.0)),
        size_cm=float(p.get("size_cm", 15.0)),
        paper=p.get("paper", "a4"),
        stack=bool(p.get("stack", True)),
        features=bool(p.get("features", False)),
    )
    for k in ("ribs", "rings"):
        if p.get(k) is not None:
            out[k] = int(p[k])
    return out


@dataclass
class Template:
    pages: list[Page]
    warnings: list[str]
    info: dict
    model: list[dict]


def build_template(prep: Prepared, params: dict) -> Template:
    P = resolve_params(params)
    T, sigma, tol = P["thickness"], P["sigma"], P["tol"]
    x0, y0, x1, y1 = prep.bbox
    min_area = P["min_frac"] * float(prep.mask.sum())

    def tidy(loops, closed=True):
        return [curves.clean(l, sigma, tol, closed) for l in loops]

    profile = tidy(slicer.drop_small(slicer.profile_loops(prep.sdf), min_area))
    rib_x = slicer.slice_positions(x0, x1, P["ribs"])
    ring_y = slicer.slice_positions(y0, y1, P["rings"])
    ribs = [tidy(slicer.drop_small(slicer.rib_loops(prep.signed, x, T), min_area * T)) for x in rib_x]
    rings = [tidy(slicer.drop_small(slicer.ring_loops(prep.signed, y, T), min_area * T)) for y in ring_y]
    features = []
    if P["features"]:
        features = [curves.clean(l, sigma, tol, False)
                    for l in feature_lines(prep.rgb, prep.mask, P["feat_len"])]

    scale = P["size_cm"] * 10.0 / max(x1 - x0, y1 - y0)  # mm per work px

    def X(x):
        return (np.asarray(x) - x0) * scale

    def Y(y):
        return (np.asarray(y) - y0) * scale

    rib_color = [PALETTE[i % len(PALETTE)] for i in range(len(rib_x))]
    ring_color = [RING_PALETTE[j % len(RING_PALETTE)] for j in range(len(ring_y))]
    rib_name = [str(i + 1) for i in range(len(rib_x))]
    ring_name = [chr(ord("A") + j) for j in range(len(ring_y))]
    ribs_kept = [i for i, loops in enumerate(ribs) if loops]
    rings_kept = [j for j, loops in enumerate(rings) if loops]
    label = max(3.0, min(5.0, P["size_cm"] * 0.3))

    pieces: list[Piece] = []

    # --- Profile: silhouette + where each rib and ring attaches -------------
    pr = Piece("Profile")
    for loop in profile:
        pr.add(Path(np.column_stack([X(loop[:, 0]), Y(loop[:, 1])]), True, OUTLINE, 0.4))
    for loop in features:
        pr.add(Path(np.column_stack([X(loop[:, 0]), Y(loop[:, 1])]), False, FEATURE, 0.3))
    for i in ribs_kept:
        segs = slicer.column_intervals(prep.sdf, rib_x[i])
        for a, b in segs:
            pr.add(Path(np.array([[X(rib_x[i]), Y(a)], [X(rib_x[i]), Y(b)]]), False, rib_color[i], 0.3))
        top = min(a for a, _ in segs)
        pr.label(X(rib_x[i]), Y(top) - 1.5, rib_name[i], label, rib_color[i])
    for j in rings_kept:
        segs = slicer.row_intervals(prep.sdf, ring_y[j])
        for a, b in segs:
            pr.add(Path(np.array([[X(a), Y(ring_y[j])], [X(b), Y(ring_y[j])]]), False, ring_color[j], 0.3))
        left = min(a for a, _ in segs)
        pr.label(X(left) - 1.5, Y(ring_y[j]) + label * 0.35, ring_name[j], label, ring_color[j], "end")
    pieces.append(pr)

    # --- Ribs: front-view cross sections -------------------------------------
    def rib_items(piece: Piece, i: int):
        for loop in ribs[i]:
            piece.add(Path(np.column_stack([loop[:, 0] * scale, Y(loop[:, 1])]), True, rib_color[i], 0.35))
        for j in rings_kept:  # where ring j crosses this rib
            w = slicer.depth_at(prep.signed, rib_x[i], ring_y[j], T) * scale
            if w > 0:
                for sx in (-w, w):
                    piece.add(Path(np.array([[sx - TICK, Y(ring_y[j])], [sx + TICK, Y(ring_y[j])]]),
                                   False, ring_color[j], 0.35))

    def center_line(piece: Piece, vertical: bool):
        x_lo, y_lo, x_hi, y_hi = piece.bbox()
        pts = [[0, y_lo - 2], [0, y_hi + 2]] if vertical else [[x_lo - 2, 0], [x_hi + 2, 0]]
        piece.add(Path(np.array(pts, float), False, GUIDE, 0.2, (2.0, 1.5)))

    if ribs_kept:
        if P["stack"]:
            rp = Piece("Ribs")
            for i in ribs_kept:
                rib_items(rp, i)
            center_line(rp, True)
            for i in ribs_kept:
                top = min(l[:, 1].min() for l in ribs[i])
                rp.label(1.0, Y(top) + label + 0.5, rib_name[i], label, rib_color[i], "start")
            pieces.append(rp)
        else:
            for i in ribs_kept:
                rp = Piece(f"Rib {rib_name[i]}")
                rib_items(rp, i)
                center_line(rp, True)
                x_lo, y_lo, x_hi, y_hi = rp.bbox()
                rp.label(1.0, (y_lo + y_hi) / 2 + label * 0.35, rib_name[i], label, rib_color[i], "start")
                pieces.append(rp)

    # --- Rings: top-view cross sections --------------------------------------
    def ring_items(piece: Piece, j: int):
        for loop in rings[j]:
            piece.add(Path(np.column_stack([X(loop[:, 0]), loop[:, 1] * scale]), True, ring_color[j], 0.35))
        for i in ribs_kept:  # where rib i crosses this ring
            w = slicer.depth_at(prep.signed, rib_x[i], ring_y[j], T) * scale
            if w > 0:
                for sw in (-w, w):
                    piece.add(Path(np.array([[X(rib_x[i]), sw - TICK], [X(rib_x[i]), sw + TICK]]),
                                   False, rib_color[i], 0.35))

    if rings_kept:
        groups = [rings_kept] if P["stack"] else [[j] for j in rings_kept]
        for group in groups:
            gp = Piece("Rings" if P["stack"] else f"Ring {ring_name[group[0]]}")
            for j in group:
                ring_items(gp, j)
            center_line(gp, False)
            for j in group:
                left = min(l[:, 0].min() for l in rings[j])
                gp.label(X(left) - 1.5, label * 0.35, ring_name[j], label, ring_color[j], "end")
            pieces.append(gp)

    # --- Scale check -----------------------------------------------------------
    sc = Piece("Scale")
    sc.add(Path(np.array([[0, 3], [50, 3]], float), False, OUTLINE, 0.35))
    for k in range(6):
        sc.add(Path(np.array([[k * 10, 1.5 if k % 5 else 0], [k * 10, 3]], float), False, OUTLINE, 0.3))
    sc.label(0, 8, "50 mm — check this with a ruler", 3.0, "#555555", "start")
    pieces.append(sc)

    title = f"3D pen skeleton · {P['size_cm']:g} cm · detail {P['detail']}"
    pages, oversize = pack(pieces, P["paper"], title)

    warnings = []
    if oversize:
        fit = min(f for _, f in oversize)
        names = ", ".join(n for n, _ in oversize)
        warnings.append(
            f"{names} won't fit on one page. Reduce size to about {P['size_cm'] * fit:.1f} cm or less."
        )
    missing = len(rib_x) - len(ribs_kept)
    if missing:
        warnings.append(f"{missing} rib(s) were too small to print and were skipped.")

    # --- 3D preview: every piece placed in space (mm, centered) -------------
    model = []
    cx, cy = X((x0 + x1) / 2), Y((y0 + y1) / 2)

    def put(color, pts3):
        pts3 = np.asarray(pts3) - [cx, cy, 0]
        pts3[:, 1] *= -1  # y up for the viewer
        model.append({"color": color, "pts": np.round(pts3, 1).tolist()})

    for loop in profile:
        put(OUTLINE, np.column_stack([X(loop[:, 0]), Y(loop[:, 1]), np.zeros(len(loop))]))
    for i in ribs_kept:
        for loop in ribs[i]:
            put(rib_color[i], np.column_stack([np.full(len(loop), X(rib_x[i])), Y(loop[:, 1]), loop[:, 0] * scale]))
    for j in rings_kept:
        for loop in rings[j]:
            put(ring_color[j], np.column_stack([X(loop[:, 0]), np.full(len(loop), Y(ring_y[j])), loop[:, 1] * scale]))

    info = {
        "ribs": len(ribs_kept),
        "rings": len(rings_kept),
        "pages": len(pages),
        "size_mm": [round((x1 - x0) * scale, 1), round((y1 - y0) * scale, 1)],
        "params": {k: P[k] for k in ("detail", "ribs", "rings", "thickness", "size_cm", "paper", "stack", "features")},
    }
    return Template(pages, warnings, info, model)
