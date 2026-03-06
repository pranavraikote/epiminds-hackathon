import os
import praw

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "swarm-agency/1.0")


def fetch_reddit_sentiment(product: str, limit: int = 50) -> dict:
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return _fallback(product)

    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

        posts = []
        for post in reddit.subreddit("all").search(product, time_filter="week", limit=limit):
            posts.append({
                "title": post.title,
                "subreddit": post.subreddit.display_name,
                "score": post.score,
                "text_snippet": post.selftext[:200] if post.selftext else "",
            })

        if not posts:
            return _fallback(product)

        top_posts = sorted(posts, key=lambda x: x["score"], reverse=True)[:10]

        return {
            "_source": "live",
            "product": product,
            "total_mentions": len(posts),
            "top_posts": top_posts,
            "active_subreddits": list({p["subreddit"] for p in posts})[:8],
        }
    except Exception as e:
        result = _fallback(product)
        result["_fallback_reason"] = str(e)
        return result


def _fallback(product: str) -> dict:
    return {
        "_source": "cached",
        "product": product,
        "total_mentions": 0,
        "top_posts": [],
        "active_subreddits": [],
    }
