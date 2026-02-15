from app.services.llm_service import generate_answer

async def classify_query(user_message: str) -> str:
    """
    Returns one of: FACTUAL, ADVISORY, CREATIVE
    """
    prompt = f"""
Classify the user's message into EXACTLY one label:

FACTUAL = needs latest data / facts / definitions / current info / verification
ADVISORY = advice, recommendations, planning, how-to, suggestions (no need for web verification)
CREATIVE = writing, captions, ideas, stories, prompts, brainstorming

Return ONLY one word: FACTUAL or ADVISORY or CREATIVE

USER MESSAGE:
{user_message}
""".strip()

    label = (await generate_answer(prompt)).strip().upper()

    if "FACTUAL" in label:
        return "FACTUAL"
    if "CREATIVE" in label:
        return "CREATIVE"
    return "ADVISORY"
