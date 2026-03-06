import asyncio
import os
from typing import Optional
from google.cloud import firestore as _fs

_db = None


def _get_db() -> _fs.Client:
    global _db
    if _db is None:
        project = os.getenv("GCP_PROJECT_ID")
        _db = _fs.Client(project=project)
    return _db


# ---------------------------------------------------------------------------
# Sync helpers (run via asyncio.to_thread)
# ---------------------------------------------------------------------------

def _init_sync(campaign_id: str, brief: dict) -> dict:
    db = _get_db()
    meta = {
        "campaign_id": campaign_id,
        "brief": brief,
        "round": 0,
        "status": "initializing",
        "brief_output": None,
    }
    db.collection("campaigns").document(campaign_id).set(meta)
    return {**meta, "observations": []}


def _get_sync(campaign_id: str) -> Optional[dict]:
    db = _get_db()
    doc = db.collection("campaigns").document(campaign_id).get()
    if not doc.exists:
        return None
    meta = doc.to_dict()
    scents_ref = (
        db.collection("campaigns")
        .document(campaign_id)
        .collection("scents")
    )
    meta["observations"] = [
        {k: v for k, v in s.to_dict().items() if k != "timestamp"}
        for s in scents_ref.stream()
    ]
    return meta


def _update_sync(campaign_id: str, state: dict) -> None:
    db = _get_db()
    meta = {k: v for k, v in state.items() if k != "observations"}
    db.collection("campaigns").document(campaign_id).set(meta, merge=True)


def _add_scent_sync(campaign_id: str, scent: dict) -> None:
    db = _get_db()
    scent_id = f"{scent['agent']}_r{scent.get('round', 0)}"
    # Strip non-serialisable fields before writing
    clean = {k: v for k, v in scent.items() if not callable(v)}
    clean["timestamp"] = _fs.SERVER_TIMESTAMP
    (
        db.collection("campaigns")
        .document(campaign_id)
        .collection("scents")
        .document(scent_id)
        .set(clean)
    )


def _decay_and_reinforce_sync(
    campaign_id: str, cited_tags: set, factor: float = 0.85
) -> list[dict]:
    """Decay all scents by factor, add reinforcement for cited ones. Returns reinforced list."""
    db = _get_db()
    scents_ref = (
        db.collection("campaigns")
        .document(campaign_id)
        .collection("scents")
    )
    batch = db.batch()
    reinforced = []

    for doc in scents_ref.stream():
        data = doc.to_dict()
        if data.get("agent") == "user":
            continue  # User prompt scent doesn't decay
        current = data.get("intensity", 0.7)
        new_intensity = round(current * factor, 4)
        tag = f"{data.get('agent', '')} | Round {data.get('round', 0)}"
        if tag in cited_tags:
            new_intensity = min(1.0, new_intensity + 0.15)
            reinforced.append({**data, "intensity": new_intensity})
        batch.update(doc.reference, {"intensity": new_intensity})

    batch.commit()
    return reinforced


# ---------------------------------------------------------------------------
# Async API
# ---------------------------------------------------------------------------

async def init_state(campaign_id: str, brief: dict) -> dict:
    return await asyncio.to_thread(_init_sync, campaign_id, brief)


async def get_state(campaign_id: str) -> dict:
    return await asyncio.to_thread(_get_sync, campaign_id)


async def update_state(campaign_id: str, state: dict) -> None:
    await asyncio.to_thread(_update_sync, campaign_id, state)


async def add_scent(campaign_id: str, scent: dict) -> None:
    await asyncio.to_thread(_add_scent_sync, campaign_id, scent)


async def decay_and_reinforce(
    campaign_id: str, cited_tags: set, factor: float = 0.85
) -> list[dict]:
    return await asyncio.to_thread(_decay_and_reinforce_sync, campaign_id, cited_tags, factor)
