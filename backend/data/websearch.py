import os
import httpx

_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
_CX      = os.getenv("GOOGLE_SEARCH_CX", "")
_CSE_URL = "https://www.googleapis.com/customsearch/v1"


def search_raw(query: str, max_results: int = 6) -> list[dict]:
    """Single-query Google Custom Search. Returns a list of {title, snippet, url} dicts."""
    if not _API_KEY or not _CX:
        return []
    try:
        resp = httpx.get(
            _CSE_URL,
            params={"key": _API_KEY, "cx": _CX, "q": query, "num": min(max_results, 10)},
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return [
            {"title": i.get("title", ""), "snippet": i.get("snippet", ""), "url": i.get("link", "")}
            for i in items
        ]
    except Exception:
        return []
