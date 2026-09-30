"""Per-client sliding-window rate limits, in memory (fine for one worker)."""
from __future__ import annotations

import threading
import time
from collections import deque


class RateLimiter:
    def __init__(self, *limits: tuple[int, float], max_clients: int = 10_000):
        """limits: (max requests, window seconds) pairs, e.g. (10, 60), (60, 3600)."""
        self.limits = limits
        self.window = max(w for _, w in limits)
        self.max_clients = max_clients
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """Record a request from `key` and return whether it's within every limit."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] > self.window:
                hits.popleft()
            for n, w in self.limits:
                if sum(1 for t in reversed(hits) if now - t <= w) >= n:
                    return False
            hits.append(now)
            if len(self._hits) > self.max_clients:
                self._forget_idle(now)
            return True

    def _forget_idle(self, now: float):
        for k in [k for k, h in self._hits.items() if not h or now - h[-1] > self.window]:
            del self._hits[k]
