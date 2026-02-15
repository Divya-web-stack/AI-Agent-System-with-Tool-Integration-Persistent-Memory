import json
from app.services.llm_service import generate_answer

FACTS_PROMPT = """
Extract only stable user facts that are useful later (preferences, goals, project details).
Do NOT extract temporary info (today, current mood).
Return STRICT JSON only, in this format:
{
  "facts": [
    {"key": "fact_key", "value": "fact_value"},
    ...
  ]
}

If no facts found, return: {"facts":[]}
"""

async def extract_facts(user_message: str) -> list[dict]:
    prompt = f"{FACTS_PROMPT}\n\nUSER_MESSAGE:\n{user_message}"
    out = await generate_answer(prompt)

    # best-effort JSON parsing
    try:
        data = json.loads(out)
        return data.get("facts", [])
    except Exception:
        return []
