import io
import xml.etree.ElementTree as ET

import cv2
import numpy as np
import pytest
from PIL import Image

from app import slicer
from app.inflate import boxy, half_thickness
from app.pipeline import PANEL, PANEL_DEPTH, build_template, prepare, prepare_mask
from app.render import page_svg, pages_pdf


def disk(r=100, pad=20):
    n = 2 * (r + pad)
    yy, xx = np.mgrid[:n, :n]
    return (xx - n / 2 + 0.5) ** 2 + (yy - n / 2 + 0.5) ** 2 < r * r


def bar(w=400, h=100, pad=20):
    m = np.zeros((h + 2 * pad, w + 2 * pad), bool)
    m[pad:pad + h, pad:pad + w] = True
    return m


def snowman():
    m = np.zeros((420, 300), bool)
    cv2.circle(m.view(np.uint8), (150, 110), 70, 1, -1)
    cv2.circle(m.view(np.uint8), (150, 290), 110, 1, -1)
    return m


def test_inflated_disk_is_a_sphere():
    m = disk(100)
    h = half_thickness(m)
    c = m.shape[0] // 2
    assert h[c, c] == pytest.approx(100, rel=0.05)
    assert h[c, c + 50] == pytest.approx(np.sqrt(100**2 - 50**2), rel=0.06)


def test_inflated_bar_is_a_round_tube():
    # Infinite strip of half-width a gives depth sqrt(2) * a at the middle.
    m = bar(400, 100)
    h = half_thickness(m)
    assert h[70, 220] == pytest.approx(np.sqrt(2) * 50, rel=0.08)


def test_rib_through_disk_center_is_a_circle():
    prep = prepare_mask(disk(100))
    c = prep.mask.shape[1] / 2
    loops = slicer.rib_loops(prep.signed, c, 1.0)
    assert len(loops) == 1
    w, y = loops[0][:, 0], loops[0][:, 1]
    assert w.max() == pytest.approx(100, rel=0.06)
    assert w.min() == pytest.approx(-100, rel=0.06)
    assert y.max() - y.min() == pytest.approx(200, rel=0.03)


def test_rib_height_matches_profile_and_thickness_scales_depth():
    prep = prepare_mask(snowman())
    for x in (110.0, 150.0, 200.0):
        segs = slicer.column_intervals(prep.sdf, x)
        a, b = min(s[0] for s in segs), max(s[1] for s in segs)
        loops = slicer.rib_loops(prep.signed, x, 1.0)
        top = min(l[:, 1].min() for l in loops)
        bottom = max(l[:, 1].max() for l in loops)
        assert top == pytest.approx(a, abs=2.0)
        assert bottom == pytest.approx(b, abs=2.0)
        thin = slicer.rib_loops(prep.signed, x, 0.5)
        assert max(l[:, 0].max() for l in thin) == pytest.approx(
            0.5 * max(l[:, 0].max() for l in loops), rel=0.1)


def test_rib_through_two_parts_gives_two_loops():
    m = np.zeros((300, 200), bool)
    m[20:120, 40:160] = True
    m[180:280, 40:160] = True
    prep = prepare_mask(m)
    assert len(slicer.rib_loops(prep.signed, 100.0, 1.0)) == 2


@pytest.mark.parametrize("detail", [1, 3, 5])
def test_template_renders(detail):
    prep = prepare_mask(snowman())
    t = build_template(prep, {"detail": detail, "size_cm": 12, "features": True})
    assert t.info["ribs"] >= 3
    assert max(t.info["size_mm"]) == pytest.approx(120, abs=0.5)
    for p in t.pages:
        ET.fromstring(page_svg(p))  # well-formed
    assert pages_pdf(t.pages).startswith(b"%PDF")
    assert not t.warnings


def test_more_detail_means_more_ribs():
    prep = prepare_mask(snowman())
    counts = [build_template(prep, {"detail": d}).info["ribs"] for d in (1, 3, 5)]
    assert counts == sorted(counts) and counts[0] < counts[-1]


