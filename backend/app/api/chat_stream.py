import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.services.classifier_service import classify_query


from app.db.database import get_db
from app.db import crud
from app.schemas.chat_schema import ChatRequest
from app.agents.orchestrator import run_agent

router = APIRouter(prefix="/chat", tags=["chat"])



@router.post("/stream")
async def chat_stream(req: ChatRequest, db: Session = Depends(get_db)):

    async def event_generator():
        session = crud.get_or_create_session(db, user_id=req.user_id, session_id=req.session_id)

        crud.add_message(db, session_id=session.id, role="user", content=req.message)
        crud.set_session_title_if_default(db, session.id, req.message)

        # classify intent
        intent = await classify_query(req.message)
        should_verify = bool(req.use_web) and intent == "FACTUAL"

        yield f"data: {json.dumps({'type':'session', 'session_id': session.id})}\n\n"

        answer, sources, verified, steps = await run_agent(
            db, user_id=req.user_id, session_id=session.id, user_message=req.message, use_web=should_verify
        )

        yield f"data: {json.dumps({'type':'steps', 'steps': steps})}\n\n"

        for ch in answer:
            yield f"data: {json.dumps({'type':'token', 'token': ch})}\n\n"

        crud.add_message(db, session_id=session.id, role="assistant", content=answer)

        final_payload = {"type": "final", "sources": sources}
        if should_verify:
            final_payload["verified"] = verified

        yield f"data: {json.dumps(final_payload)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
