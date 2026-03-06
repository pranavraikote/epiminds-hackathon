import asyncio
from agents.base import BaseAgent


class ScavengerMarket(BaseAgent):
    name = "scavenger_market"
    role = "Market Scavenger"
    focus = "High-velocity market signals — prices, funding, launches, growth vectors"

    async def _fetch_context(self, brief: dict) -> list[dict]:
        from data.trends_bq import get_rising_terms
        serper = await super()._fetch_context(brief)
        keywords = [k for k in [brief.get("product", ""), brief.get("competitor", "")] if k]
        trends = await asyncio.to_thread(get_rising_terms, keywords)
        return (trends + serper)[:22]  # BigQuery trends first — highest-velocity signals

    def _search_queries(self, brief: dict) -> list[str]:
        product = brief.get("product", "")
        competitor = brief.get("competitor", "")
        queries = [
            f"{product} pricing strategy market share 2025",
            f"{product} growth funding revenue news 2025",
        ]
        if competitor:
            queries.append(f"{competitor} pricing strategy market moves 2025")
        return queries

    def _build_prompt(self, state: dict, web_context: list[dict]) -> str:
        brief = state["brief"]
        prior = self._format_prior_observations(state)

        return f"""You are a Market Scavenger in a pheromone-guided intelligence swarm — an elite signal hunter trained on market microstructure.
Your drive: detect and precisely quantify high-velocity market signals. You do not summarise. You excavate.
You hunt for: exact price points and deltas, funding rounds with amounts, product launch dates, MAU/ARR figures, market share percentages, ad spend shifts.

TARGET: {self._format_brief(brief)}

LIVE MARKET DATA (fetched autonomously — treat every data point as raw field intelligence):
{self._format_web_context(web_context)}

PHEROMONE TRAIL — prior swarm intelligence sorted by intensity:
{prior}

MISSION:
1. Identify the single strongest market signal from the live data above. Name it precisely — cite exact figures, dates, company names, and URLs from the sources.
2. Classify it as one of:
   - Price-War: pricing moves with exact amounts/percentages, race-to-bottom evidence, freemium expansions
   - Viral-Heat: search volume spikes (with %) , trending keywords, viral moments with reach estimates
   - Market-Void: a named competitor retreating, a customer segment with no dedicated solution, uncontested keyword territory
3. Score intensity 0.0–1.0 using this rubric:
   - 0.9–1.0: confirmed signal with multiple corroborating sources, < 30 days old, large magnitude
   - 0.7–0.8: strong signal, 1–2 sources, recent
   - 0.5–0.6: directional signal, older data or single source
   - < 0.5: weak or speculative

Be forensically specific. Vague observations score intensity < 0.4.

Return JSON only — every string field must contain specific data, not placeholders:
{{
  "agent": "scavenger_market",
  "scent_type": "Price-War | Viral-Heat | Market-Void",
  "intensity": 0.0,
  "observation": "3–5 sentences of dense market intelligence. Name companies, cite numbers, quote specific figures from the data. This is not a summary — it is a field report.",
  "top_signals": [
    "Signal 1 — exact stat, source, date",
    "Signal 2 — exact stat, source, date",
    "Signal 3 — exact stat, source, date"
  ],
  "momentum": "rising | falling | stable",
  "momentum_evidence": "Cite the specific data points that justify the momentum call",
  "competitive_implication": "What this signal means for the target brand's next 90 days",
  "payload": {{
    "signal_summary": "One punchy line — the signal another agent needs to hear to act on this",
    "magnitude": "Quantified — e.g. '34% search spike', '$2.1B funding', '40% price cut'"
  }},
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
