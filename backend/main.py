import json
import re
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv()

from state import init_state, get_state
from swarm import run_swarm


app = FastAPI(title="Campaign Intelligence Swarm")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CampaignRequest(BaseModel):
    prompt: str


_VS_PATTERN = re.compile(r'\s+(?:vs\.?|versus|against|compared to)\s+', re.IGNORECASE)
_STOP = frozenset(
    "a an the i we my our is are was were be been being have has had do does did "
    "will would could should may might shall for that which this with of in to and "
    "or but not how what when where who why if then than because about into from "
    "launching launch building build campaign help position market".split()
)


def _parse_prompt(prompt: str) -> dict:
    """Extract search keywords for data APIs. Full prompt goes to agents unchanged."""
    p = prompt.strip()

    # "X vs Y" — two distinct search targets
    vs_parts = _VS_PATTERN.split(p, maxsplit=1)
    if len(vs_parts) == 2:
        return {"product": vs_parts[0].strip(), "competitor": vs_parts[1].strip(), "prompt": p}

    # Everything else — extract meaningful keywords for data fetching
    words = [w for w in re.sub(r'[^\w\s]', '', p).split() if w.lower() not in _STOP]
    search_term = " ".join(words[:5]) or p[:80]
    return {"product": search_term, "competitor": "", "prompt": p}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/campaign")
async def create_campaign(req: CampaignRequest):
    campaign_id = str(uuid.uuid4())
    brief = _parse_prompt(req.prompt)
    await init_state(campaign_id, brief)
    return {"campaign_id": campaign_id}


@app.get("/stream/{campaign_id}")
async def stream_campaign(campaign_id: str):
    state = await get_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Campaign not found")

    async def event_generator():
        async for update in run_swarm(campaign_id):
            yield {"data": json.dumps(update)}

    return EventSourceResponse(event_generator())


@app.get("/result/{campaign_id}")
async def get_result(campaign_id: str):
    state = await get_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if state["status"] != "complete":
        return {"status": state["status"], "brief": None}
    return {"status": "complete", "brief": state["brief_output"]}
