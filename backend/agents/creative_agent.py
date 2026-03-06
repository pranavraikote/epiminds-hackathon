from agents.base import BaseAgent


class CreativeAgent(BaseAgent):
    name = "creative_agent"
    role = "Creative Strategist"
    focus = "What story the data wants to tell — narrative hooks, angles, copy instincts"

    def _search_queries(self, brief: dict) -> list[str]:
        product = brief.get("product", "")
        competitor = brief.get("competitor", "")
        queries = [f"{product} marketing campaign advertising 2025", f"{product} brand positioning story"]
        if competitor:
            queries.append(f"{product} challenger brand vs {competitor}")
        return queries

    def _build_prompt(self, state: dict, web_context: list[dict]) -> str:
        brief = state["brief"]
        prior = self._format_prior_observations(state)

        return f"""You are a Creative Strategist. Translate signals into story.
Think in headlines, hooks, narratives, tensions worth dramatising. Ask: what campaign does this data demand?

TARGET: {self._format_brief(brief)}

LIVE SEARCH CONTEXT (fetched by you for this task):
{self._format_web_context(web_context)}

BLACKBOARD (what the swarm has observed so far):
{prior}

What narrative hook is latent here? What is the most surprising, memorable, or true thing a campaign could say?
Push back on obvious angles. Look for the counterintuitive read that makes people stop.
If prior agents have missed a creative angle hiding in the data, name it.

Return JSON only:
{{
  "agent": "creative_agent",
  "observation": "The narrative hiding in the data — the story that wants to be told",
  "hook": "The single sharpest opening line or campaign hook",
  "narrative_angle": "The story arc — what tension exists and how the product resolves it",
  "tone": "The right register: challenger, empathetic, provocative, authoritative, etc.",
  "headline_idea": "A rough headline that captures the angle",
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
