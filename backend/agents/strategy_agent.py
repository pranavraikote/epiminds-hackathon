import json
from agents.base import BaseAgent


class StrategyAgent(BaseAgent):
    name = "strategy_agent"
    role = "Campaign Strategist"
    focus = "Cross-signal pattern recognition — where signals converge into a campaign angle"

    def _build_prompt(self, state: dict) -> str:
        brief = state["brief"]
        prior = self._format_prior_observations(state)

        return f"""You are a Campaign Strategist. Your specialist skill is reading multiple signals simultaneously and identifying where they converge into a campaign insight that none of the signals reveal alone.

BRAND TARGET:
{json.dumps(brief, indent=2)}

ALL TEAM OBSERVATIONS SO FAR:
{prior}

In Round 1, you have no prior observations — form your own initial hypothesis about campaign strategy from the brief alone.
In Round 2+, your job is to identify convergence: where do the community, trend, conversation, and review signals point to the same thing?
A convergence is more valuable than any single signal.
Also flag divergences — where signals contradict each other.

You are NOT directing the other agents. You are a specialist adding your own perspective to shared state.

Return JSON only:
{{
  "agent": "strategy_agent",
  "observation": "Cross-signal pattern you identified",
  "convergences": ["where multiple agents agree and what it implies"],
  "divergences": ["where agents contradict and what the uncertainty means"],
  "campaign_angle": "The single strongest insight for a campaign, grounded in convergent signals",
  "positioning_recommendation": "How to position the product based on all signals",
  "builds_on": [],
  "confidence": 0.0
}}"""
