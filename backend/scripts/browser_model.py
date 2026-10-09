"""Make the background-removal model that runs in the browser (frontend/src/lib/cutout.ts).

It's rembg's isnet-general-use, the model the server runs, with its training-only outputs removed and its weights
stored as 16-bit floats: half the size (~90 MB) and the same masks (on 16 test photos, the final outlines were
within 1 px at the 600 px working size).

Run from backend/ for local development (the Docker build makes its own copy):
    .venv/bin/python -m pip install -r requirements-dev.txt   # once
    .venv/bin/python scripts/browser_model.py
Writes frontend/public/models/isnet-general-use-fp16-v1.onnx, which git ignores. Pass --src to convert a copy of
isnet-general-use.onnx that's already on disk instead of downloading it.
"""
from __future__ import annotations

import argparse
import hashlib
import tempfile
import urllib.request
import warnings
from pathlib import Path

import numpy as np
import onnx
from onnx.utils import extract_model
from onnxconverter_common import float16

URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx"
MD5 = "fc16ebd8b0c10d971d3513d564d01e29"  # the checksum rembg uses
NAME = "isnet-general-use-fp16-v1.onnx"  # must match MODEL_URL in frontend/src/lib/cutout.ts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, help="isnet-general-use.onnx on disk (default: download it)")
    ap.add_argument("--out", type=Path, help="where to write it (default: frontend/public/models/ in this repo)")
    a = ap.parse_args()
    a.out = a.out or Path(__file__).resolve().parents[2] / "frontend" / "public" / "models" / NAME

    with tempfile.TemporaryDirectory() as tmp:
        src = a.src or Path(tmp) / "isnet-general-use.onnx"
        if not a.src:
            print(f"Downloading {URL}")
            urllib.request.urlretrieve(URL, src)
        md5 = hashlib.md5(src.read_bytes()).hexdigest()
        if md5 != MD5:
            raise SystemExit(f"{src}: unexpected checksum {md5} (expected {MD5})")

        # The model has 11 extra outputs used only in training; the mask is the first one.
        stripped = Path(tmp) / "stripped.onnx"
        extract_model(str(src), str(stripped), ["input_image"], ["output_image"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # it warns about every tiny weight it rounds to fp16's smallest value
            model = float16.convert_float_to_float16(onnx.load(stripped), keep_io_types=True)

    onnx.checker.check_model(model)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, a.out)
    print(f"Wrote {a.out} ({a.out.stat().st_size / 1e6:.1f} MB, sha256 {sha256(a.out)[:16]}…)")
    check(a.out)


def check(path: Path):
    """Fail loudly if the converted model doesn't run or its input and output have changed."""
    try:
        import onnxruntime as ort
    except ImportError:
        return
    s = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    (out,) = s.run(None, {"input_image": np.zeros((1, 3, 1024, 1024), np.float32)})
    assert out.shape == (1, 1, 1024, 1024) and out.dtype == np.float32, (out.shape, out.dtype)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
