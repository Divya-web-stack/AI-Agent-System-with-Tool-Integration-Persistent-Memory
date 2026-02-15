from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException


from app.db.database import get_db
from app.db import crud

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("")
def list_user_sessions(user_id: str, db: Session = Depends(get_db)):
    sessions = crud.list_sessions(db, user_id=user_id, limit=50)
    return [
        {"id": s.id, "title": s.title, "created_at": str(s.created_at)}
        for s in sessions
    ]

@router.get("/{session_id}/messages")
def get_messages(session_id: int, db: Session = Depends(get_db)):
    msgs = crud.get_session_messages(db, session_id=session_id, limit=200)
    return [
        {"role": m.role, "content": m.content, "created_at": str(m.created_at)}
        for m in msgs
    ]

from fastapi import HTTPException

@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    success = crud.delete_session(db, session_id=session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted successfully"}
