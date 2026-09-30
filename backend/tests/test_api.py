import asyncio
import hashlib
import io
import os
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app import main
from app.cache import PreparedCache
from app.limits import RateLimiter
from app.pipeline import prepare_mask


def cutout_png(r=150, seed=0):
    """A transparent PNG, so /api/segment skips background removal."""
    img = Image.new("RGBA", (600, 500), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((300 - r, 250 - r * 0.8, 300 + r, 250 + r * 0.8), fill=(40, 90, 160 + seed, 255))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "cache", PreparedCache(tmp_path))
    monkeypatch.setattr(main, "upload_limit", RateLimiter((10, 60)))
    monkeypatch.setattr(main, "build_limit", RateLimiter((240, 60)))
    monkeypatch.setattr(main, "_segment_slots", asyncio.Semaphore(1))
    monkeypatch.setattr(main, "_queued", 0)
    return TestClient(main.app)


def upload(client, data):
    return client.post("/api/segment", files={"file": ("a.png", data, "image/png")})


def test_upload_then_template_and_export(client):
    r = upload(client, cutout_png())
    assert r.status_code == 200
    image_id = r.json()["image_id"]
    assert (main.cache.dir / f"{image_id}.npz").exists()

    t = client.post("/api/template", json={"image_id": image_id})
    assert t.status_code == 200 and t.json()["pages"]
    pdf = client.post("/api/export", json={"image_id": image_id})
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_upload_survives_a_restart(client, tmp_path, monkeypatch):
    image_id = upload(client, cutout_png()).json()["image_id"]
    monkeypatch.setattr(main, "cache", PreparedCache(tmp_path))  # fresh memory, same disk
    assert client.post("/api/template", json={"image_id": image_id}).status_code == 200


def test_unknown_or_malicious_ids_are_404(client):
    for image_id in ["0" * 40, "../../etc/passwd", "abc"]:
        r = client.post("/api/template", json={"image_id": image_id})
        assert r.status_code == 404
        assert "upload it again" in r.json()["detail"]


def test_not_an_image(client):
    r = upload(client, b"definitely not a picture")
    assert r.status_code == 400


def test_upload_rate_limit_skips_repeat_uploads(client):
    data = [cutout_png(seed=i) for i in range(11)]
    for d in data[:10]:
        assert upload(client, d).status_code == 200
    assert upload(client, data[0]).status_code == 200  # already processed: free
    r = upload(client, data[10])
    assert r.status_code == 429


def test_turns_uploads_away_when_queue_is_full(client, monkeypatch):
    monkeypatch.setattr(main, "_queued", main.MAX_QUEUED)
    assert upload(client, cutout_png()).status_code == 503


def test_cache_prunes_unused_entries(tmp_path):
    cache = PreparedCache(tmp_path, ttl=60)
    mask = np.zeros((50, 50), bool)
    mask[10:40, 10:40] = True
    old, fresh = hashlib.sha1(b"old").hexdigest(), hashlib.sha1(b"fresh").hexdigest()
    cache.put(old, prepare_mask(mask))
    cache.put(fresh, prepare_mask(mask))
    past = time.time() - 120
    os.utime(tmp_path / f"{old}.npz", (past, past))
    cache.prune(force=True)
    assert cache.get(old) is None
    assert cache.get(fresh) is not None


def test_rate_limiter_windows(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("app.limits.time.monotonic", lambda: now[0])
    rl = RateLimiter((2, 60), (3, 3600))
    assert rl.allow("a") and rl.allow("a")
    assert not rl.allow("a")  # 2 per minute
    assert rl.allow("b")  # per client
    now[0] += 61
    assert rl.allow("a")
    now[0] += 61
    assert not rl.allow("a")  # 3 per hour
