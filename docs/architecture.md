# Stano Reader — Architecture

## System Overview

```
Browser / Phone
      ↓
React Canvas (DrawingCanvas)
      ↓ Socket.IO WebSocket
FastAPI + python-socketio Backend
      ↓ (Phase 2)
RecognizerBase implementation
      ↓
English Text Output
```

## Frontend Layers

| Layer | Path | Responsibility |
|---|---|---|
| Types | `src/types/` | Shared contracts (Stroke, StrokePoint, socket events) |
| Services | `src/services/` | Socket.IO singleton |
| Hooks | `src/hooks/` | Canvas drawing logic, socket lifecycle |
| Components | `src/components/` | Pure UI rendering |
| Pages | `src/pages/` | State owner, composes components |

## Backend Layers

| Layer | Path | Responsibility |
|---|---|---|
| Config | `app/config.py` | Environment settings via pydantic-settings |
| Socket | `app/socket/` | Real-time stroke event handling |
| API | `app/api/` | REST endpoints (Phase 2) |
| Services | `app/services/` | Business logic (Phase 2) |
| Recognizer | `recognizer/` | AI engine interface (Phase 2) |

## Stroke Data Contract

```json
{
  "sessionId": "uuid",
  "stroke": {
    "id": "uuid",
    "points": [
      { "x": 120.5, "y": 340.2, "timestamp": 1718000000123 }
    ]
  }
}
```

Coordinates are in CSS pixel space (logical pixels, DPR-independent).

## AI Integration Seam

`backend/recognizer/base.py` defines `RecognizerBase` — an abstract class with
`recognize(strokes) -> str` and `is_ready() -> bool`. Any Phase 2 engine
(PyTorch, rule-based, etc.) subclasses this without touching the socket or API layers.
