from agents.base import BaseAgent, _recent_range


class Strategist(BaseAgent):
    name = "strategist"
    role = "Campaign Strategist"
    focus = "Exploit high-intensity scents — translate signals into campaign weapons"

    wake_on = frozenset({"Price-War", "Viral-Heat", "Market-Void", "Sentiment-Bleed", "Feature-Gap", "Doubt"})
    wake_threshold = 0.70
    react_only = True  # never synthesises a near-empty blackboard

    def _search_queries(self, brief: dict) -> list[str]:
        product = brief.get("product", "")
        competitor = brief.get("competitor", "")
        date_range = _recent_range()
        queries = [
            f"{product} marketing campaign positioning differentiator {date_range}",
            f"{product} brand story challenger narrative",
        ]
        if competitor:
            queries.append(f"{product} vs {competitor} challenger strategy campaign {date_range}")
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
  "builds_on": <choose 1–3 from {self._format_buildable_scents(state)}, or [] if you are the first to act>,
  "done": false
}}

Set "done": true only on a reaction round (not your first) when your strategy fully accounts for all high-intensity signals on the trail and there is no new tension to exploit — your campaign thesis is complete."""
