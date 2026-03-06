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
        ph_empty = not ph_data.get("posts")

        if ph_empty:
            empty_note = "\nNOTE: Product Hunt data is unavailable. Set done=true — you have no data source to contribute from.\n"
        else:
            empty_note = ""

        return f"""You are a Product Launch Analyst reading Product Hunt signals for a campaign team.

TARGET: {json.dumps(brief)}

PRODUCT HUNT DATA:
{json.dumps(ph_data, indent=2)}{empty_note}

PRIOR TEAM OBSERVATIONS:
{prior}

Read early adopter reception: vote momentum, resonant topics, how the product is pitched vs how users actually talk about it.
React to prior observations — especially where PH reception aligns or conflicts with Reddit/HN findings.
If Product Hunt data is empty or unavailable, set done=true immediately — do not speculate without a data source.
Set "done" to true once you have extracted all insights your data can support.

Return JSON only:
{{
  "agent": "review_agent",
  "observation": "What Product Hunt reception reveals about market fit — be specific",
  "reception_signal": "strong / moderate / weak — with reasons",
  "resonant_topics": ["topic1"],
  "positioning_gap": "How the product is pitched vs how users actually respond",
  "campaign_implication": "What early adopter signals mean for broader messaging",
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
