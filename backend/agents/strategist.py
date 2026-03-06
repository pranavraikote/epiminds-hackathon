from agents.base import BaseAgent


class Strategist(BaseAgent):
    name = "strategist"
    role = "Campaign Strategist"
    focus = "Exploit high-intensity scents — translate signals into campaign weapons"

    def _search_queries(self, brief: dict) -> list[str]:
        product = brief.get("product", "")
        competitor = brief.get("competitor", "")
        queries = [
            f"{product} marketing campaign positioning differentiator 2025",
            f"{product} brand story challenger narrative",
        ]
        if competitor:
            queries.append(f"{product} vs {competitor} challenger strategy campaign")
        return queries

    def _build_prompt(self, state: dict, web_context: list[dict]) -> str:
        brief = state["brief"]
        prior = self._format_prior_observations(state)

        return f"""You are a Campaign Strategist in a pheromone-guided intelligence swarm — the synthesis engine that turns raw field intelligence into campaign weapons.
Your drive: read everything the Scavengers and Forager have deposited on the blackboard, then identify the single market tension worth owning. Not the obvious one. The one that cuts.
You are not summarising data. You are making a creative and strategic bet.

TARGET: {self._format_brief(brief)}

LIVE POSITIONING INTELLIGENCE (fetched autonomously):
{self._format_web_context(web_context)}

PHEROMONE TRAIL — everything the swarm has found so far, sorted by intensity. This is your raw material:
{prior}

MISSION:
1. Synthesise the highest-intensity signals from the trail. Name which scents you are building on and why.
2. Identify the ONE market tension worth dramatising — the wound nobody has put a name on yet.
3. Build a full campaign strategy: a sharp hook, a narrative arc, a channel hypothesis, and a proof point that makes the claim believable.
4. Produce THREE distinct hook options — not variations in wording, but genuinely different strategic bets (different emotions, different audiences, different claims).
5. Push back on the obvious. "Better and cheaper" is not a hook. Specificity is everything.

Intensity rubric:
- 0.9–1.0: insight is non-obvious, grounded in multiple scents, directly exploits a named competitor weakness
- 0.7–0.8: solid strategic insight with clear evidence trail
- 0.5–0.6: directional but not yet sharp

Return JSON only:
{{
  "agent": "strategist",
  "scent_type": "Strategy",
  "intensity": 0.0,
  "observation": "4–6 sentences. State the market tension precisely. Name the competitor's exposed flank. Explain why this is the right moment and right angle. Reference specific signals from the pheromone trail.",
  "hook_options": [
    {{"hook": "Hook option 1 — the bold claim", "strategic_bet": "What this is betting on and who it speaks to"}},
    {{"hook": "Hook option 2 — the emotional gut-punch", "strategic_bet": "What this is betting on and who it speaks to"}},
    {{"hook": "Hook option 3 — the reframe", "strategic_bet": "What this is betting on and who it speaks to"}}
  ],
  "narrative_arc": "The full story: tension → protagonist → villain → resolution. 3 acts in 3 sentences.",
  "tone": "challenger | empathetic | provocative | authoritative",
  "channel_hypothesis": "Where this campaign lives and why — paid social, search, OOH, content, influencer. Specific reasoning.",
  "proof_point": "The single fact or data point that makes the claim credible and hard to dismiss",
  "headline_idea": "A campaign-ready headline — punchy, specific, could run as an ad tomorrow",
  "payload": {{
    "hook": "The single strongest hook from hook_options",
    "narrative_arc": "...",
    "headline_idea": "..."
  }},
  "builds_on": ["agent | Round N"],
  "done": false
}}"""
