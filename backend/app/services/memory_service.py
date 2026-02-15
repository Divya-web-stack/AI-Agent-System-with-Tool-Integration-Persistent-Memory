from sqlalchemy.orm import Session
from app.db import crud

def build_context_from_memory(db: Session, session_id: int, limit: int = 8) -> str:
    msgs = crud.get_recent_messages(db, session_id=session_id, limit=limit)
    lines = []
    for m in msgs:
        lines.append(f"{m.role.upper()}: {m.content}")
    return "\n".join(lines)

def build_facts_context(db: Session, user_id: str, limit: int = 20) -> str:
    facts = crud.get_memory_facts(db, user_id=user_id, limit=limit)
    if not facts:
        return ""
    # show most recent first
    lines = [f"- {f.key}: {f.value}" for f in facts[::-1]]
    return "\n".join(lines)
