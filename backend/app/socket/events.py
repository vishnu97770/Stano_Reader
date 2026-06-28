import socketio


# ── Singleton reference to the Socket.IO server ──────────────────────────────
# Set once in main.py after create_socket_server() returns.
# Background tasks in ai.py call get_sio() to emit candidates_refined events.

_sio_instance: socketio.AsyncServer | None = None


def set_sio(server: socketio.AsyncServer) -> None:
    """Store the application-level Socket.IO server for use by background tasks."""
    global _sio_instance
    _sio_instance = server


def get_sio() -> socketio.AsyncServer | None:
    """Return the stored Socket.IO server, or None if not yet initialised."""
    return _sio_instance


def create_socket_server() -> socketio.AsyncServer:
    sio = socketio.AsyncServer(
        async_mode="asgi",
        cors_allowed_origins="*",
        logger=False,
        engineio_logger=False,
    )

    @sio.event
    async def connect(sid: str, environ: dict) -> None:  # type: ignore[type-arg]
        print(f"[socket] connected: {sid}")

    @sio.event
    async def disconnect(sid: str) -> None:
        print(f"[socket] disconnected: {sid}")

    @sio.event
    async def stroke_data(sid: str, data: dict) -> None:  # type: ignore[type-arg]
        stroke = data.get("stroke", {})
        stroke_id: str = stroke.get("id", "unknown")
        session_id: str = data.get("sessionId", "unknown")
        point_count: int = len(stroke.get("points", []))

        print(
            f"[socket] stroke | session={session_id} id={stroke_id} points={point_count}"
        )

        # Acknowledge receipt to the sender
        await sio.emit("stroke_ack", stroke_id, to=sid)

        # Broadcast the full payload to every other connected client.
        # skip_sid ensures the sender does not receive their own stroke back,
        # which prevents duplicate rendering on the drawing client.
        await sio.emit("stroke_broadcast", data, skip_sid=sid)

    return sio
