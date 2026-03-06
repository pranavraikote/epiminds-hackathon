import time
import httpx

HN_API = "https://hn.algolia.com/api/v1/search"


def fetch_hn_mentions(product: str, limit: int = 30) -> dict:
    try:
        since = int(time.time()) - (7 * 24 * 3600)  # last 7 days
        params = {
            "query": product,
            "tags": "story,comment",
            "numericFilters": f"created_at_i>{since}",
            "hitsPerPage": limit,
        }
        r = httpx.get(HN_API, params=params, timeout=10)
        r.raise_for_status()
        hits = r.json().get("hits", [])

        posts = [
            {
                "title": h.get("title") or h.get("comment_text", "")[:120],
                "points": h.get("points", 0),
                "num_comments": h.get("num_comments", 0),
                "type": "story" if h.get("title") else "comment",
                "url": h.get("url", ""),
            }
            for h in hits
            if h.get("title") or h.get("comment_text")
        ]

        top = sorted(posts, key=lambda x: x["points"] or 0, reverse=True)[:10]

        return {
            "_source": "live",
            "product": product,
            "total_mentions": len(posts),
            "top_posts": top,
        }
    except Exception as e:
        return _fallback(product, str(e))


def _fallback(product: str, reason: str = "") -> dict:
    return {
        "_source": "cached",
        "product": product,
        "total_mentions": 0,
        "top_posts": [],
        "_fallback_reason": reason,
    }
