from app.services.llm_service import generate_answer

async def verify_answer(draft_answer: str, search_context: str) -> tuple[bool, str]:
    """
    Returns (verified, final_answer).
    The verifier must only trust search_context.
    """

    prompt = f"""
You are a strict fact-checker.

TASK:
- Check the DRAFT ANSWER using ONLY the SEARCH RESULTS.
- If at least TWO independent sources support the key claims, mark VERIFIED.
- If not, mark NOT_VERIFIED and rewrite a safer answer that only includes what is supported.

OUTPUT FORMAT (exactly):
STATUS: VERIFIED or NOT_VERIFIED
FINAL_ANSWER: <final answer text with citations like [1], [2]>
REASON: <1 short line why>

SEARCH RESULTS:
{search_context}

DRAFT ANSWER:
{draft_answer}
""".strip()

    result = await generate_answer(prompt)

    # Simple parsing (robust enough for MVP)
    status = "NOT_VERIFIED"
    final_answer = draft_answer

    for line in result.splitlines():
        if line.strip().startswith("STATUS:"):
            status = line.split("STATUS:", 1)[1].strip()
        if line.strip().startswith("FINAL_ANSWER:"):
            final_answer = line.split("FINAL_ANSWER:", 1)[1].strip()

    verified = (status.upper() == "VERIFIED")
    return verified, final_answer
