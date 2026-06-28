"""
Tests for M18 — Production Release

Coverage (15 tests):
  Health endpoint (3):
    - GET /health returns 200 (1)
    - GET /health contains status ok (1)
    - GET /health contains uptime_seconds (1)

  Ready endpoint (3):
    - GET /ready returns 200 when db is up (1)
    - GET /ready response contains ready=True when db up (1)
    - GET /ready response contains database field (1)

  Cache module (7):
    - cache_get returns None for unknown key (1)
    - cache_set stores a value (1)
    - cache_get returns value after cache_set (1)
    - cache_get returns None after TTL expires (1)
    - LRU eviction when MAX_SIZE exceeded (1)
    - cache_clear resets store and counters (1)
    - cache_stats returns expected keys (1)

  ResponseCacheMiddleware (2):
    - Classifier endpoint returns X-Cache MISS on first call (1)
    - Classifier endpoint returns X-Cache HIT on second call (1)
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient

from app.cache import (
    MAX_SIZE,
    cache_clear,
    cache_get,
    cache_set,
    cache_stats,
)

# We import main indirectly via TestClient so the app is fully assembled.
# Use a deferred import to avoid touching app-level globals at module load.


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    cache_clear()
    yield
    cache_clear()


@pytest.fixture(scope="module")
def client():
    from app.main import fastapi_app
    with TestClient(fastapi_app, raise_server_exceptions=True) as c:
        yield c


# ── Health endpoint ────────────────────────────────────────────────────────────


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_status_ok(client):
    resp = client.get("/health")
    assert resp.json()["status"] == "ok"


def test_health_contains_uptime(client):
    resp = client.get("/health")
    data = resp.json()
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], (int, float))
    assert data["uptime_seconds"] >= 0


# ── Ready endpoint ─────────────────────────────────────────────────────────────


def test_ready_returns_200_when_db_available(client):
    resp = client.get("/ready")
    assert resp.status_code == 200


def test_ready_reports_ready_true(client):
    resp = client.get("/ready")
    data = resp.json()
    assert data["ready"] is True


def test_ready_contains_database_field(client):
    resp = client.get("/ready")
    data = resp.json()
    assert "database" in data
    assert data["database"] == "ok"


# ── Cache module ───────────────────────────────────────────────────────────────


def test_cache_get_unknown_key_returns_none():
    assert cache_get("nonexistent-key-xyz") is None


def test_cache_set_stores_value():
    cache_set("k1", {"word": "give"})
    assert cache_get("k1") == {"word": "give"}


def test_cache_get_returns_value_after_set():
    cache_set("k2", [1, 2, 3])
    result = cache_get("k2")
    assert result == [1, 2, 3]


def test_cache_get_returns_none_after_ttl(monkeypatch):
    import app.cache as cache_module

    # Patch time.monotonic to simulate time passing
    original = time.monotonic
    monkeypatch.setattr(cache_module, "TTL", 0.01)

    cache_set("expiring", "value")
    # Fast-forward time past TTL by patching monotonic
    start = original()

    def future_time():
        return start + 1.0  # 1 second in the future, past 0.01s TTL

    monkeypatch.setattr(time, "monotonic", future_time)
    assert cache_module.cache_get("expiring") is None


def test_cache_lru_eviction_when_max_size_exceeded(monkeypatch):
    import app.cache as cache_module

    monkeypatch.setattr(cache_module, "MAX_SIZE", 3)

    cache_set("a", 1)
    cache_set("b", 2)
    cache_set("c", 3)
    cache_set("d", 4)  # Should evict "a" (LRU)

    assert cache_module.cache_get("a") is None
    assert cache_module.cache_get("b") == 2
    assert cache_module.cache_get("d") == 4


def test_cache_clear_resets_store():
    cache_set("x", "hello")
    assert cache_get("x") == "hello"
    cache_clear()
    assert cache_get("x") is None


def test_cache_stats_returns_expected_keys():
    cache_set("stat-test", 42)
    cache_get("stat-test")       # hit
    cache_get("stat-missing")    # miss

    stats = cache_stats()
    assert "size" in stats
    assert "hits" in stats
    assert "misses" in stats
    assert "hit_rate" in stats
    assert "max_size" in stats
    assert "ttl_seconds" in stats
    assert stats["hits"] >= 1
    assert stats["misses"] >= 1


# ── ResponseCacheMiddleware ────────────────────────────────────────────────────


def _classify_family_payload():
    return {
        "stroke_id": "cache-test",
        "points": [
            {"x": 0, "y": 50, "timestamp": 1000},
            {"x": 50, "y": 50, "timestamp": 1050},
            {"x": 100, "y": 50, "timestamp": 1100},
        ],
    }


def test_classifier_endpoint_cache_miss_on_first_call(client):
    payload = _classify_family_payload()
    resp = client.post("/api/classify-family", json=payload)
    assert resp.status_code == 200
    assert resp.headers.get("x-cache") == "MISS"


def test_classifier_endpoint_cache_hit_on_second_call(client):
    payload = _classify_family_payload()
    # First call warms the cache
    client.post("/api/classify-family", json=payload)
    # Second call should be a HIT
    resp = client.post("/api/classify-family", json=payload)
    assert resp.status_code == 200
    assert resp.headers.get("x-cache") == "HIT"
