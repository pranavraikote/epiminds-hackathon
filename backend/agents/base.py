import asyncio
import json
import os

import vertexai
from vertexai.generative_models import GenerativeModel

_project = os.getenv("GCP_PROJECT_ID")
_location = os.getenv("GCP_REGION", "us-central1")

if _project:
    vertexai.init(project=_project, location=_location)

_model = GenerativeModel("gemini-2.0-flash-001")


async def call_gemini(prompt: str) -> dict:
    response = await asyncio.to_thread(
        _model.generate_content,
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.7,
            "max_output_tokens": 1024,
        },
    )
    return json.loads(response.text)


class BaseAgent:
    name: str = "base_agent"
    role: str = ""
    focus: str = ""

    async def run(self, state: dict) -> dict:
        prompt = self._build_prompt(state)
        try:
            result = await call_gemini(prompt)
            result["agent"] = self.name
            result["round"] = state["round"]
            result["status"] = "success"
        except Exception as e:
            result = {
                "agent": self.name,
                "round": state["round"],
                "status": "failed",
                "error": str(e),
                "observation": f"{self.name} is offline.",
                "proposal": None,
                "confidence": 0.0,
                "builds_on": [],
            }
        return result

    def _build_prompt(self, state: dict) -> str:
        raise NotImplementedError

    def _format_prior_observations(self, state: dict) -> str:
        obs = state.get("observations", [])
        if not obs:
            return "None yet — you are in Round 1."
        lines = []
        for o in obs:
            lines.append(
                f"[{o['agent']} | Round {o['round']}]\n"
                f"Observation: {o.get('observation', '')}\n"
                f"Proposal: {o.get('proposal', '')}\n"
                f"Confidence: {o.get('confidence', 0)}\n"
            )
        return "\n".join(lines)
