import asyncio
import threading
from typing import AsyncGenerator, Optional

from agents import all_agents, mutator_agent, strategist_agent
from state import get_state, update_state, add_scent, decay_and_reinforce

REACTION_TIMEOUT = 60   # seconds an agent waits for a peer scent before going idle
SAFETY_TIMEOUT   = 360  # total wall-clock budget for the whole swarm


# ---------------------------------------------------------------------------
# Firestore-backed pub/sub — real-time, zero polling
# on_snapshot fires on background thread → call_soon_threadsafe into asyncio queues
# ---------------------------------------------------------------------------

class _FirestoreBus:
    def __init__(self, campaign_id: str, loop: asyncio.AbstractEventLoop):
        self._campaign_id = campaign_id
        self._loop = loop
        self._inboxes: list[asyncio.Queue] = []
        self._watch = None
        self._ready = threading.Event()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._inboxes.append(q)
        return q

    def start(self) -> None:
        """Blocks until initial Firestore snapshot received. Call via asyncio.to_thread."""
        import os
        from google.cloud import firestore
        db = firestore.Client(project=os.getenv("GCP_PROJECT_ID"))
        initial_done = [False]
        seen_ids: set = set()

        def on_snapshot(col_snapshot, changes, read_time):
            if not initial_done[0]:
                for change in changes:
                    seen_ids.add(change.document.id)
                initial_done[0] = True
                self._ready.set()
                return
            for change in changes:
                if change.type.name == "ADDED" and change.document.id not in seen_ids:
                    seen_ids.add(change.document.id)
                    doc = change.document.to_dict()
                    event = {
                        "type": "new_scent",
                        "from_agent": doc.get("agent", ""),
                        "scent_type": doc.get("scent_type", ""),
                        "intensity": doc.get("intensity", 0.7),
                    }
                    for q in self._inboxes:
                        self._loop.call_soon_threadsafe(q.put_nowait, event)

        scents_ref = (
            db.collection("campaigns")
            .document(self._campaign_id)
            .collection("scents")
        )
        self._watch = scents_ref.on_snapshot(on_snapshot)
        self._ready.wait(timeout=10.0)

    def stop(self) -> None:
        if self._watch:
            self._watch.unsubscribe()


# ---------------------------------------------------------------------------
# Atomic scent commit: decay → reinforce cited → write new scent
# Bus notification is handled automatically by Firestore on_snapshot
# ---------------------------------------------------------------------------

async def _commit(
    result: dict, campaign_id: str, lock: asyncio.Lock, sse_q: asyncio.Queue
) -> None:
    async with lock:
        cited = set(result.get("builds_on", []))
        reinforced = await decay_and_reinforce(campaign_id, cited)
        await add_scent(campaign_id, result)
    for r in reinforced:
        await sse_q.put({
            "type": "scent_reinforced",
            "agent": r["agent"],
            "round": r["round"],
            "intensity": r["intensity"],
        })


def _scent_event(result: dict) -> dict:
    return {
        "type": "observation",
        "phase": "swarm",
        "agent": result["agent"],
        "round": result.get("round", 1),
        "observation": result.get("observation", ""),
        "scent_type": result.get("scent_type", ""),
        "intensity": result.get("intensity", 0.7),
        "builds_on": result.get("builds_on", []),
        "payload": result.get("payload", {}),
    }


# ---------------------------------------------------------------------------
# Data agent: all 7 agents go through this — foragers run independently first,
# react_only agents (strategist, skeptic, mutator, audience_sniper) wait for
# qualifying peer scents before acting. Coordination is entirely via the blackboard.
# ---------------------------------------------------------------------------

MAX_AGENT_ROUNDS = 5  # maximum stigmergic reactions per agent per swarm run


