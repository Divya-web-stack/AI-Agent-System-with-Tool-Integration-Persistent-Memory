import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.schemas.chat_schema import ChatRequest
from app.agents.orchestrator import run_agent

router = APIRouter(prefix="/chat", tags=["chat"])



@router.post("/stream")
async def chat_stream(req: ChatRequest, db: Session = Depends(get_db)):

    async def event_generator():
        # 1) session
        session = crud.get_or_create_session(db, user_id=req.user_id, session_id=req.session_id)

        # 2) store user msg
        crud.add_message(db, session_id=session.id, role="user", content=req.message)
        crud.set_session_title_if_default(db, session.id, req.message)


        # 3) send session_id early
        yield f"data: {json.dumps({'type':'session', 'session_id': session.id})}\n\n"

        # 4) run agent (non-streaming LLM for now, but we stream output to UI)
        answer, sources, verified, steps = await run_agent(
            db, user_id=req.user_id, session_id=session.id, user_message=req.message, use_web=req.use_web
        )

        # 5) send steps
        yield f"data: {json.dumps({'type':'steps', 'steps': steps})}\n\n"

        # 6) stream answer character-by-character (simple + effective)
        for ch in answer:
            yield f"data: {json.dumps({'type':'token', 'token': ch})}\n\n"

        # 7) store assistant msg
        crud.add_message(db, session_id=session.id, role="assistant", content=answer)

        # 8) send final meta
        yield f"data: {json.dumps({'type':'final', 'verified': verified, 'sources': sources})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
