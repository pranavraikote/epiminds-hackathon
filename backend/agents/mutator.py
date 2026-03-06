from agents.base import BaseAgent


class Mutator(BaseAgent):
    name = "mutator"
    role = "Strategy Mutator"
    focus = "Evolve the highest-intensity Strategy scent into 3 more potent variations"

    def _search_queries(self, brief: dict) -> list[str]:
        return []  # Mutator reads from the blackboard only — no external foraging

    def _build_prompt(self, state: dict, web_context: list[dict]) -> str:
        brief = state["brief"]

        # Find highest-intensity Strategy scent on the blackboard
        strategy_scents = [
            o for o in state.get("observations", [])
            if o.get("scent_type") == "Strategy" and o.get("status") == "success"
        ]
        if not strategy_scents:
            # Fall back to highest-intensity successful scent of any type
            strategy_scents = [
                o for o in state.get("observations", [])
                if o.get("status") == "success" and o.get("agent") != "user"
            ]

        top = max(strategy_scents, key=lambda x: x.get("intensity", 0), default=None)

        if top:
            payload = top.get("payload", {})
            source_hook = payload.get("hook", top.get("observation", ""))
            source_agent = top.get("agent", "unknown")
            source_round = top.get("round", 1)
            source_intensity = top.get("intensity", 0.7)
            builds_ref = f'["{source_agent} | Round {source_round}"]'
        else:
            source_hook = "No strategy scent found — generate from the brief directly."
            source_agent = "none"
            source_round = 0
            source_intensity = 0.0
            builds_ref = '[]'

        prior = self._format_prior_observations(state)

        # Surface any real campaign performance data — these are the highest-value signals
        performance_scents = [
            o for o in state.get("observations", [])
            if o.get("scent_type") == "Performance" and o.get("status") == "success"
        ]
        performance_block = ""
        if performance_scents:
            lines = []
            for p in sorted(performance_scents, key=lambda x: x.get("round", 0)):
                payload = p.get("payload", {})
                lines.append(
                    f"  [{payload.get('hook_angle', '?').upper()}] angle: "
                    f"{payload.get('metric_value', '?')} {payload.get('metric_name', '?')} — {p.get('observation', '')}"
                )
            performance_block = (
                "\n\nREAL CAMPAIGN PERFORMANCE DATA (highest-priority signal — mutations must build on what worked):\n"
                + "\n".join(lines)
                + "\n"
            )

        return f"""You are a Strategy Mutator in a pheromone-guided intelligence swarm — the final evolution stage. You are a creative director, a copywriter, and a strategist in one.
Your drive: take the highest-intensity Strategy scent, read the entire pheromone trail, and produce campaign-ready creative mutations that a brand could run tomorrow.
You are not improving the hook. You are evolving it — different angles, different emotional registers, different audiences, different levels of aggression.

TARGET: {self._format_brief(brief)}

HIGHEST-INTENSITY STRATEGY SCENT (intensity: {source_intensity:.2f}, deposited by: {source_agent}):
{source_hook}

FULL PHEROMONE TRAIL — every signal the swarm collected:
{prior}{performance_block}

MISSION:
Produce 5 distinct campaign-ready mutations. Each must be genuinely different — not the same idea reworded, but a different creative bet.

The five angles:
1. **bold** — makes the biggest possible claim, maximally confident, nearly arrogant
2. **empathetic** — leads with the audience's pain, makes them feel seen before they feel sold to
3. **provocative** — challenges a belief the audience holds, creates productive discomfort
4. **data-driven** — grounds the hook in a specific number or fact from the pheromone trail
5. **cultural** — ties the hook to a cultural moment, trend, or shared reference the audience lives in

Rules:
- Each hook must be a single punchy line someone could run as an ad headline or opening line of copy
- Each hook must feel DIFFERENT from the others — test: could they run as competing A/B variants?
- The "reason" field must explain the specific audience psychology this variation exploits
- Pull from the full pheromone trail — the best mutations synthesise signals from multiple agents

Return JSON only (use {builds_ref} for builds_on):
{{
  "agent": "mutator",
  "scent_type": "Mutation",
  "intensity": 0.95,
  "observation": "3–4 sentences explaining what the swarm collectively found, which signals were strongest, and what creative direction the mutations pursue. This is the synthesis — the intelligence report headline.",
  "synthesis": "The single most important insight the swarm produced — the thing a CMO needs to hear",
  "payload": {{
    "source_hook": "The original strategy hook being evolved",
    "variations": [
      {{"hook": "...", "angle": "bold", "reason": "Specific audience psychology and why this registers", "media_fit": "Where this runs best — e.g. paid social, OOH, search"}},
      {{"hook": "...", "angle": "empathetic", "reason": "Specific audience psychology and why this registers", "media_fit": "Where this runs best"}},
      {{"hook": "...", "angle": "provocative", "reason": "Specific audience psychology and why this registers", "media_fit": "Where this runs best"}},
      {{"hook": "...", "angle": "data-driven", "reason": "Specific audience psychology and why this registers", "media_fit": "Where this runs best"}},
      {{"hook": "...", "angle": "cultural", "reason": "Specific audience psychology and why this registers", "media_fit": "Where this runs best"}}
    ],
    "ab_test_recommendation": "Which two variations to test first and why",
    "kill_signal": "What result in the first 48 hours would tell you to kill this campaign and pivot"
  }},
  "builds_on": {builds_ref},
  "done": true
}}"""
