import hashlib
import json
import time

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.cache import cache_get, cache_set
from app.config import settings
from app.socket.events import create_socket_server, set_sio
from app.database import engine, Base, run_migrations, SessionLocal
from app.api.router import api_router
from recognizer.ai_context_engine import configure as configure_ai

# Import models so Base.metadata is populated before create_all
import app.models  # noqa: F401

_START_TIME = time.monotonic()
_VERSION = "0.1.0"

# Deterministic classifier paths whose POST responses are safe to cache.
_CACHED_PATHS = frozenset([
    "/api/classify-family",
    "/api/classify-symbol",
    "/api/classify-circle",
    "/api/classify-hook",
    "/api/classify-length",
    "/api/classify-position",
])


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """Cache POST responses for deterministic classifier endpoints."""

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST" or request.url.path not in _CACHED_PATHS:
            return await call_next(request)

        body = await request.body()
        cache_key = hashlib.sha256(
            f"{request.url.path}:{body.decode('utf-8', errors='replace')}".encode()
        ).hexdigest()

        cached = cache_get(cache_key)
        if cached is not None:
            return Response(
                content=json.dumps(cached),
                media_type="application/json",
                headers={"X-Cache": "HIT"},
            )

        # Re-attach the body so downstream handlers can read it
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request._receive = receive  # type: ignore[attr-defined]
        response = await call_next(request)

        if response.status_code == 200:
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            full_body = b"".join(chunks)
            try:
                cache_set(cache_key, json.loads(full_body))
            except Exception:
                pass
            return Response(
                content=full_body,
                status_code=response.status_code,
                headers=dict(response.headers) | {"X-Cache": "MISS"},
                media_type=response.media_type,
            )

        return response


Base.metadata.create_all(bind=engine)
run_migrations()

sio = create_socket_server()
set_sio(sio)
configure_ai(url=settings.ollama_url, model=settings.ollama_model, timeout=settings.ollama_timeout)

fastapi_app = FastAPI(
    title="Stano Reader API",
    version=_VERSION,
    description="Stenography recognition platform — stroke capture backend",
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
fastapi_app.add_middleware(ResponseCacheMiddleware)

fastapi_app.include_router(api_router)


@fastapi_app.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "version": _VERSION,
        "uptime_seconds": round(time.monotonic() - _START_TIME, 1),
    }


@fastapi_app.get("/ready")
async def readiness_check() -> JSONResponse:
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        pass

    ready = db_ok
    payload = {
        "ready": ready,
        "database": "ok" if db_ok else "unavailable",
        "details": {"sqlite": db_ok},
    }
    return JSONResponse(content=payload, status_code=200 if ready else 503)


# Mount FastAPI inside the Socket.IO ASGI app so both share one port
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
