import os
from typing import List, Dict

_PROJECT = os.getenv("GCP_PROJECT_ID")


def get_rising_terms(keywords: List[str], max_results: int = 8) -> List[Dict]:
    """
    Query BigQuery Google Trends public dataset for rising search terms
    matching the product/competitor keywords. Returns {title, snippet, url} dicts
    compatible with the standard web context format.
    """
    keywords = [k.strip() for k in keywords if k.strip()]
    if not keywords:
        return []
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=_PROJECT)

        conditions = " OR ".join(
            f"LOWER(term) LIKE '%{k.lower()}%'" for k in keywords
        )
        query = f"""
            SELECT term, week, percent_gain, rank
            FROM `bigquery-public-data.google_trends.top_rising_terms`
            WHERE ({conditions})
              AND refresh_date = (
                  SELECT MAX(refresh_date)
                  FROM `bigquery-public-data.google_trends.top_rising_terms`
              )
            ORDER BY percent_gain DESC
            LIMIT {max_results}
        """
        results = []
        for row in client.query(query).result():
            results.append({
                "title": f"Google Trends Rising — \"{row.term}\"",
                "snippet": (
                    f"Search interest up {row.percent_gain}% "
                    f"(week of {row.week}, national rank #{row.rank}). "
                    f"High-velocity keyword signal."
                ),
                "url": f"https://trends.google.com/trends/explore?q={row.term}",
            })
        return results
    except Exception:
        return []
