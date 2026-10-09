"""HTTP API. Run with:  uvicorn app.main:app --reload"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import UnidentifiedImageError
from pydantic import BaseModel, Field

from .cache import PreparedCache
from .limits import RateLimiter
from .pipeline import Prepared, build_template, prepare, preview_png
from .render import page_svg, pages_pdf

MAX_UPLOAD = 25 * 1024 * 1024
# Background removal uses every core and ~1.5 GB, so uploads that need it run this many at a time...
SEGMENT_CONCURRENCY = int(os.environ.get("SEGMENT_CONCURRENCY", "1"))
# ...and at most this many (running + waiting) before new ones are turned away.
MAX_QUEUED = int(os.environ.get("SEGMENT_MAX_QUEUED", "20"))

app = FastAPI(title="Trace 3D Pen")
cache = PreparedCache(Path(os.environ.get("CACHE_DIR") or Path(tempfile.gettempdir()) / "skeleton3d-cache"))
upload_limit = RateLimiter((10, 60), (60, 3600))
build_limit = RateLimiter((240, 60))
_segment_slots = asyncio.Semaphore(SEGMENT_CONCURRENCY)
_queued = 0


def _client(request: Request) -> str:
    # uvicorn's --proxy-headers sets this from Caddy's X-Forwarded-For.
    return request.client.host if request.client else "unknown"


def _get(image_id: str) -> Prepared:
    prep = cache.get(image_id)
    if prep is None:
        raise HTTPException(404, "This photo has expired. Please upload it again.")
    return prep


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


def _prepare_and_store(image_id: str, data: bytes, mask_data: bytes | None) -> Prepared:
    prep = prepare(data, mask_data)
    cache.put(image_id, prep)
    return prep


async def _prepare(image_id: str, data: bytes, mask_data: bytes | None) -> Prepared:
    try:
        return await run_in_threadpool(_prepare_and_store, image_id, data, mask_data)
    except UnidentifiedImageError:
        raise HTTPException(400, "That file isn't an image we can read. Try a JPG or PNG.")
    except ValueError as e:
        raise HTTPException(422, f"{e} Try a photo with one clear object on a plain background.")


async def _prepare_queued(image_id: str, data: bytes, request: Request) -> Prepared:
    """Background removal on the server: one at a time, with a bounded queue."""
    global _queued
    if _queued >= MAX_QUEUED:
        raise HTTPException(503, "Lots of people are using this right now. Please try again in a minute.")
    _queued += 1
    try:
        async with _segment_slots:
            if await request.is_disconnected():
                raise HTTPException(499, "Client left while waiting.")
            # The same photo may have finished while this one waited.
            return cache.get(image_id) or await _prepare(image_id, data, None)
    finally:
        _queued -= 1


@app.post("/api/segment")
async def segment(file: UploadFile, request: Request, mask: UploadFile | None = None):
    """`mask`: the cut-out, made in the browser. Without one, background removal runs here."""
    data = await file.read()
    mask_data = await mask.read() if mask is not None else None
    if len(data) > MAX_UPLOAD or len(mask_data or b"") > MAX_UPLOAD:
        raise HTTPException(413, "That photo is too large (max 25 MB).")
    h = hashlib.sha1(data)
    if mask_data is not None:
        h.update(b"\0mask\0" + mask_data)
    image_id = h.hexdigest()
    prep = cache.get(image_id)
    if prep is None:
        if not upload_limit.allow(_client(request)):
            raise HTTPException(429, "You've uploaded a lot of photos in a short time. Please wait a minute and try again.")
        if mask_data is None:
            prep = await _prepare_queued(image_id, data, request)
        else:
            prep = await _prepare(image_id, data, mask_data)
    png = base64.b64encode(preview_png(prep)).decode()
    return {"image_id": image_id, "preview": f"data:image/png;base64,{png}"}


def _build(req: TemplateRequest):
    return build_template(_get(req.image_id), req.params.model_dump())


def _check_build_limit(request: Request):
    if not build_limit.allow(_client(request)):
        raise HTTPException(429, "Too many requests. Please slow down for a moment.")


@app.post("/api/template")
async def template(req: TemplateRequest, request: Request):
    _check_build_limit(request)
    t = await run_in_threadpool(_build, req)
    return {
        "pages": [page_svg(p) for p in t.pages],
        "warnings": t.warnings,
        "info": t.info,
        "model": t.model,
    }


@app.post("/api/export")
async def export(req: TemplateRequest, request: Request):
    _check_build_limit(request)
    t = await run_in_threadpool(_build, req)
    pdf = pages_pdf(t.pages)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="trace3dpen-template.pdf"'},
    )


_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
