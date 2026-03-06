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
        hn_empty = hn.get("_source") == "error" or not hn.get("top_posts")

        if hn_empty:
            empty_note = "\nNOTE: HackerNews data is unavailable. Set done=true — you have no data source to contribute from.\n"
        else:
            empty_note = ""

        return f"""You are a Developer Conversation Analyst reading HackerNews for a campaign team.

TARGET: {json.dumps(brief)}

HACKERNEWS DATA:
{json.dumps(hn, indent=2)}{empty_note}

PRIOR TEAM OBSERVATIONS:
{prior}

Read how technical/professional users discuss this product: word-of-mouth, credibility, concerns, comparisons.
React to prior observations — especially where HN sentiment agrees or conflicts with Reddit/Product Hunt.
If HackerNews data is unavailable, set done=true immediately — do not speculate without data.
Set "done" to true once you have no new insight the team hasn't already captured.

Return JSON only:
{{
  "agent": "conversation_agent",
  "observation": "What the technical community is saying — cite specific themes or quotes",
  "sentiment": "positive / negative / mixed — with specific reasons",
  "credibility_signals": ["signal1"],
  "concerns": ["concern1"],
  "campaign_implication": "What this means for messaging to technical buyers",
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
