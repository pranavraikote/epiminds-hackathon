import asyncio
from typing import AsyncGenerator

from agents import all_agents
from state import get_state, update_state

REACTION_TIMEOUT = 30   # seconds an agent waits for a peer signal before going idle
SAFETY_TIMEOUT   = 150  # total wall-clock budget for the whole swarm


# ---------------------------------------------------------------------------
# In-process fanout pub/sub — zero polling
# ---------------------------------------------------------------------------

class _Bus:
    def __init__(self):
        self._inboxes: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._inboxes.append(q)
        return q

    async def publish(self, event: dict) -> None:
        for q in self._inboxes:
            await q.put(event)


# ---------------------------------------------------------------------------
# Atomic state write + stigmergy reinforcement + bus notification
# ---------------------------------------------------------------------------

async def _commit(
    result: dict, campaign_id: str, bus: _Bus, lock: asyncio.Lock, sse_q: asyncio.Queue
) -> None:
    reinforced = []
    async with lock:
        state = await get_state(campaign_id)
        cited = set(result.get("builds_on", []))
        for prior in state["observations"]:
            tag = f"{prior['agent']} | Round {prior['round']}"
            if tag in cited:
                prior["signal"] = prior.get("signal", 1.0) + 0.5
                reinforced.append({"agent": prior["agent"], "round": prior["round"], "signal": prior["signal"]})
        state["observations"].append(result)
        await update_state(campaign_id, state)
    # Signal reinforcement events — the visible moment of emergence
    for r in reinforced:
        await sse_q.put({"type": "signal_reinforced", "agent": r["agent"], "round": r["round"], "signal": r["signal"]})
    # Publish outside the lock so other agents can react immediately
    await bus.publish({"type": "new_observation", "from_agent": result["agent"]})


def _obs_event(result: dict) -> dict:
    return {
        "type": "observation",
        "phase": "swarm",
        "agent": result["agent"],
        "round": result["round"],
        "observation": result.get("observation", ""),
        "builds_on": result.get("builds_on", []),
        "signal": result.get("signal", 1.0),
    }


# ---------------------------------------------------------------------------
# Data agent: runs immediately, then reacts once when a peer posts
# ---------------------------------------------------------------------------

async def _data_agent(
    agent, campaign_id: str, bus: _Bus, sse_q: asyncio.Queue, lock: asyncio.Lock
) -> None:
    # Subscribe before first run so we don't miss peer events
    inbox = bus.subscribe()

    # Pass 1 — read own data source
    state = await get_state(campaign_id)
    result = await agent.run(state)
    result.update(round=1, signal=1.0)
    await _commit(result, campaign_id, bus, lock, sse_q)

    if result["status"] == "failed":
        err = result.get("error", "unknown error")
        await sse_q.put({"type": "agent_offline", "phase": "swarm", "agent": agent.name,
                         "message": f"{agent.name} offline: {err[:120]}"})
        return

    await sse_q.put(_obs_event(result))
    if result.get("done"):
        return

    # Pass 2 — wait for a signal from any other agent, then react once
    while True:
        try:
            event = await asyncio.wait_for(inbox.get(), timeout=REACTION_TIMEOUT)
        except asyncio.TimeoutError:
            return  # no peer activity — go idle
        if event["type"] == "new_observation" and event["from_agent"] != agent.name:
            break   # a peer wrote something; time to react

    state = await get_state(campaign_id)
    result = await agent.run(state)
    result.update(round=2, signal=1.0)
    await _commit(result, campaign_id, bus, lock, sse_q)

    if result["status"] == "failed":
        err2 = result.get("error", "unknown error")
        await sse_q.put({"type": "agent_offline", "phase": "swarm", "agent": agent.name,
                         "message": f"{agent.name} offline: {err2[:120]}"})
    else:
        await sse_q.put(_obs_event(result))


# ---------------------------------------------------------------------------
# Swarm runner
# ---------------------------------------------------------------------------

async def run_swarm(campaign_id: str) -> AsyncGenerator[dict, None]:
    state = await get_state(campaign_id)
    if not state:
        yield {"type": "error", "message": "Campaign not found."}
        return

    brief = state["brief"]

    # User prompt is the first write to the blackboard — agents react to it
    user_obs = {
        "agent": "user",
        "round": 0,
        "signal": 1.0,
        "status": "success",
        "observation": brief["prompt"],
        "builds_on": [],
        "done": False,
    }
    state["observations"] = [user_obs]
    state["status"] = "running"
    state["round"] = 1
    await update_state(campaign_id, state)

    yield {"type": "observation", "phase": "user", "agent": "user", "round": 0,
           "observation": brief["prompt"], "builds_on": [], "signal": 1.0}
    yield {"type": "status", "phase": "swarm", "message": "Swarm online — agents foraging independently..."}

    bus   = _Bus()
    sse_q: asyncio.Queue = asyncio.Queue()
    lock  = asyncio.Lock()

    tasks = [
        asyncio.create_task(_data_agent(a, campaign_id, bus, sse_q, lock))
        for a in all_agents
    ]

    all_done = asyncio.Event()

    async def _watch():
        await asyncio.gather(*tasks, return_exceptions=True)
        all_done.set()

    watcher = asyncio.create_task(_watch())
    loop = asyncio.get_event_loop()
    deadline = loop.time() + SAFETY_TIMEOUT

    try:
        while not all_done.is_set():
            remaining = deadline - loop.time()
            if remaining <= 0:
                yield {"type": "status", "phase": "swarm", "message": "Safety timeout — wrapping up."}
                for t in tasks:
                    t.cancel()
                break
            try:
                event = await asyncio.wait_for(sse_q.get(), timeout=min(0.3, remaining))
                yield event
            except asyncio.TimeoutError:
                pass
    finally:
        watcher.cancel()

    while not sse_q.empty():
        yield sse_q.get_nowait()

    # Emergent output — blackboard sorted by pheromone signal, top per agent
    state = await get_state(campaign_id)
    successful_obs = [o for o in state["observations"] if o["status"] == "success" and o["agent"] != "user"]

    top_by_agent: dict = {}
    for o in sorted(successful_obs, key=lambda x: x.get("signal", 1.0), reverse=True):
        ag = o["agent"]
        if ag not in top_by_agent:
            top_by_agent[ag] = o

    # User observation signal shows which framing resonated with the swarm
    user_signal = next((o["signal"] for o in state["observations"] if o["agent"] == "user"), 1.0)

    brief_output = {
        "observations": successful_obs,
        "top_by_agent": top_by_agent,
        "user_signal": user_signal,
        "agents_online":  list(top_by_agent.keys()),
        "agents_offline": list({o["agent"] for o in state["observations"] if o["status"] == "failed"}),
    }

    state["brief_output"] = brief_output
    state["status"] = "complete"
    await update_state(campaign_id, state)

    yield {"type": "complete", "phase": "swarm", "brief": brief_output}
