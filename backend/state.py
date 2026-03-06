import json
import os
from typing import Optional
import redis.asyncio as aioredis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
TTL = 3600  # 1 hour

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
        )
    return _redis


async def init_state(campaign_id: str, brief: dict) -> dict:
    state = {
        "campaign_id": campaign_id,
        "brief": brief,
        "round": 0,
        "observations": [],
        "status": "initializing",
        "brief_output": None,
    }
    r = await get_redis()
    await r.set(f"campaign:{campaign_id}", json.dumps(state), ex=TTL)
    return state


async def get_state(campaign_id: str) -> Optional[dict]:
    r = await get_redis()
    data = await r.get(f"campaign:{campaign_id}")
    return json.loads(data) if data else None


async def update_state(campaign_id: str, state: dict) -> None:
    r = await get_redis()
    await r.set(f"campaign:{campaign_id}", json.dumps(state), ex=TTL)
