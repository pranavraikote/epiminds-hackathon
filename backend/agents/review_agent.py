import json
from agents.base import BaseAgent


class ReviewAgent(BaseAgent):
    name = "review_agent"
    role = "Product Launch Analyst"
    focus = "Product Hunt — launch reception, community votes, early adopter signals, market fit indicators"

    def _build_prompt(self, state: dict) -> str:
        brief = state["brief"]
        ph_data = state.get("live_data", {}).get("producthunt", {})
        prior = self._format_prior_observations(state)

        return f"""You are a Product Launch Analyst. You read Product Hunt data to understand how early adopters and the maker community receive a product — votes, comments, launch timing, and topic resonance.

BRAND TARGET:
{json.dumps(brief, indent=2)}

LIVE PRODUCT HUNT DATA:
{json.dumps(ph_data, indent=2)}

PRIOR TEAM OBSERVATIONS (build on these, don't repeat):
{prior}

Analyze Product Hunt reception. Look for: vote momentum, topic categories that resonate, tagline patterns,
how this product is positioned vs how users actually talk about it.
If other agents have posted observations, react — especially if PH reception aligns or conflicts with Reddit/HN findings.

Return JSON only:
{{
  "agent": "review_agent",
  "observation": "What Product Hunt reception reveals about market fit and positioning",
  "reception_signal": "strong / moderate / weak with context",
  "resonant_topics": ["topics that got traction"],
  "positioning_gap": "Difference between how the product is pitched vs how community responds",
  "campaign_implication": "What early adopter signals mean for broader campaign messaging",
  "builds_on": [],
  "confidence": 0.0
}}"""
