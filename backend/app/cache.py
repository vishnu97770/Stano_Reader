"""
Thread-safe LRU cache with per-entry TTL.

Used to memoize deterministic classifier endpoints — same stroke geometry
always produces the same result, so repeated calls are served from memory.

Configuration
─────────────
    MAX_SIZE : int   — max entries before LRU eviction (default 1000)
    TTL      : float — seconds before an entry expires (default 300 = 5min)

Public interface
────────────────
    cache_get(key: str) -> object | None
    cache_set(key: str, value: object) -> None
    cache_clear() -> None
    cache_stats() -> dict
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any

MAX_SIZE: int = 1000
TTL: float = 300.0  # 5 minutes

_lock = threading.Lock()
_store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
_hits: int = 0
_misses: int = 0


def cache_get(key: str) -> Any | None:
    global _hits, _misses
    with _lock:
        if key not in _store:
            _misses += 1
            return None
        value, expiry = _store[key]
        if time.monotonic() > expiry:
            del _store[key]
            _misses += 1
            return None
        # Move to end (most-recently-used)
        _store.move_to_end(key)
        _hits += 1
        return value


def cache_set(key: str, value: Any) -> None:
    with _lock:
        if key in _store:
            _store.move_to_end(key)
        _store[key] = (value, time.monotonic() + TTL)
        if len(_store) > MAX_SIZE:
            # Evict least-recently-used entry
            _store.popitem(last=False)


def cache_clear() -> None:
    global _hits, _misses
    with _lock:
        _store.clear()
        _hits = 0
        _misses = 0


def cache_stats() -> dict[str, int | float]:
    with _lock:
        total = _hits + _misses
        return {
            "size": len(_store),
            "max_size": MAX_SIZE,
            "hits": _hits,
            "misses": _misses,
            "hit_rate": round(_hits / total, 4) if total else 0.0,
            "ttl_seconds": TTL,
        }
