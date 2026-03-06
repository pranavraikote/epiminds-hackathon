from agents.base import BaseAgent


class AudienceSniper(BaseAgent):
    name = "audience_sniper"
    role = "Audience Sniper"
    focus = "Identify micro-segments primed to convert — specific enough to drop straight into an ad platform"

    def _search_queries(self, brief: dict) -> list[str]:
        product = brief.get("product", "")
        queries = [
            f"{product} buyer persona demographics psychographics 2025",
            f"{product} early adopter profile who switches first",
            f"{product} target audience intent signals purchase triggers",
        ]
        return queries

    def _build_prompt(self, state: dict, web_context: list[dict]) -> str:
        brief = state["brief"]

        # Pull the richest scents from the trail for audience inference
        observations = state.get("observations", [])

        mutation_scent = next(
            (o for o in sorted(observations, key=lambda x: x.get("intensity", 0), reverse=True)
             if o.get("scent_type") == "Mutation" and o.get("status") == "success"),
            None
        )
        strategy_scent = next(
            (o for o in sorted(observations, key=lambda x: x.get("intensity", 0), reverse=True)
             if o.get("scent_type") == "Strategy" and o.get("status") == "success"),
            None
        )
        social_scent = next(
            (o for o in sorted(observations, key=lambda x: x.get("intensity", 0), reverse=True)
             if o.get("scent_type") in ("Sentiment-Bleed", "Feature-Gap") and o.get("status") == "success"),
            None
        )
        forager_scent = next(
            (o for o in sorted(observations, key=lambda x: x.get("intensity", 0), reverse=True)
             if o.get("scent_type") == "Market-Void" and o.get("status") == "success"),
            None
        )

        mutation_block = ""
        if mutation_scent:
            payload = mutation_scent.get("payload", {})
            variations = payload.get("variations", [])
            hooks_text = "\n".join(
                f"  [{v.get('angle', '?').upper()}] \"{v.get('hook', '')}\" — {v.get('reason', '')}"
                for v in variations
            )
            mutation_block = f"""
MUTATION SCENT — 5 campaign hooks ready for audience matching:
{hooks_text}
Synthesis: {mutation_scent.get('observation', '')}
"""

        strategy_block = ""
        if strategy_scent:
            payload = strategy_scent.get("payload", {})
            strategy_block = f"""
STRATEGY SCENT — market tension the campaign will own:
{strategy_scent.get('observation', '')}
Primary hook: {payload.get('hook', '')}
Channel hypothesis: {strategy_scent.get('channel_hypothesis', '')}
"""

        social_block = ""
        if social_scent:
            emotional_language = social_scent.get("emotional_language", [])
            social_block = f"""
SOCIAL SCENT — emotional fault lines in the community:
Dominant emotion: {social_scent.get('dominant_emotion', '')}
Tension: {social_scent.get('tension', '')}
Verbatim language: {' | '.join(emotional_language[:3])}
"""

        forager_block = ""
        if forager_scent:
            forager_block = f"""
FORAGER SCENT — uncontested market void:
Void: {forager_scent.get('void', '')}
Primary barrier: {forager_scent.get('primary_barrier', '')}
Unlock: {forager_scent.get('unlock', '')}
Void size: {forager_scent.get('void_size', '')}
"""

        prior = self._format_prior_observations(state)

        return f"""You are an Audience Sniper in a pheromone-guided intelligence swarm — a precision targeting specialist.
Your drive: read the full pheromone trail, especially the Mutation hooks and social fault lines, then identify exactly WHO should receive each hook and WHEN they are most receptive.
You are not describing demographics. You are naming specific, targetable micro-segments with the precision of a media buyer setting up an ad set.

TARGET: {self._format_brief(brief)}

LIVE AUDIENCE INTELLIGENCE:
{self._format_web_context(web_context)}
{mutation_block}{strategy_block}{social_block}{forager_block}

FULL PHEROMONE TRAIL:
{prior}

MISSION:
Identify 3 distinct micro-segments. Each must be:
1. Specific enough to target in Meta Ads, LinkedIn Campaign Manager, or Google DV360 today
2. Matched to a specific mutation hook from the trail (by angle)
3. Defined by a trigger event — the thing that happened in their life that makes them ready RIGHT NOW
4. Sized — give an honest estimate of addressable audience

For each segment, answer: who are they, what just happened to them, what do they feel, which hook lands, and how do you find them on a DSP.

Then name the "cold audience" — the segment most brands would target by default — and explain what the swarm found that makes a different segment the smarter beachhead.

Finally, give a sequencing recommendation: which segment do you activate first and why (think: who converts fastest, who builds social proof for the next segment, who has the highest LTV).

Intensity rubric:
- 0.9–1.0: 3 segments all grounded in pheromone trail signals, trigger events are specific and named, targeting layers are DSP-ready
- 0.7–0.8: strong segments but one is directional or targeting layer is vague
- 0.5–0.6: segments are demographic, not psychographic

Return JSON only:
{{
  "agent": "audience_sniper",
  "scent_type": "Audience",
  "intensity": 0.0,
  "observation": "4–5 sentences. Name the three segments. Explain what the pheromone trail revealed about WHO actually responds to this campaign vs. who the brief assumed. Call out the most surprising audience signal.",
  "segments": [
    {{
      "name": "Segment name — specific, not generic (e.g. 'Mid-market RevOps leads who just survived a merger')",
      "description": "Who they are: role, platform behavior, life stage, defining worldview in one sentence",
      "size": "Estimated addressable audience — be honest about uncertainty",
      "trigger": "The specific event or moment in their life that makes them ready to act RIGHT NOW",
      "pain_alignment": "Which signal from the pheromone trail (name the agent and scent) hits this segment hardest",
      "best_hook": "Which mutation hook angle (bold/empathetic/provocative/data-driven/cultural) lands best and why — quote the hook",
      "targeting_layer": "Exact targeting method: interest category, job title, behavior signal, lookalike seed, keyword cluster — specific enough to brief a media buyer",
      "conversion_window": "How long does their decision cycle run — days, weeks, months?"
    }},
    {{
      "name": "...",
      "description": "...",
      "size": "...",
      "trigger": "...",
      "pain_alignment": "...",
      "best_hook": "...",
      "targeting_layer": "...",
      "conversion_window": "..."
    }},
    {{
      "name": "...",
      "description": "...",
      "size": "...",
      "trigger": "...",
      "pain_alignment": "...",
      "best_hook": "...",
      "targeting_layer": "...",
      "conversion_window": "..."
    }}
  ],
  "cold_audience": "The segment the brand is probably targeting by default — and what the swarm found that makes it the wrong beachhead",
  "sequencing": "Activation order and rationale: which segment is the beachhead (fastest to convert, builds proof), which is the scale layer, which is the long-game",
  "payload": {{
    "primary_segment": "One line — the single highest-priority segment for immediate activation",
    "targeting_signal": "The one data point or behavioral signal that unlocks this segment in a DSP"
  }},
  "builds_on": ["{mutation_scent['agent'] + ' | Round ' + str(mutation_scent['round']) if mutation_scent else 'mutator | Round 3'}",
               "{strategy_scent['agent'] + ' | Round ' + str(strategy_scent['round']) if strategy_scent else 'strategist | Round 1'}"],
  "done": true
}}"""
