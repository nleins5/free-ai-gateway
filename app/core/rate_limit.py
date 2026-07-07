"""
Lightweight in-memory rate limiter — no external dependencies.
Uses a sliding-window counter per client IP.
"""
import time
from collections import defaultdict
from typing import Dict, Tuple


class RateLimiter:
    """Simple sliding-window rate limiter keyed by client IP."""

    def __init__(self, requests_per_minute: int = 30, burst: int = 5):
        self.rpm = requests_per_minute
        self.burst = burst
        self._windows: Dict[str, list] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> Tuple[bool, dict]:
        """
        Check if a request from `client_ip` should be allowed.
        Returns (allowed: bool, info: dict with remaining/retry_after).
        """
        now = time.time()
        window = self._windows[client_ip]

        # Purge timestamps older than 60s
        cutoff = now - 60
        self._windows[client_ip] = window = [t for t in window if t > cutoff]

        if len(window) >= self.rpm:
            retry_after = int(window[0] - cutoff) + 1
            return False, {
                "remaining": 0,
                "retry_after": retry_after,
                "limit": self.rpm,
            }

        # Burst check: no more than `burst` requests in 2 seconds
        recent = [t for t in window if t > now - 2]
        if len(recent) >= self.burst:
            return False, {
                "remaining": max(0, self.rpm - len(window)),
                "retry_after": 2,
                "limit": self.rpm,
            }

        window.append(now)
        return True, {
            "remaining": max(0, self.rpm - len(window)),
            "retry_after": 0,
            "limit": self.rpm,
        }

    def cleanup(self):
        """Remove stale entries (call periodically if needed)."""
        now = time.time()
        cutoff = now - 120
        stale = [k for k, v in self._windows.items() if not v or v[-1] < cutoff]
        for k in stale:
            del self._windows[k]


# Global instance — shared across all endpoints
rate_limiter = RateLimiter(requests_per_minute=30, burst=5)
