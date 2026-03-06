import asyncio
from agents.base import BaseAgent


class ScavengerSocial(BaseAgent):
    name = "scavenger_social"
    role = "Social Scavenger"
    focus = "Community sentiment, complaint clusters, feature gaps — what the crowd feels but rarely says clearly"

    async def _fetch_context(self, brief: dict) -> list[dict]:
        from data.nlp import analyze_snippets_sentiment
        serper = await super()._fetch_context(brief)
        snippets = [r["snippet"] for r in serper if r.get("snippet")]
        sentiment = await asyncio.to_thread(analyze_snippets_sentiment, snippets)
        if sentiment["score"] != 0.0 or sentiment["highlights"]:
            highlights_text = " | ".join(sentiment["highlights"][:2]) or "No highlights"
            serper.insert(0, {
                "title": f"NLP Sentiment — {sentiment['label'].upper()} (score {sentiment['score']:+.2f}, magnitude {sentiment['magnitude']:.1f})",
                "snippet": f"Most charged signals: {highlights_text}",
                "url": "",
            })
        return serper[:22]

    def _search_queries(self, brief: dict) -> list[str]:
        product = brief.get("product", "")
        competitor = brief.get("competitor", "")
        queries = [
            f"{product} user complaints community reviews 2025",
            f"{product} reddit users love hate frustration 2025",
        ]
        if competitor:
            queries.append(f"{competitor} missing features user complaints switching 2025")
        return queries

    def _build_prompt(self, state: dict, web_context: list[dict]) -> str:
        brief = state["brief"]
        prior = self._format_prior_observations(state)

        return f"""You are a Social Scavenger in a pheromone-guided intelligence swarm — a deep-pattern reader of collective human frustration.
Your drive: surface the emotional fault lines that show up in communities before they show up in market data. You read between the lines.
You hunt for: recurring complaint clusters, feature absences people are screaming for, brand trust erosion, the exact language angry users reach for.

TARGET: {self._format_brief(brief)}

LIVE COMMUNITY & SENTIMENT DATA (NLP-scored and web-scraped):
{self._format_web_context(web_context)}

PHEROMONE TRAIL — prior swarm intelligence:
{prior}

MISSION:
1. Find the single deepest emotional fault line in the community around this target. Not the loudest complaint — the one that keeps coming back, the wound that never heals.
2. Classify it as one of:
   - Sentiment-Bleed: sustained negative sentiment toward a specific, nameable competitor weakness (what are users calling out by name?)
   - Feature-Gap: a specific capability users are pleading for that no competitor delivers (what exact thing do they say they wish existed?)
3. Score intensity 0.0–1.0:
   - 0.9–1.0: pattern appears across multiple platforms, verbatim frustration, tied to a product decision the company made
   - 0.7–0.8: consistent complaint across multiple threads, specific feature or behaviour named
   - 0.5–0.6: directional frustration, limited data
   - < 0.5: anecdotal or unclear

Pull exact language from the data. Quote real phrases. A marketer reading this should be able to write copy directly from your output.

Return JSON only:
{{
  "agent": "scavenger_social",
  "scent_type": "Sentiment-Bleed | Feature-Gap",
  "intensity": 0.0,
  "observation": "3–5 sentences of dense emotional intelligence. Name the platforms, the user segments, the specific product decisions causing the pain. Quote real language from the data.",
  "dominant_emotion": "The single most charged emotion — not 'frustration', be specific: 'betrayal over pricing change', 'rage at broken promise'",
  "tension": "The core unresolved contradiction the audience is living with — what they expected vs. what they got",
  "emotional_language": [
    "verbatim phrase or close paraphrase from community data",
    "verbatim phrase or close paraphrase from community data",
    "verbatim phrase or close paraphrase from community data"
  ],
  "platform_signals": ["Reddit: ...", "Twitter/X: ...", "Review sites: ..."],
  "campaign_exploit": "How a competing brand could weaponise this exact pain in a single campaign moment",
  "payload": {{
    "community_signal": "One line — the emotional wound another agent can aim a campaign at",
    "sentiment_score": "The NLP sentiment score from the data if available, e.g. -0.62"
  }},
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
