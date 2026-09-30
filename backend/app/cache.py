"""Prepared uploads, kept on disk so they outlast the small in-memory LRU, restarts, and deploys."""
from __future__ import annotations

import os
import re
import tempfile
import threading
import time
from collections import OrderedDict
from pathlib import Path

import numpy as np

from .pipeline import Prepared

_ID = re.compile(r"[0-9a-f]{40}")  # sha1 hex; also keeps client-supplied ids out of the filesystem
_FIELDS = ("mask", "rgb", "sdf", "signed")


class PreparedCache:
    def __init__(self, directory: Path, ttl: float = 6 * 3600, memory: int = 8, prune_every: float = 600):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl  # seconds since last use
        self.memory = memory
        self.prune_every = prune_every
        self._mem: OrderedDict[str, Prepared] = OrderedDict()
        self._lock = threading.Lock()
        self._last_prune = 0.0

    def _path(self, image_id: str) -> Path:
        return self.dir / f"{image_id}.npz"

    def _remember(self, image_id: str, prep: Prepared):
        with self._lock:
            self._mem[image_id] = prep
            self._mem.move_to_end(image_id)
            while len(self._mem) > self.memory:
                self._mem.popitem(last=False)

    def get(self, image_id: str) -> Prepared | None:
        if not _ID.fullmatch(image_id):
            return None
        path = self._path(image_id)
        with self._lock:
            prep = self._mem.get(image_id)
        try:
            os.utime(path)  # mark as used, so active sessions aren't pruned
        except FileNotFoundError:
            return None  # pruned from disk; drop the memory copy too so it expires consistently
        if prep is None:
            try:
                with np.load(path, allow_pickle=False) as z:
                    prep = Prepared(**{k: z[k] for k in _FIELDS})
            except (OSError, ValueError, KeyError):
                return None
        self._remember(image_id, prep)
        return prep

    def put(self, image_id: str, prep: Prepared):
        if not _ID.fullmatch(image_id):
            raise ValueError("bad image id")
        self._remember(image_id, prep)
        fd, tmp = tempfile.mkstemp(dir=self.dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                np.savez_compressed(f, **{k: getattr(prep, k) for k in _FIELDS})
            os.replace(tmp, self._path(image_id))
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        self.prune()

    def prune(self, force: bool = False):
        now = time.time()
        if not force and now - self._last_prune < self.prune_every:
            return
        self._last_prune = now
        for p in self.dir.iterdir():
            try:
                if now - p.stat().st_mtime > self.ttl:
                    p.unlink()
            except FileNotFoundError:
                pass
