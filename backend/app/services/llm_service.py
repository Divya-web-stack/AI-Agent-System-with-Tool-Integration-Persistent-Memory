from groq import AsyncGroq
from app.config import settings

DEFAULT_MODEL = "llama-3.3-70b-versatile"

_client = None

def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _client

async def generate_answer(prompt: str) -> str:
    if not settings.GROQ_API_KEY:
        return "GROQ_API_KEY missing in .env"

    try:
        client = _get_client()
        resp = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Keep answers clear and concise."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""

    except Exception as e:
        return f"[Groq Error] {e}"
