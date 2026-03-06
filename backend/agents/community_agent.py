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

        return f"""You are a Community Intelligence Specialist. You read Reddit to understand what real users think.

BRAND TARGET:
{json.dumps(brief, indent=2)}

LIVE REDDIT DATA:
{json.dumps(reddit, indent=2)}

PRIOR TEAM OBSERVATIONS (build on these, don't repeat):
{prior}

Analyze what the community is saying about this product and its competitors.
Look for: recurring complaints, switching triggers, things people love, language patterns.
If other agents have posted observations, explicitly react — agree, challenge, or extend.

Return JSON only:
{{
  "agent": "community_agent",
  "observation": "What Reddit is saying right now",
  "key_themes": ["theme1", "theme2"],
  "switching_signals": ["signal1"],
  "user_language": ["exact phrases users use"],
  "campaign_implication": "What this means for marketing",
  "builds_on": [],
  "confidence": 0.0
}}"""
