import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.socket.events import create_socket_server
from app.database import engine, Base
from app.api.router import api_router

# Import models so Base.metadata is populated before create_all
import app.models  # noqa: F401

Base.metadata.create_all(bind=engine)

sio = create_socket_server()

fastapi_app = FastAPI(
    title="Stano Reader API",
    version="0.1.0",
    description="Stenography recognition platform — stroke capture backend",
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(api_router)


@fastapi_app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


# Mount FastAPI inside the Socket.IO ASGI app so both share one port
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
