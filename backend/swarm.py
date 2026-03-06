import asyncio
import json
from typing import AsyncGenerator

from agents import all_agents
from agents.base import call_gemini
from data.fetcher import fetch_live_data
from state import get_state, update_state

MAX_ROUNDS = 3
CONVERGENCE_THRESHOLD = 0.75


async def run_swarm(campaign_id: str) -> AsyncGenerator[dict, None]:
    state = await get_state(campaign_id)
    if not state:
        yield {"type": "error", "message": "Campaign not found."}
        return

    brief = state["brief"]

    # Phase 1: fetch live data
    yield {"type": "status", "phase": "data", "message": "Fetching live market data..."}

    live_data = await fetch_live_data(
        product=brief["product"],
        competitor=brief.get("competitor", ""),
    )
    state["live_data"] = live_data
    state["status"] = "running"
    await update_state(campaign_id, state)

    sources = {k: v.get("_source", "unknown") for k, v in live_data.items()}
    yield {"type": "status", "phase": "data", "message": f"Data collected. Sources: {sources}"}

    # Phase 2: multi-round swarm
    for round_num in range(1, MAX_ROUNDS + 1):
        state["round"] = round_num
        await update_state(campaign_id, state)

        yield {
            "type": "status",
            "phase": "swarm",
            "message": f"Round {round_num} — all agents analyzing in parallel...",
        }

        # All agents run concurrently — true flat swarm
        tasks = [agent.run(state) for agent in all_agents]
        round_results = await asyncio.gather(*tasks)

        failed_agents = []
        for result in round_results:
            state["observations"].append(result)
            await update_state(campaign_id, state)

            if result["status"] == "failed":
                failed_agents.append(result["agent"])
                yield {
                    "type": "agent_offline",
                    "phase": "swarm",
                    "agent": result["agent"],
                    "message": f"{result['agent']} is offline. Swarm continues with remaining agents.",
                }
            else:
                yield {
                    "type": "observation",
                    "phase": "swarm",
                    "agent": result["agent"],
                    "round": round_num,
                    "observation": result.get("observation", ""),
                    "proposal": result.get("proposal", ""),
                    "builds_on": result.get("builds_on", []),
                    "confidence": result.get("confidence", 0),
                }

            await asyncio.sleep(0.2)  # stagger for UI readability

        if failed_agents:
            yield {
                "type": "status",
                "phase": "swarm",
                "message": f"Note: {len(failed_agents)} agent(s) offline ({', '.join(failed_agents)}). Proceeding with available signals.",
            }

        # Check convergence
        successful = [r for r in round_results if r["status"] == "success"]
        if successful:
            avg_confidence = sum(r.get("confidence", 0) for r in successful) / len(successful)
            yield {
                "type": "status",
                "phase": "swarm",
                "message": f"Round {round_num} complete. Average confidence: {avg_confidence:.2f}",
            }
            if avg_confidence >= CONVERGENCE_THRESHOLD:
                yield {
                    "type": "status",
                    "phase": "swarm",
                    "message": f"Consensus reached at round {round_num}. Synthesizing campaign brief...",
                }
                break

    # Phase 3: synthesize final brief
    yield {"type": "status", "phase": "synthesis", "message": "Generating final campaign brief..."}

    brief_output = await _synthesize(state)
    state["brief_output"] = brief_output
    state["status"] = "complete"
    await update_state(campaign_id, state)

    yield {"type": "complete", "phase": "synthesis", "brief": brief_output}


async def _synthesize(state: dict) -> dict:
    observations_text = json.dumps(state["observations"], indent=2)
    brief = state["brief"]
    total_obs = len(state["observations"])
    rounds = state["round"]

    prompt = f"""You are a senior strategist reviewing a swarm intelligence report.
Your team of specialists completed {rounds} rounds of analysis with {total_obs} observations.
Distill their findings into a campaign intelligence brief.

BRAND TARGET:
{json.dumps(brief, indent=2)}

SWARM OBSERVATIONS:
{observations_text}

Integrate insights from ALL agents, especially convergences where multiple agents reached the same conclusion independently.
Note any signal gaps where an agent was offline.

Return JSON only:
{{
  "executive_summary": "2-3 sentences on what the swarm collectively found",
  "convergent_insights": ["insight backed by 2+ agents independently"],
  "campaign_angle": "The single strongest positioning angle, grounded in convergent signals",
  "target_audience": {{
    "primary_segment": "",
    "pain_points": [],
    "language_to_use": []
  }},
  "positioning": {{
    "value_proposition": "",
    "tone": "",
    "what_to_avoid": []
  }},
  "channel_recommendations": [
    {{
      "channel": "",
      "rationale": "",
      "message_angle": ""
    }}
  ],
  "copy_starters": [
    {{
      "headline": "",
      "hook": "",
      "cta": ""
    }}
  ],
  "signal_conflicts": ["where agents disagreed and what it means"],
  "data_gaps": ["signals that were unavailable"]
}}"""

    try:
        return await call_gemini(prompt)
    except Exception as e:
        return {"error": str(e), "raw_observations": state["observations"]}
