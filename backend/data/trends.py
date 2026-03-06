import time
from pytrends.request import TrendReq


def fetch_search_trends(keywords: list[str]) -> dict:
    if not keywords:
        return _fallback(keywords)

    try:
        pt = TrendReq(hl="en-US", tz=360)
        # Limit to 5 keywords (Google Trends API constraint)
        kws = keywords[:5]
        pt.build_payload(kws, timeframe="now 7-d")
        time.sleep(1)  # avoid rate limiting

        interest_df = pt.interest_over_time()

        if interest_df.empty:
            return _fallback(keywords)

        # Compare last 24h vs prior 6 days
        recent = interest_df.tail(8).mean()
        earlier = interest_df.head(-8).mean() if len(interest_df) > 8 else interest_df.mean()

        trend_direction = {}
        for kw in kws:
            if kw not in interest_df.columns:
                continue
            r, e = recent.get(kw, 0), earlier.get(kw, 0)
            if e == 0:
                trend_direction[kw] = "no_data"
            elif r > e * 1.15:
                trend_direction[kw] = "rising"
            elif r < e * 0.85:
                trend_direction[kw] = "falling"
            else:
                trend_direction[kw] = "stable"

        return {
            "_source": "live",
            "keywords": kws,
            "trend_direction": trend_direction,
            "relative_interest": {kw: round(float(recent.get(kw, 0)), 1) for kw in kws},
        }
    except Exception as e:
        result = _fallback(keywords)
        result["_fallback_reason"] = str(e)
        return result


def _fallback(keywords: list[str]) -> dict:
    return {
        "_source": "cached",
        "keywords": keywords,
        "trend_direction": {},
        "relative_interest": {},
    }
