import os
import httpx

_API_KEY    = os.getenv("SERPER_API_KEY", "")
_SERPER_URL = "https://google.serper.dev/search"


def search_raw(query: str, max_results: int = 10) -> list[dict]:
    """Single-query Serper (Google) search. Returns a list of {title, snippet, url} dicts."""
    if not _API_KEY:
        return []
    try:
        resp = httpx.post(
            _SERPER_URL,
            headers={"X-API-KEY": _API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": min(max_results, 10)},
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("organic", [])
        return [
            {"title": i.get("title", ""), "snippet": i.get("snippet", ""), "url": i.get("link", "")}
            for i in items
        ]
    except Exception:
        return []
