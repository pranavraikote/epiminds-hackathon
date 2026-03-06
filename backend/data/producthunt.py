import os
import httpx

PH_API = "https://api.producthunt.com/v2/api/graphql"
PH_TOKEN_URL = "https://api.producthunt.com/v2/oauth/token"
PH_CLIENT_ID = os.getenv("PRODUCTHUNT_CLIENT_ID", "")
PH_CLIENT_SECRET = os.getenv("PRODUCTHUNT_CLIENT_SECRET", "")
PH_TOKEN = os.getenv("PRODUCTHUNT_TOKEN", "")  # fallback: static developer token

QUERY = """
query SearchPosts($query: String!) {
  posts(query: $query, first: 10, order: VOTES) {
    edges {
      node {
        name
        tagline
        votesCount
        commentsCount
        createdAt
        topics {
          edges {
            node { name }
          }
        }
      }
    }
  }
}
"""


def _get_token() -> str:
    """Get access token via client credentials, falling back to static token."""
    if PH_CLIENT_ID and PH_CLIENT_SECRET:
        try:
            r = httpx.post(
                PH_TOKEN_URL,
                json={
                    "client_id": PH_CLIENT_ID,
                    "client_secret": PH_CLIENT_SECRET,
                    "grant_type": "client_credentials",
                },
                timeout=10,
            )
            r.raise_for_status()
            return r.json().get("access_token", "")
        except Exception:
            pass
    return PH_TOKEN


def fetch_producthunt(product: str) -> dict:
    token = _get_token()
    if not token:
        return _fallback(product)

    try:
        r = httpx.post(
            PH_API,
            json={"query": QUERY, "variables": {"query": product}},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        r.raise_for_status()
        edges = r.json().get("data", {}).get("posts", {}).get("edges", [])

        posts = []
        for edge in edges:
            node = edge["node"]
            posts.append({
                "name": node.get("name"),
                "tagline": node.get("tagline"),
                "votes": node.get("votesCount", 0),
                "comments": node.get("commentsCount", 0),
                "topics": [t["node"]["name"] for t in node.get("topics", {}).get("edges", [])],
                "launched": node.get("createdAt", "")[:10],
            })

        return {
            "_source": "live",
            "product": product,
            "total_results": len(posts),
            "posts": posts,
        }
    except Exception as e:
        result = _fallback(product)
        result["_fallback_reason"] = str(e)
        return result


def _fallback(product: str) -> dict:
    return {
        "_source": "cached",
        "product": product,
        "total_results": 0,
        "posts": [],
    }
