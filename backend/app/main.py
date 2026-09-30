"""HTTP API. Run with:  uvicorn app.main:app --reload"""
from __future__ import annotations

import base64
import hashlib
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import UnidentifiedImageError
from pydantic import BaseModel, Field

from .pipeline import Prepared, build_template, prepare, preview_png
from .render import page_svg, pages_pdf

MAX_UPLOAD = 25 * 1024 * 1024
CACHE_SIZE = 20

app = FastAPI(title="3D Pen Skeleton")
_cache: "OrderedDict[str, Prepared]" = OrderedDict()
_cache_lock = threading.Lock()


def _get(image_id: str) -> Prepared:
    with _cache_lock:
        prep = _cache.get(image_id)
        if prep is None:
            raise HTTPException(404, "Image not found or expired. Please upload it again.")
        _cache.move_to_end(image_id)
        return prep


def _put(image_id: str, prep: Prepared):
    with _cache_lock:
        _cache[image_id] = prep
        while len(_cache) > CACHE_SIZE:
            _cache.popitem(last=False)


class Params(BaseModel):
    detail: int = Field(3, ge=1, le=5)
    ribs: int | None = Field(None, ge=1, le=30)
    rings: int | None = Field(None, ge=0, le=10)
    thickness: float = Field(1.0, ge=0.2, le=3.0)
    size_cm: float = Field(15.0, ge=3.0, le=100.0)
    paper: Literal["a4", "letter"] = "a4"
    stack: bool = True
    features: bool = False


class TemplateRequest(BaseModel):
    image_id: str
    params: Params = Params()


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/segment")
async def segment(file: UploadFile):
    data = await file.read()
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "Image is too large (max 25 MB).")
    image_id = hashlib.sha1(data).hexdigest()
    with _cache_lock:
        prep = _cache.get(image_id)
    if prep is None:
        try:
            prep = await run_in_threadpool(prepare, data)
        except UnidentifiedImageError:
            raise HTTPException(400, "That file isn't an image we can read.")
        except ValueError as e:
            raise HTTPException(422, str(e))
        _put(image_id, prep)
    png = base64.b64encode(preview_png(prep)).decode()
    return {"image_id": image_id, "preview": f"data:image/png;base64,{png}"}


def _build(req: TemplateRequest):
    return build_template(_get(req.image_id), req.params.model_dump())


@app.post("/api/template")
async def template(req: TemplateRequest):
    t = await run_in_threadpool(_build, req)
    return {
        "pages": [page_svg(p) for p in t.pages],
        "warnings": t.warnings,
        "info": t.info,
        "model": t.model,
    }


@app.post("/api/export")
async def export(req: TemplateRequest):
    t = await run_in_threadpool(_build, req)
    pdf = pages_pdf(t.pages)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="skeleton-template.pdf"'},
    )


_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
