import asyncio
from data.reddit import fetch_reddit_sentiment
from data.trends import fetch_search_trends
from data.hackernews import fetch_hn_mentions
from data.producthunt import fetch_producthunt
from data.websearch import fetch_web_search


async def fetch_live_data(product: str, competitor: str = "") -> dict:
    """Fetch all live signals concurrently. Each fetcher has its own fallback."""

    keywords = [product] + ([competitor] if competitor else [])

    results = await asyncio.gather(
        asyncio.to_thread(fetch_reddit_sentiment, product),
        asyncio.to_thread(fetch_search_trends, keywords[:5]),
        asyncio.to_thread(fetch_hn_mentions, product),
        asyncio.to_thread(fetch_producthunt, product),
        asyncio.to_thread(fetch_web_search, product, competitor),
        return_exceptions=True,
    )

    keys = ["reddit", "trends", "hackernews", "producthunt", "web_search"]
    return {
        key: r if not isinstance(r, Exception) else {"_source": "error", "error": str(r)}
        for key, r in zip(keys, results)
    }
