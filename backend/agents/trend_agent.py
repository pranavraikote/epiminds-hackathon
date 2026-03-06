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
        trends_empty = trends.get("_source") == "error" or not trends.get("trend_direction")

        if trends_empty:
            empty_note = "\nNOTE: Google Trends data is unavailable. Set done=true — you have no data source to contribute from.\n"
        else:
            empty_note = ""

        return f"""You are a Search Trend Analyst reading momentum signals for a campaign team.

TARGET: {json.dumps(brief)}

GOOGLE TRENDS DATA:
{json.dumps(trends, indent=2)}{empty_note}

PRIOR TEAM OBSERVATIONS:
{prior}

Read momentum: rising/falling interest, timing windows, competitor trajectory.
React to prior observations — especially if trends confirm or contradict community/review findings.
If Trends data is unavailable, set done=true immediately — do not speculate without data.
Set "done" to true once you have no new momentum insight beyond what's already captured.

Return JSON only:
{{
  "agent": "trend_agent",
  "observation": "What search momentum reveals — be specific about direction and magnitude",
  "momentum": "rising / falling / stable — with numbers if available",
  "timing_insight": "Good or bad time to advertise, and why",
  "competitor_comparison": "Product vs competitor search trajectory",
  "campaign_implication": "Specific timing or spend recommendation",
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
