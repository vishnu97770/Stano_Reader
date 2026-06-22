import json

from sqlalchemy.orm import Session as DbSession

from app.models.stroke import StrokeEntry
from app.schemas.stroke import StrokeCreate


def save_strokes(db: DbSession, session_id: str, strokes: list[StrokeCreate]) -> int:
    entries = [
        StrokeEntry(
            id=s.id,
            session_id=session_id,
            points=json.dumps([p.model_dump() for p in s.points]),
            pen_color=s.pen_color,
            pen_width=s.pen_width,
        )
        for s in strokes
    ]
    db.add_all(entries)
    db.commit()
    return len(entries)
