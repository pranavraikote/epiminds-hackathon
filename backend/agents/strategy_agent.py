from agents.base import BaseAgent


class StrategyAgent(BaseAgent):
    name = "strategy_agent"
    role = "Campaign Strategist"
    focus = "Cross-signal pattern recognition — where signals converge into a campaign angle"

    def _build_prompt(self, state: dict) -> str:
        brief = state["brief"]
        prior = self._format_prior_observations(state)

        return f"""You are a Campaign Positioning Specialist. Your domain is marketing strategy: how products win, how audiences are moved, what makes a campaign land.

TARGET: {self._format_brief(brief)}

WHAT THE TEAM HAS OBSERVED SO FAR:
{prior}

Your team has given you four analytical lenses on the same problem:
- signal_agent: the facts and momentum in the data
- sentiment_agent: the emotional temperature and hidden tensions
- friction_agent: the barriers that prevent switching
- creative_agent: the narrative hooks latent in the data

Your job is NOT to summarise them. Your job is to take the sharpest signal from each lens and forge it into a single decisive campaign position.
Where agents agree, that's signal strength. Where they disagree, pick a side and defend it.
Set "done" to true — this is your one shot.

Return JSON only:
{{
  "agent": "strategy_agent",
  "observation": "Your campaign positioning hypothesis — specific, opinionated, grounded in marketing logic",
  "campaign_angle": "The single strongest angle for a campaign right now",
  "target_emotion": "The core emotion or tension this campaign should activate",
  "positioning_recommendation": "How to position against the competitor specifically",
  "channel_hint": "Where this campaign should live and why",
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
