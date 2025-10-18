"""Simple in-memory rate limiter for API requests."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass(slots=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after: int | None = None


@dataclass(slots=True)
class RateLimiter:
    limit: int
    window_seconds: int
    blocked: int = 0
    _buckets: dict[str, deque[float]] = field(default_factory=dict)

    def allow(self, key: str) -> RateLimitDecision:
        now = time.monotonic()
        bucket = self._buckets.setdefault(key, deque())
        cutoff = now - self.window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            self.blocked += 1
            retry_after = int(max(1, round(bucket[0] + self.window_seconds - now)))
            return RateLimitDecision(allowed=False, remaining=0, retry_after=retry_after)
        bucket.append(now)
        remaining = max(0, self.limit - len(bucket))
        return RateLimitDecision(allowed=True, remaining=remaining)

    def snapshot(self) -> dict[str, int]:
        return {
            "limit": self.limit,
            "window_seconds": self.window_seconds,
            "active_keys": len(self._buckets),
            "blocked": self.blocked,
        }

    def reset(self) -> None:
        self.blocked = 0
        self._buckets.clear()
