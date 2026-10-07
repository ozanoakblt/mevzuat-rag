"""
Basit, bagimliliksiz, bellek-ici kayan-pencere (sliding window) rate limiter.

/api/ask her cagrida 3 LLM istegi tetikledigi icin (cevap + applicability +
claim verifier), kontrolsuz istek API kotasini ve maliyeti hizla tuketebilir.
Tek surecli bir uygulama icin harici bir bagimlilik (slowapi/redis) gereksiz;
coklu-surec/coklu-makine dagitimda bu sinif yetersiz kalir (her surecin kendi
sayaci olur) - o durumda ters-proxy seviyesinde limit onerilir.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0, clock=time.monotonic):
        self.limit = limit
        self.window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> float | None:
        """
        Izin verilirse None doner ve istegi sayar. Limit asilmissa istegi
        SAYMAZ ve yeniden denemeden once beklenmesi gereken saniyeyi doner.
        """
        now = self._clock()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return max(self.window - (now - hits[0]), 0.0)
            hits.append(now)
            if len(self._hits) > 10_000:  # bellek sisme korumasi
                self._prune(now)
            return None

    def _prune(self, now: float) -> None:
        stale = [k for k, h in self._hits.items() if not h or now - h[-1] >= self.window]
        for k in stale:
            del self._hits[k]
