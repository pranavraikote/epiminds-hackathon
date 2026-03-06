from agents.base import BaseAgent


class FrictionAgent(BaseAgent):
    name = "friction_agent"
    role = "Switching Barrier Analyst"
    focus = "What stops people from switching — inertia, risk, trust gaps, objections"

    def _search_queries(self, brief: dict) -> list[str]:
        product = brief.get("product", "")
        competitor = brief.get("competitor", "")
        queries = [f"{product} switching costs lock-in problems 2025"]
        if competitor:
            queries.append(f"why people stay with {competitor} instead of {product}")
            queries.append(f"{product} vs {competitor} complaints reviews")
        else:
            queries.append(f"{product} why people don't switch adoption barriers")
        return queries

    def _build_prompt(self, state: dict, web_context: list[dict]) -> str:
        brief = state["brief"]
        prior = self._format_prior_observations(state)

        return f"""You are a Switching Barrier Analyst. Map what prevents people from moving.
Think in: switching costs, lock-in, risk aversion, status quo bias, trust deficits, objections.

TARGET: {self._format_brief(brief)}

LIVE SEARCH CONTEXT (fetched by you for this task):
{self._format_web_context(web_context)}

BLACKBOARD (what the swarm has observed so far):
{prior}

What is stopping people from switching? What keeps them with the competitor?
What would they have to give up, risk, or learn? Where is trust missing?
If prior agents have named barriers, validate or challenge them with evidence.

Return JSON only:
{{
  "agent": "friction_agent",
  "observation": "The real barriers preventing switching — specific and evidenced",
  "primary_barrier": "The single biggest obstacle to switching",
  "trust_gap": "Where the product hasn't earned trust yet",
  "competitor_lock_in": "What the competitor has that creates stickiness",
  "unlock": "What message or proof point would most reduce friction",
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
