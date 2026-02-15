import httpx
from app.config import settings

TAVILY_URL = "https://api.tavily.com/search"

async def web_search(query: str):
    if not settings.TAVILY_API_KEY:
        return []

    payload = {
        "api_key": settings.TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "max_results": 5,
        "include_answer": False,
        "include_raw_content": False
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(TAVILY_URL, json=payload)
        r.raise_for_status()
        data = r.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", "")  # short snippet
        })
    return results
