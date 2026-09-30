"""Command line:  python -m app.cli photo.jpg -o template.pdf --detail 3 --size 15"""
from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import build_template, prepare, preview_png
from .render import page_svg, pages_pdf


def main():
    ap = argparse.ArgumentParser(description="Photo -> Trace 3D Pen template")
    ap.add_argument("image")
    ap.add_argument("-o", "--out", default="template.pdf")
    ap.add_argument("--detail", type=int, default=3, choices=range(1, 6))
    ap.add_argument("--size", type=float, default=15.0, help="longest side in cm")
    ap.add_argument("--thickness", type=float, default=1.0)
    ap.add_argument("--ribs", type=int)
    ap.add_argument("--rings", type=int)
    ap.add_argument("--paper", choices=["a4", "letter"], default="a4")
    ap.add_argument("--separate", action="store_true", help="draw each rib on its own")
    ap.add_argument("--features", action="store_true", help="include inner detail lines")
    ap.add_argument("--svg", action="store_true", help="also write page SVGs and a mask preview")
    a = ap.parse_args()

    prep = prepare(Path(a.image).read_bytes())
    t = build_template(prep, dict(
        detail=a.detail, size_cm=a.size, thickness=a.thickness, ribs=a.ribs, rings=a.rings,
        paper=a.paper, stack=not a.separate, features=a.features,
    ))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(pages_pdf(t.pages))
    if a.svg:
        out.with_suffix(".mask.png").write_bytes(preview_png(prep))
        for i, p in enumerate(t.pages, 1):
            out.with_suffix(f".p{i}.svg").write_text(page_svg(p), encoding="utf-8")
    print(f"Wrote {out}: {t.info['pages']} page(s), {t.info['ribs']} ribs, {t.info['rings']} rings, "
          f"{t.info['size_mm'][0]} x {t.info['size_mm'][1]} mm")
    for w in t.warnings:
        print("warning:", w)


if __name__ == "__main__":
    main()
