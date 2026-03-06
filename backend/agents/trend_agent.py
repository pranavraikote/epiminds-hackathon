import json
from agents.base import BaseAgent


class TrendAgent(BaseAgent):
    name = "trend_agent"
    role = "Search Trend Analyst"
    focus = "Search interest momentum — who is rising, who is falling, what timing signals say"

    def _build_prompt(self, state: dict) -> str:
        brief = state["brief"]
        trends = state.get("live_data", {}).get("trends", {})
        prior = self._format_prior_observations(state)

        return f"""You are a Search Trend Analyst. You interpret Google Trends data to detect momentum shifts.

BRAND TARGET:
{json.dumps(brief, indent=2)}

LIVE SEARCH TREND DATA:
{json.dumps(trends, indent=2)}

PRIOR TEAM OBSERVATIONS (build on these, don't repeat):
{prior}

Analyze search momentum. Look for: rising vs falling interest, category timing, competitor momentum.
If other agents have posted observations, react explicitly — especially if trends confirm or contradict what they found.

Return JSON only:
{{
  "agent": "trend_agent",
  "observation": "What the search trend data reveals",
  "momentum": "rising / falling / stable with context",
  "timing_insight": "Is now a good or bad time to advertise? Why?",
  "competitor_comparison": "How does product search compare to competitor",
  "campaign_implication": "What this means for campaign timing and spend",
  "builds_on": [],
  "confidence": 0.0
}}"""
