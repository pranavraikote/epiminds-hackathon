from agents.base import BaseAgent, _recent_range


class Skeptic(BaseAgent):
    name = "skeptic"
    role = "Evidence Skeptic"
    focus = "Challenge the highest-intensity claim — surface counter-evidence, flag weak signals, rate confidence"

    # Only reacts — never forages blind. Waits for a strong signal to challenge.
    react_only = True
    wake_on = frozenset({
        "Price-War", "Viral-Heat", "Market-Void",
        "Sentiment-Bleed", "Feature-Gap", "Strategy",
    })
    wake_threshold = 0.72  # only challenges genuinely strong claims

    async def run(self, state: dict) -> dict:
        # Extract the claim to challenge before _fetch_context runs,
        # so _search_queries can build targeted counter-evidence queries.
        candidates = [
            o for o in state.get("observations", [])
            if o.get("status") == "success"
            and o.get("agent") not in ("user", "skeptic", "mutator", "audience_sniper")
        ]
        target = max(candidates, key=lambda x: x.get("intensity", 0), default=None)
        self._claim_to_challenge = (target.get("observation", "")[:120] if target else "")
        return await super().run(state)

    def _search_queries(self, brief: dict) -> list[str]:
        # _build_prompt stashes the claim being challenged on self before super().run() calls us
        claim = getattr(self, "_claim_to_challenge", "")
        product = brief.get("product", "")
        competitor = brief.get("competitor", "")
        date_range = _recent_range()

        if claim:
            return [
                f"{claim[:80]} counter evidence alternative explanation {date_range}",
                f"{product} {competitor} contradicts challenges {claim[:60]} {date_range}",
            ]
        return [
            f"{product} marketing claim debunked alternative evidence {date_range}",
        ]

    def _build_prompt(self, state: dict, web_context: list[dict]) -> str:
        brief = state["brief"]

        # Find the highest-intensity non-user, non-skeptic, non-strategy scent to challenge
        candidates = [
            o for o in state.get("observations", [])
            if o.get("status") == "success"
            and o.get("agent") not in ("user", "skeptic", "mutator", "audience_sniper")
        ]
        target = max(candidates, key=lambda x: x.get("intensity", 0), default=None)

        if target:
            claim_text = target.get("observation", "")
            claim_agent = target.get("agent", "unknown")
            claim_type = target.get("scent_type", "")
            claim_intensity = target.get("intensity", 0.7)
            # Stash so _search_queries can use it (called before _build_prompt in run())
            self._claim_to_challenge = claim_text[:120]
            builds_ref = f'["{claim_agent} | Round {target.get("round", 1)}"]'
        else:
            claim_text = "No specific claim to challenge yet."
            claim_agent = "none"
            claim_type = ""
            claim_intensity = 0.0
            self._claim_to_challenge = ""
            builds_ref = "[]"

        prior = self._format_prior_observations(state)

        return f"""You are an Evidence Skeptic in a pheromone-guided intelligence swarm — the agent that stress-tests every strong signal before it crystallises into strategy.
Your drive: find the counter-evidence, the alternative explanation, the inconvenient data point. You are not destructive — you are rigorous. A claim that survives your challenge is a claim worth building a campaign on.

TARGET: {self._format_brief(brief)}

HIGHEST-INTENSITY CLAIM TO CHALLENGE (deposited by {claim_agent}, type: {claim_type}, intensity: {claim_intensity:.2f}):
{claim_text}

COUNTER-EVIDENCE SEARCH RESULTS (fetched autonomously):
{self._format_web_context(web_context)}

FULL PHEROMONE TRAIL — for context:
{prior}

MISSION:
1. Evaluate the claim above against the counter-evidence search results.
2. Identify the single strongest piece of counter-evidence — the fact, signal, or data point that most challenges the claim.
3. Rate your challenge strength 0.0–1.0:
   - 0.9–1.0: strong counter-evidence found, claim is significantly overstated or wrong
   - 0.7–0.8: meaningful counter-evidence, claim holds but with important caveats
   - 0.5–0.6: weak counter-evidence, claim likely valid but not proven
   - < 0.5: no meaningful counter-evidence found — claim confirmed
4. Name what's MISSING from the claim — what it doesn't account for.

Be precise. Name sources. If you found nothing that challenges the claim, say so honestly and give a low intensity. False doubt is as harmful as false confidence.

Return JSON only:
{{
  "agent": "skeptic",
  "scent_type": "Doubt",
  "intensity": 0.0,
  "observation": "3–4 sentences. State what you were challenging and what you found. Name the counter-evidence precisely — cite the source, the figure, the date. End with your confidence verdict on the original claim.",
  "claim_challenged": "{claim_agent} — {claim_type}",
  "counter_evidence": "The single strongest piece of evidence that challenges the claim — specific, cited",
  "what_is_missing": "What the original claim doesn't account for — the blind spot",
  "challenge_strength": 0.0,
  "verdict": "overstated | partially valid | confirmed | unverifiable",
  "payload": {{
    "challenge_summary": "One line — what the Strategist and Mutator need to know before building on this signal",
    "confidence_adjustment": "Suggested intensity adjustment for the challenged scent — e.g. 'reduce to 0.55'"
  }},
  "builds_on": {builds_ref},
  "done": false
}}

Set "done": true only on a reaction round when you've already challenged the strongest claim and no new high-intensity scent on the trail warrants further investigation."""
