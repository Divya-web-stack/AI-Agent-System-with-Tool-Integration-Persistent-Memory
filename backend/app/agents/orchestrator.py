from sqlalchemy.orm import Session
from app.services.search_service import web_search
from app.services.llm_service import generate_answer
from app.services.memory_service import build_context_from_memory
from app.services.verify_service import verify_answer
from app.services.facts_service import extract_facts
from app.db import crud
from app.services.memory_service import build_facts_context
from app.services.classifier_service import classify_query


def is_small_talk(text: str) -> bool:
    t = text.strip().lower()
    small = {"hi", "hello", "hey", "hii", "hiii", "yo", "good morning", "good evening", "good night"}
    return t in small or t.startswith("hi ") or t.startswith("hello ") or t.startswith("hey ")


async def run_agent(db: Session, user_id: str, session_id: int, user_message: str, use_web: bool):
    steps = []
    mode = await classify_query(user_message)
    steps.append(f"🧭 Intent: {mode}")
    
    small_talk = is_small_talk(user_message)
    
    if small_talk:
        # override behavior
        mode = "ADVISORY"     # no web
        steps.append("💬 Small-talk detected (no web, minimal memory).")

   
    
    sources = []
    search_context = ""

    # 1) Extract + store memory facts from user message
    if not small_talk:
        facts = await extract_facts(user_message)
        for f in facts:
            key = (f.get("key") or "").strip()
            value = (f.get("value") or "").strip()
            if key and value:
                crud.upsert_memory_fact(db, user_id=user_id, key=key, value=value)

    do_web = use_web and (mode == "FACTUAL")

  


    if do_web:
        steps.append("🔍 Searching the web…")
        results = await web_search(user_message)
        sources = [{"title": r["title"], "url": r["url"]} for r in results]
        search_context = "\n\n".join(
            [f"[{i+1}] {r['title']}\nURL: {r['url']}\nSnippet: {r.get('content','')}"
             for i, r in enumerate(results)]
        )
    else:
        steps.append("🧠 Using internal reasoning + memory (no web needed).")

    steps.append("🧠 Generating answer…")
    memory_context = build_context_from_memory(db, session_id=session_id, limit=8)
    facts_context = "" if small_talk else build_facts_context(db, user_id=user_id, limit=20)

    if mode == "FACTUAL":
        citation_rule = "- Use SEARCH RESULTS and add citations like [1], [2]."
    else:
        citation_rule = "- Do NOT use citations. Provide clean, structured answer."



    draft_prompt = f"""
You are a Live AI Assistant.

RULES:
{citation_rule}
- Use USER FACTS MEMORY to personalize answers.

USER FACTS MEMORY:
{facts_context}

CONVERSATION MEMORY:
{memory_context}

SEARCH RESULTS:
{search_context}

USER QUESTION:
{user_message}
""".strip()

    draft_answer = await generate_answer(draft_prompt)

    verified = False
    final_answer = draft_answer

    

    if do_web and search_context.strip():
        steps.append("✅ Verifying with multiple sources…")
        verified, final_answer = await verify_answer(draft_answer, search_context)
        if not verified:
            final_answer = "⚠️ Couldn’t fully verify with multiple sources.\n\n" + final_answer
    else:
        # Not a factual query, so we don't label as verified
        verified = False

    steps.append("📩 Done")
    return final_answer, sources, verified, steps
