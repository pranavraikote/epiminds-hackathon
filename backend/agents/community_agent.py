import json
from agents.base import BaseAgent


class CommunityAgent(BaseAgent):
    name = "community_agent"
    role = "Community Intelligence Specialist"
    focus = "What real users say on Reddit — pain points, love, switching signals"

    def _build_prompt(self, state: dict) -> str:
        brief = state["brief"]
        reddit = state.get("live_data", {}).get("reddit", {})
        prior = self._format_prior_observations(state)
        reddit_empty = reddit.get("_source") == "error" or not reddit.get("top_posts")

        if reddit_empty:
            empty_note = "\nNOTE: Reddit data is unavailable. Set done=true — you have no data source to contribute from.\n"
        else:
            empty_note = ""

        return f"""You are a Community Intelligence Specialist reading Reddit signals for a campaign team.

TARGET: {json.dumps(brief)}

REDDIT DATA:
{json.dumps(reddit, indent=2)}{empty_note}

PRIOR TEAM OBSERVATIONS:
{prior}

Extract what real users say: complaints, switching triggers, love, exact language patterns.
React explicitly to prior observations — agree, challenge, or extend with new evidence.
If Reddit data is unavailable, set done=true immediately — do not speculate without data.
Set "done" to true once you have no new insight beyond what's already captured.

Return JSON only:
{{
  "agent": "community_agent",
  "observation": "What Reddit reveals right now — be specific, cite themes",
  "key_themes": ["theme1"],
  "switching_signals": ["signal1"],
  "user_language": ["exact phrase"],
  "campaign_implication": "Specific marketing implication",
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
