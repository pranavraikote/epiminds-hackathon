import json
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


class BrandTarget(BaseModel):
    product: str
    competitor: str = ""


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/campaign")
async def create_campaign(brief: BrandTarget):
    campaign_id = str(uuid.uuid4())
    await init_state(campaign_id, brief.model_dump())
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
