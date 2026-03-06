import os
from typing import List, Dict

_PROJECT = os.getenv("GCP_PROJECT_ID")


def analyze_snippets_sentiment(snippets: List[str]) -> Dict:
    """
    Run Google Cloud Natural Language API sentiment analysis over a batch of
    text snippets (e.g. Serper search results). Returns a summary dict with
    score, magnitude, label, and the most emotionally charged sentences.
    """
    snippets = [s for s in snippets if s and s.strip()]
    if not snippets:
        return {"score": 0.0, "magnitude": 0.0, "label": "neutral", "highlights": []}
    try:
        from google.cloud import language_v1
        client = language_v1.LanguageServiceClient()

        combined = " ".join(snippets[:12])  # cap to avoid quota burn
        document = language_v1.Document(
            content=combined,
            type_=language_v1.Document.Type.PLAIN_TEXT,
        )
        response = client.analyze_sentiment(
            request={"document": document, "encoding_type": language_v1.EncodingType.UTF8}
        )
        score = response.document_sentiment.score
        magnitude = response.document_sentiment.magnitude

        # Extract most emotionally charged sentences
        highlights = [
            s.text.content.strip()
            for s in sorted(
                response.sentences,
                key=lambda x: abs(x.sentiment.score) * (x.sentiment.magnitude + 0.1),
                reverse=True,
            )[:3]
            if len(s.text.content.strip()) > 20
        ]

        if score < -0.5:
            label = "strongly negative"
        elif score < -0.1:
            label = "negative"
        elif score < 0.1:
            label = "neutral"
        elif score < 0.5:
            label = "positive"
        else:
            label = "strongly positive"

        return {
            "score": round(score, 3),
            "magnitude": round(magnitude, 3),
            "label": label,
            "highlights": highlights,
        }
    except Exception:
        return {"score": 0.0, "magnitude": 0.0, "label": "neutral", "highlights": []}
