from agents.base import BaseAgent


class SentimentAgent(BaseAgent):
    name = "sentiment_agent"
    role = "Emotional Intelligence Analyst"
    focus = "How people actually feel — emotional temperature, tensions, desires beneath the surface"

    def _search_queries(self, brief: dict) -> list[str]:
        product = brief.get("product", "")
        competitor = brief.get("competitor", "")
        queries = [f"{product} community feedback complaints 2025", f"{product} users love hate 2025"]
        if competitor:
            queries.append(f"{competitor} frustration switching users 2025")
        return queries

    def _build_prompt(self, state: dict, web_context: list[dict]) -> str:
        brief = state["brief"]
        prior = self._format_prior_observations(state)

        return f"""You are an Emotional Intelligence Analyst. Read the emotional subtext beneath the data.
Not what people say, but what they feel. Look for fear, aspiration, frustration, pride, anxiety, delight, resentment.

TARGET: {self._format_brief(brief)}

LIVE SEARCH CONTEXT (fetched by you for this task):
{self._format_web_context(web_context)}

BLACKBOARD (what the swarm has observed so far):
{prior}

Dig into the emotional layer others miss. What is the dominant feeling driving behaviour right now?
Is what people say they want different from what they emotionally respond to?
If prior observations surface emotional signals, agree or challenge them with specific evidence.

Return JSON only:
{{
  "agent": "sentiment_agent",
  "observation": "The emotional truth beneath the data — what people feel, not just what they say",
  "dominant_emotion": "The single strongest emotional driver right now",
  "tension": "The core tension or unresolved feeling in the audience",
  "emotional_language": ["exact phrases that reveal feeling"],
  "campaign_implication": "What emotion a campaign should activate or resolve",
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