async def _data_agent(
    agent, campaign_id: str, bus: _FirestoreBus, sse_q: asyncio.Queue, lock: asyncio.Lock,
    round_offset: int = 0,
    killed_agents: Optional[set] = None,
) -> None:
    # Demo kill — agent goes offline immediately (short pause for dramatic effect)
    if killed_agents and agent.name in killed_agents:
        await asyncio.sleep(1.5)
        await sse_q.put({
            "type": "agent_offline", "phase": "swarm", "agent": agent.name,
            "message": f"{agent.name} offline: connection terminated.",
        })
        return

    inbox = bus.subscribe()
    # react_only agents skip their independent first pass — they only ever
    # synthesise real peer signal, never forage on a near-empty blackboard.
    local_round = 1 if getattr(agent, 'react_only', False) else 0

    while local_round < MAX_AGENT_ROUNDS:
        # First pass runs immediately; subsequent passes wait for a new peer scent
        if local_round > 0:
            # Drain stale events already in inbox, then wait for a fresh peer signal
            while not inbox.empty():
                inbox.get_nowait()
            try:
                while True:
                    event = await asyncio.wait_for(inbox.get(), timeout=REACTION_TIMEOUT)
                    if (
                        event["type"] == "new_scent"
                        and event["from_agent"] != agent.name
                        and (not agent.wake_on or event["scent_type"] in agent.wake_on)
                        and event.get("intensity", 0.0) >= agent.wake_threshold
                    ):
                        break
            except asyncio.TimeoutError:
                return  # no new peer stimulus — this agent is idle

        try:
            state = await get_state(campaign_id)
            result = await agent.run(state)
            result.update(round=local_round + 1 + round_offset)
            result.setdefault("intensity", 0.7)
            await _commit(result, campaign_id, lock, sse_q)
        except Exception as e:
            # Catches failures outside agent.run() (e.g. Firestore commit errors)
            # that would otherwise be silently swallowed by gather(return_exceptions=True)
            await sse_q.put({
                "type": "agent_offline", "phase": "swarm", "agent": agent.name,
                "message": f"{agent.name} offline (infra): {str(e)[:120]}",
            })
            return

        if result["status"] == "failed":
            err = result.get("error", "unknown error")
            await sse_q.put({
                "type": "agent_offline", "phase": "swarm", "agent": agent.name,
                "message": f"{agent.name} offline: {err[:120]}",
            })
            return

        await sse_q.put(_scent_event(result))
        local_round += 1

        if result.get("done"):
            return  # agent self-terminated — no further reactions needed


# ---------------------------------------------------------------------------
# Swarm runner
# ---------------------------------------------------------------------------

async def run_swarm(campaign_id: str, demo_kill: Optional[set] = None) -> AsyncGenerator[dict, None]:
    state = await get_state(campaign_id)
    if not state:
        yield {"type": "error", "message": "Campaign not found."}
        return

    brief = state["brief"]

    # Compute round offset so watch-mode runs don't overwrite prior scents
    existing_rounds = [
        o.get("round", 0) for o in state.get("observations", [])
        if o.get("agent") != "user"
    ]
    round_offset = max(existing_rounds, default=0)

    # User prompt is the first scent — the pheromone trail begins here
    user_scent = {
        "agent": "user",
        "round": 0,
        "intensity": 0.7,
        "scent_type": "Prompt",
        "status": "success",
        "observation": brief["prompt"],
        "payload": {"prompt": brief["prompt"]},
        "builds_on": [],
        "done": False,
    }
    await add_scent(campaign_id, user_scent)
    state["status"] = "running"
    state["round"] = 1
    await update_state(campaign_id, state)

    yield {
        "type": "observation", "phase": "user", "agent": "user", "round": 0,
        "observation": brief["prompt"], "scent_type": "Prompt",
        "intensity": 0.7, "builds_on": [], "payload": {},
    }
    yield {"type": "status", "phase": "swarm", "message": "Swarm online — Scavengers foraging the field..."}

    loop = asyncio.get_event_loop()
    bus = _FirestoreBus(campaign_id, loop)
    await asyncio.to_thread(bus.start)  # Block until initial Firestore snapshot received

    sse_q: asyncio.Queue = asyncio.Queue()
    lock = asyncio.Lock()

    # Foraging agents run independently and react to peer scents.
    # Synthesis agents (mutator, audience_sniper) are also in all_agents but are react_only —
    # they wake on typed scents (Strategy, Mutation) rather than foraging the field directly.
    # All 7 go through the same _data_agent mechanism — no coordinator.
    _SYNTHESIS = {"mutator", "audience_sniper"}
    foraging_tasks = [
        asyncio.create_task(_data_agent(a, campaign_id, bus, sse_q, lock, round_offset, demo_kill))
        for a in all_agents if a.name not in _SYNTHESIS
    ]
    synthesis_tasks = [
        asyncio.create_task(_data_agent(a, campaign_id, bus, sse_q, lock, round_offset, demo_kill))
        for a in all_agents if a.name in _SYNTHESIS
    ]

    synthesis_done = asyncio.Event()

    async def _watch():
        await asyncio.gather(*synthesis_tasks, return_exceptions=True)
        synthesis_done.set()

    watcher = asyncio.create_task(_watch())
    deadline = loop.time() + SAFETY_TIMEOUT
    foraging_cancelled = False

    try:
        while not synthesis_done.is_set():
            remaining = deadline - loop.time()
            if remaining <= 0 and not foraging_cancelled:
                yield {"type": "status", "phase": "swarm", "message": "Safety timeout — foraging agents released, synthesis converging..."}
                for t in foraging_tasks:
                    t.cancel()
                foraging_cancelled = True
                deadline = loop.time() + 120  # 2-min extension for synthesis to complete
            try:
                event = await asyncio.wait_for(sse_q.get(), timeout=0.3)
                yield event
            except asyncio.TimeoutError:
                pass
    finally:
        watcher.cancel()
        for t in foraging_tasks:
            if not t.done():
                t.cancel()

    while not sse_q.empty():
        yield sse_q.get_nowait()

    await asyncio.to_thread(bus.stop)

    # Emergent output — blackboard sorted by intensity, top scent per agent
    final_state = await get_state(campaign_id)
    successful = [
        o for o in final_state["observations"]
        if o.get("status") == "success" and o.get("agent") != "user"
    ]

    top_by_agent: dict = {}
    for o in sorted(successful, key=lambda x: x.get("intensity", 0.7), reverse=True):
        ag = o["agent"]
        if ag not in top_by_agent:
            top_by_agent[ag] = o

    user_intensity = next(
        (o["intensity"] for o in final_state["observations"] if o["agent"] == "user"), 0.7
    )

    brief_output = {
        "observations": successful,
        "top_by_agent": top_by_agent,
        "user_intensity": user_intensity,
        "agents_online":  list(top_by_agent.keys()),
        "agents_offline": list({o["agent"] for o in final_state["observations"] if o.get("status") == "failed"}),
    }

    final_state["brief_output"] = brief_output
    final_state["status"] = "complete"
    await update_state(campaign_id, final_state)

    yield {"type": "complete", "phase": "swarm", "brief": brief_output}


