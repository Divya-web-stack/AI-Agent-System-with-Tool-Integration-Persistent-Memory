from sqlalchemy.orm import Session
from app.db import models

def get_or_create_session(db: Session, user_id: str, session_id: int | None) -> models.ChatSession:
    if session_id is not None:
        s = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
        if s:
            return s

    s = models.ChatSession(user_id=user_id, title="New Chat")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

def add_message(db: Session, session_id: int, role: str, content: str) -> models.ChatMessage:
    m = models.ChatMessage(session_id=session_id, role=role, content=content)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

def get_recent_messages(db: Session, session_id: int, limit: int = 10) -> list[models.ChatMessage]:
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.id.desc())
        .limit(limit)
        .all()[::-1]
    )

def upsert_memory_fact(db: Session, user_id: str, key: str, value: str):
    fact = (
        db.query(models.MemoryFact)
        .filter(models.MemoryFact.user_id == user_id, models.MemoryFact.key == key)
        .first()
    )
    if fact:
        fact.value = value
    else:
        fact = models.MemoryFact(user_id=user_id, key=key, value=value)
        db.add(fact)

    db.commit()
    db.refresh(fact)
    return fact

def get_memory_facts(db: Session, user_id: str, limit: int = 20) -> list[models.MemoryFact]:
    return (
        db.query(models.MemoryFact)
        .filter(models.MemoryFact.user_id == user_id)
        .order_by(models.MemoryFact.id.desc())
        .limit(limit)
        .all()
    )

def list_sessions(db: Session, user_id: str, limit: int = 30):
    return (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == user_id)
        .order_by(models.ChatSession.id.desc())
        .limit(limit)
        .all()
    )

def get_session_messages(db: Session, session_id: int, limit: int = 50):
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.id.asc())
        .limit(limit)
        .all()
    )

def set_session_title_if_default(db: Session, session_id: int, title: str):
    s = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not s:
        return

    if not s.title or s.title.strip().lower() in ["new chat", ""]:
        s.title = title.strip()[:60]
        db.commit()


def delete_session(db: Session, session_id: int):
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id
    ).first()

    if not session:
        return False

    db.delete(session)
    db.commit()
    return True

        


