import json
from agents.base import BaseAgent


class ConversationAgent(BaseAgent):
    name = "conversation_agent"
    role = "Developer Conversation Analyst"
    focus = "HackerNews — technical and professional audience sentiment, word-of-mouth signals"

    def _build_prompt(self, state: dict) -> str:
        brief = state["brief"]
        hn = state.get("live_data", {}).get("hackernews", {})
        prior = self._format_prior_observations(state)

        return f"""You are a Developer Conversation Analyst. You read HackerNews to understand how technical and professional audiences talk about products.

BRAND TARGET:
{json.dumps(brief, indent=2)}

LIVE HACKERNEWS DATA:
{json.dumps(hn, indent=2)}

PRIOR TEAM OBSERVATIONS (build on these, don't repeat):
{prior}

Analyze how technical/professional users discuss this product. Look for: word-of-mouth signals,
credibility markers, concerns, comparisons to alternatives.
If other agents have posted observations, react — especially if HN sentiment aligns or conflicts with Reddit.

Return JSON only:
{{
  "agent": "conversation_agent",
  "observation": "What the technical community is saying",
  "sentiment": "positive / negative / mixed with context",
  "credibility_signals": ["signal1"],
  "concerns": ["concern1"],
  "campaign_implication": "What this means for messaging to professional/technical buyers",
  "builds_on": [],
  "confidence": 0.0
}}"""