# ---------------------------------------------------------------------------
# Follow-up runner — re-enters the field with a directed question, runs
# Strategist + Mutator against the existing pheromone trail.  Fast path: no
# web re-scraping by Phase 1/2 agents, just strategic synthesis on live data.
# ---------------------------------------------------------------------------

async def run_followup(campaign_id: str, followup_prompt: str) -> AsyncGenerator[dict, None]:
    state = await get_state(campaign_id)
    if not state:
        yield {"type": "error", "message": "Campaign not found."}
        return

    existing_rounds = [
        o.get("round", 0) for o in state.get("observations", [])
        if o.get("agent") != "user"
    ]
    round_offset = max(existing_rounds, default=0)

    # Write the follow-up as a high-intensity directed signal — it overrides ambient signals
    followup_scent = {
        "agent": "user",
        "round": round_offset + 1,
        "intensity": 0.85,
        "scent_type": "Followup",
        "status": "success",
        "observation": followup_prompt,
        "payload": {"prompt": followup_prompt},
        "builds_on": [],
        "done": True,
    }
    await add_scent(campaign_id, followup_scent)

    yield {
        "type": "observation", "phase": "user", "agent": "user",
        "round": round_offset + 1, "observation": followup_prompt,
        "scent_type": "Followup", "intensity": 0.85, "builds_on": [], "payload": {},
    }
    yield {"type": "status", "phase": "followup", "message": "Follow-up received — Strategist re-evaluating against live trail..."}

    lock = asyncio.Lock()
    sse_q: asyncio.Queue = asyncio.Queue()

    fresh_state = await get_state(campaign_id)
    fresh_state["round"] = round_offset + 2
    await update_state(campaign_id, fresh_state)

    # Re-run Strategist focused on the follow-up direction
    try:
        s_state = await get_state(campaign_id)
        s_result = await strategist_agent.run(s_state)
        s_result.update(round=round_offset + 2)
        s_result.setdefault("intensity", 0.8)
        await _commit(s_result, campaign_id, lock, sse_q)
        if s_result["status"] == "success":
            yield _scent_event(s_result)
        else:
            yield {
                "type": "agent_offline", "phase": "followup", "agent": "strategist",
                "message": f"strategist offline: {s_result.get('error', 'unknown')[:120]}",
            }
    except Exception as e:
        yield {
            "type": "agent_offline", "phase": "followup", "agent": "strategist",
            "message": f"strategist offline (infra): {str(e)[:120]}",
        }

    while not sse_q.empty():
        yield sse_q.get_nowait()

    yield {"type": "status", "phase": "followup", "message": "Mutator evolving updated strategy..."}

    # Re-run Mutator — it reads the updated trail including the Followup scent
    try:
        m_state = await get_state(campaign_id)
        m_result = await mutator_agent.run(m_state)
        m_result.update(round=round_offset + 3)
        m_result.setdefault("intensity", 0.88)
        await _commit(m_result, campaign_id, lock, sse_q)
        if m_result["status"] == "success":
            yield _scent_event(m_result)
        else:
            yield {
                "type": "agent_offline", "phase": "followup", "agent": "mutator",
                "message": f"mutator offline: {m_result.get('error', 'unknown')[:120]}",
            }
    except Exception as e:
        yield {
            "type": "agent_offline", "phase": "followup", "agent": "mutator",
            "message": f"mutator offline (infra): {str(e)[:120]}",
        }

    while not sse_q.empty():
        yield sse_q.get_nowait()

    yield {"type": "complete", "phase": "followup", "message": "Follow-up intelligence ready."}
