from agents.base import BaseAgent


class SignalAgent(BaseAgent):
    name = "signal_agent"
    role = "Signal Analyst"
    focus = "What is actually happening — concrete facts, numbers, directions"

    def _search_queries(self, brief: dict) -> list[str]:
        product = brief.get("product", "")
        competitor = brief.get("competitor", "")
        queries = [f"{product} market growth revenue 2025", f"{product} news 2025"]
        if competitor:
            queries.append(f"{product} vs {competitor} market share 2025")
        return queries

    def _build_prompt(self, state: dict, web_context: list[dict]) -> str:
        brief = state["brief"]
        prior = self._format_prior_observations(state)

        return f"""You are a Signal Analyst. Strict factual extraction — no interpretation, no spin.
Surface what is concretely measurable: numbers, directions, volumes, exact phrases, titles.

TARGET: {self._format_brief(brief)}

LIVE SEARCH CONTEXT (fetched by you for this task):
{self._format_web_context(web_context)}

BLACKBOARD (what the swarm has observed so far):
{prior}

Extract only what the data actually says. Skip signals already captured accurately by prior agents. Disagree with prior facts if the evidence contradicts them.

Return JSON only:
{{
  "agent": "signal_agent",
  "observation": "Concrete signals — numbers, directions, exact phrases, volumes",
  "top_signals": ["signal with source and magnitude"],
  "momentum": "rising / falling / stable — cite the numbers",
  "gap": "What the data shows that prior agents haven't surfaced yet",
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
