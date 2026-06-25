import json
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session as DbSession

from app.models.session import WritingSession
from app.models.stroke import StrokeEntry
from app.schemas.session import SessionCreate, SessionDetail, SessionSummary
from app.schemas.stroke import StrokeResponse


def list_sessions(db: DbSession) -> list[SessionSummary]:
    sessions = (
        db.query(WritingSession)
        .order_by(WritingSession.updated_at.desc())
        .all()
    )
    result: list[SessionSummary] = []
    for s in sessions:
        count = (
            db.query(StrokeEntry)
            .filter(StrokeEntry.session_id == s.id)
            .count()
        )
        result.append(
            SessionSummary(
                id=s.id,
                name=s.name,
                created_at=s.created_at,
                updated_at=s.updated_at,
                stroke_count=count,
            )
        )
    return result


def create_session(db: DbSession, data: SessionCreate) -> SessionDetail:
    name = data.name.strip() or _default_name()
    record = WritingSession(id=str(uuid.uuid4()), name=name)
    db.add(record)
    db.commit()
    db.refresh(record)
    return SessionDetail(
        id=record.id,
        name=record.name,
        created_at=record.created_at,
        updated_at=record.updated_at,
        strokes=[],
    )


def get_session(db: DbSession, session_id: str) -> SessionDetail | None:
    record = (
        db.query(WritingSession)
        .filter(WritingSession.id == session_id)
        .first()
    )
    if not record:
        return None
    strokes = [StrokeResponse.model_validate(s) for s in record.strokes]
    try:
        transcript: list[str] = json.loads(record.transcript)
    except Exception:
        transcript = []
    return SessionDetail(
        id=record.id,
        name=record.name,
        created_at=record.created_at,
        updated_at=record.updated_at,
        strokes=strokes,
        transcript=transcript,
    )


def save_transcript(db: DbSession, session_id: str, words: list[str]) -> bool:
    rows = db.query(WritingSession).filter(WritingSession.id == session_id).update(
        {"transcript": json.dumps(words), "updated_at": datetime.now(UTC)}
    )
    db.commit()
    return rows > 0


def touch_session(db: DbSession, session_id: str) -> None:
    """Update updated_at when strokes are appended."""
    db.query(WritingSession).filter(WritingSession.id == session_id).update(
        {"updated_at": datetime.now(UTC)}
    )
    db.commit()


def _default_name() -> str:
    return datetime.now(UTC).strftime("Session %Y-%m-%d %H:%M")
