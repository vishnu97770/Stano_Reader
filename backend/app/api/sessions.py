from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.schemas.session import SessionCreate, SessionDetail, SessionSummary
from app.schemas.stroke import StrokesBulkCreate, StrokesSavedResponse
from app.schemas.transcript import TranscriptSaveRequest, TranscriptSaveResponse
from app.services import session_service, stroke_service

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionSummary])
def list_sessions(db: DbSession = Depends(get_db)) -> list[SessionSummary]:
    return session_service.list_sessions(db)


@router.post("", response_model=SessionDetail, status_code=201)
def create_session(
    body: SessionCreate, db: DbSession = Depends(get_db)
) -> SessionDetail:
    return session_service.create_session(db, body)


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: str, db: DbSession = Depends(get_db)
) -> SessionDetail:
    session = session_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/strokes", response_model=StrokesSavedResponse, status_code=201)
def save_strokes(
    session_id: str,
    body: StrokesBulkCreate,
    db: DbSession = Depends(get_db),
) -> StrokesSavedResponse:
    if not session_service.get_session(db, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    count = stroke_service.save_strokes(db, session_id, body.strokes)
    session_service.touch_session(db, session_id)
    return StrokesSavedResponse(saved=count)


@router.patch("/{session_id}/transcript", response_model=TranscriptSaveResponse)
def save_transcript(
    session_id: str,
    body: TranscriptSaveRequest,
    db: DbSession = Depends(get_db),
) -> TranscriptSaveResponse:
    if not session_service.get_session(db, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    saved = session_service.save_transcript(db, session_id, body.words)
    return TranscriptSaveResponse(saved=saved)
