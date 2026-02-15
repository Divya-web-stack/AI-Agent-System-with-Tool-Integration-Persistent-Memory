from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.schemas.chat_schema import ChatRequest, ChatResponse, Source
from app.agents.orchestrator import run_agent

router = APIRouter(prefix="/chat", tags=["chat"])

@router.delete("/session/{session_id}")
def delete_chat_session(session_id: int, db: Session = Depends(get_db)):
    success = crud.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}




@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        session = crud.get_or_create_session(db, user_id=req.user_id, session_id=req.session_id)

        crud.add_message(db, session_id=session.id, role="user", content=req.message)
        crud.set_session_title_if_default(db, session.id, req.message)

        answer, sources, verified, steps = await run_agent(
            db, user_id=req.user_id, session_id=session.id, user_message=req.message, use_web=req.use_web
        )

        crud.add_message(db, session_id=session.id, role="assistant", content=answer)

        return ChatResponse(
            session_id=session.id,
            answer=answer,
            verified=verified,
            sources=[Source(**s) for s in sources],
            steps=steps
        )

    except Exception as e:
        # This will show the actual error message instead of plain 500
        raise HTTPException(status_code=500, detail=str(e))