def test_round_shape_is_unchanged():
    prep = prepare_mask(snowman())
    today = build_template(prep, {})
    # Round ignores width and panels, which only apply to boxy shapes.
    t = build_template(prep, {"shape": 0, "width_cm": 20, "panels": True})
    assert t.model == today.model
    assert [page_svg(p) for p in t.pages] == [page_svg(p) for p in today.pages]
    assert t.info["width_cm"] is None


def test_boxy_ribs_have_flat_sides_at_the_width():
    prep = prepare_mask(bar())  # 400 x 100 px, like a car from the side
    half = 50.0
    flat_share = {}
    for name, field in (("round", prep.signed), ("boxy", boxy(prep.signed, half, 6.0))):
        (loop,) = slicer.rib_loops(field, 220.0, 1.0)
        w, y = np.abs(loop[:, 0]), loop[:, 1]
        near_max = y[w > 0.95 * w.max()]
        flat_share[name] = (near_max.max() - near_max.min()) / (y.max() - y.min())
        if name == "boxy":
            assert w.max() == pytest.approx(half, rel=0.03)
    assert flat_share["boxy"] > 0.6  # flat sides for most of the height
    assert flat_share["round"] < 0.4  # today's rounded cross section


def test_boxy_width_sets_depth_and_defaults_from_length():
    prep = prepare_mask(bar())
    t = build_template(prep, {"shape": 4, "size_cm": 40})  # 400 px long -> 1 mm per px
    assert t.info["width_cm"] == pytest.approx(16.0)  # 40% of the 40 cm length
    depth = max(abs(p[2]) for line in t.model for p in line["pts"])
    assert depth == pytest.approx(80.0, rel=0.03)
    # The width replaces the thickness slider.
    thin = build_template(prep, {"shape": 4, "size_cm": 40, "thickness": 0.3})
    assert thin.model == t.model
    wide = build_template(prep, {"shape": 4, "size_cm": 40, "width_cm": 30})
    assert max(abs(p[2]) for line in wide.model for p in line["pts"]) == pytest.approx(150.0, rel=0.03)


def test_side_panels():
    prep = prepare_mask(bar())
    t = build_template(prep, {"shape": 4, "size_cm": 40, "width_cm": 20, "panels": True})
    panels = [line for line in t.model if line["color"] == PANEL]
    assert len(panels) == 2  # one each side
    depths = sorted(line["pts"][0][2] for line in panels)
    assert depths[0] == pytest.approx(-depths[1])
    assert depths[1] == pytest.approx(PANEL_DEPTH * 100.0, rel=0.03)
    for line in panels:
        pts = np.asarray(line["pts"])
        assert np.ptp(pts[:, 2]) == 0  # flat, parallel to the photo
        assert np.ptp(pts[:, 0]) == pytest.approx(400.0, rel=0.06)  # about as long as the outline
    svg = "".join(page_svg(p) for p in t.pages)
    assert "Side panel: make 2" in svg and PANEL in svg
    assert all("won't fit" in w for w in t.warnings)  # 40 cm is bigger than A4, nothing else


def test_oversize_warns():
    prep = prepare_mask(snowman())
    t = build_template(prep, {"size_cm": 60})
    assert any("won't fit" in w for w in t.warnings)


def test_prepare_from_transparent_png():
    rgba = np.zeros((400, 300, 4), np.uint8)
    cv2.ellipse(rgba, (150, 200), (100, 160), 0, 0, 360, (40, 90, 200, 255), -1)
    buf = io.BytesIO()
    Image.fromarray(rgba).save(buf, "PNG")
    prep = prepare(buf.getvalue())
    ys, xs = np.nonzero(prep.mask)
    aspect = (ys.max() - ys.min()) / (xs.max() - xs.min())
    assert aspect == pytest.approx(1.6, rel=0.05)
