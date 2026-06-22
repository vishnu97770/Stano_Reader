import socketio


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
        await sio.emit("stroke_ack", stroke_id, to=sid)

    return sio
