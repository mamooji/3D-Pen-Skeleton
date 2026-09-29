"""Load an uploaded photo and cut out its main object as a binary mask."""
from __future__ import annotations

import io
import threading

import cv2
import numpy as np
from PIL import Image, ImageOps

# Longest side (px) of the working mask that all geometry is computed on.
WORK_SIZE = 600
# Longest side the photo is reduced to before background removal.
INPUT_SIZE = 1024

_session = None
_session_lock = threading.Lock()


def load_image(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img)
    img.load()
    if max(img.size) > INPUT_SIZE:
        img.thumbnail((INPUT_SIZE, INPUT_SIZE), Image.LANCZOS)
    return img


def _alpha_mask(img: Image.Image) -> np.ndarray | None:
    """Use the image's own transparency if it already has a cut-out."""
    if img.mode not in ("RGBA", "LA", "PA") and "transparency" not in img.info:
        return None
    alpha = np.array(img.convert("RGBA"))[..., 3]
    transparent = (alpha < 128).mean()
    if 0.01 < transparent < 0.99:
        return alpha >= 128
    return None


def _rembg_mask(img: Image.Image) -> np.ndarray:
    global _session
    from rembg import new_session, remove

    with _session_lock:
        if _session is None:
            _session = new_session("isnet-general-use")
    out = remove(img.convert("RGB"), session=_session, only_mask=True)
    return np.array(out) >= 128


def _grabcut_mask(img: Image.Image) -> np.ndarray:
    """Fallback when rembg is unavailable: GrabCut seeded with a centered box."""
    rgb = np.array(img.convert("RGB"))[..., ::-1].copy()
    h, w = rgb.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    rect = (int(w * 0.05), int(h * 0.05), int(w * 0.9), int(h * 0.9))
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(rgb, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    return (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)


def extract_mask(img: Image.Image) -> np.ndarray:
    mask = _alpha_mask(img)
    if mask is not None:
        return mask
    try:
        return _rembg_mask(img)
    except ImportError:
        return _grabcut_mask(img)


def clean_mask(mask: np.ndarray) -> np.ndarray:
    """Keep the largest object, fill small holes and smooth jagged edges."""
    m = mask.astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n <= 1:
        raise ValueError("No object found in the image.")
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    m = (labels == largest).astype(np.uint8)
    area = int(m.sum())

    # Fill background islands that don't touch the border and are small;
    # big ones (e.g. the gap inside a mug handle) are real holes.
    n, labels, stats, _ = cv2.connectedComponentsWithStats(1 - m, connectivity=4)
    h, w = m.shape
    for i in range(1, n):
        x, y, bw, bh, a = stats[i]
        touches = x == 0 or y == 0 or x + bw == w or y + bh == h
        if not touches and a < 0.01 * area:
            m[labels == i] = 1

    k = max(3, int(round(max(h, w) * 0.006)) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel)
    if m.sum() == 0:
        raise ValueError("No object found in the image.")
    return m.astype(bool)


def crop_to_work(mask: np.ndarray, rgb: np.ndarray, pad_frac: float = 0.04):
    """Crop mask and image to the object's bounding box and rescale to WORK_SIZE."""
    ys, xs = np.nonzero(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    pad = int(round(max(y1 - y0, x1 - x0) * pad_frac)) + 2
    h, w = mask.shape
    # Pad with background so the object never touches the crop border.
    mpad = np.pad(mask, pad)
    rpad = np.pad(rgb, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    y0, y1, x0, x1 = y0, y1 + 2 * pad, x0, x1 + 2 * pad
    mc = mpad[y0:y1, x0:x1].astype(np.float32)
    rc = rpad[y0:y1, x0:x1]

    scale = WORK_SIZE / max(mc.shape)
    size = (max(1, round(mc.shape[1] * scale)), max(1, round(mc.shape[0] * scale)))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    mw = cv2.resize(mc, size, interpolation=interp) > 0.5
    rw = cv2.resize(rc, size, interpolation=interp)
    return mw, rw
