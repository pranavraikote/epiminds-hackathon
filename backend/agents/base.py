import asyncio
import json
import os
from datetime import datetime, timedelta

import vertexai
from vertexai.generative_models import GenerativeModel

_project = os.getenv("GCP_PROJECT_ID")
_location = os.getenv("GCP_REGION", "us-central1")

if _project:
    vertexai.init(project=_project, location=_location)

_model = GenerativeModel("gemini-2.0-flash-001")


def _recent_range() -> str:
    """Returns a human-readable date range covering the last 6 months."""
    now = datetime.now()
    start = now - timedelta(days=180)
    return f"{start.strftime('%b %Y')}–{now.strftime('%b %Y')}"


async def call_gemini(prompt: str) -> dict:
    response = await asyncio.to_thread(
        _model.generate_content,
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 1.2,
            "max_output_tokens": 4096,
        },
    )
    return json.loads(response.text)


class BaseAgent:
    name: str = "base_agent"
    role: str = ""
    focus: str = ""

    # Typed wake conditions — only react to peer scents of these types at or above this intensity.
    # Empty frozenset means wake on any peer scent (default / backward-compat).
    wake_on: frozenset = frozenset()
    wake_threshold: float = 0.0

    async def run(self, state: dict) -> dict:
        brief = state["brief"]
        try:
            web_context = await self._fetch_context(brief)
            prompt = self._build_prompt(state, web_context)
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
                "builds_on": [],
                "done": False,
            }
        return result

    def _search_queries(self, brief: dict) -> list[str]:
        """Override in each agent to return tailored search queries."""
        return []

    async def _fetch_context(self, brief: dict) -> list[dict]:
        from data.websearch import search_raw
        queries = self._search_queries(brief)
        if not queries:
            return []
        results = await asyncio.gather(*[asyncio.to_thread(search_raw, q) for q in queries])
        combined = [item for sublist in results for item in sublist]
        return combined[:18]

    def _format_web_context(self, results: list[dict]) -> str:
        if not results:
            return "No live data available."
        return "\n".join(f"- {r['title']}: {r['snippet']}" for r in results)

    def _format_brief(self, brief: dict) -> str:
        prompt = brief.get("prompt", brief.get("product", ""))
        competitor = brief.get("competitor", "")
        suffix = f" (vs {competitor})" if competitor else ""
        return f"{prompt}{suffix}"

    def _build_prompt(self, state: dict, web_context: list[dict]) -> str:
        raise NotImplementedError

    def _format_buildable_scents(self, state: dict) -> str:
        """Returns a constrained JSON array of real scent references agents can cite in builds_on."""
        obs = [
            o for o in state.get("observations", [])
            if o.get("status") == "success" and o.get("agent") != "user"
        ]
        if not obs:
            return "[]"
        top = sorted(obs, key=lambda x: x.get("intensity", 0), reverse=True)[:8]
        refs = [f'"{o["agent"]} | Round {o["round"]}"' for o in top]
        return "[" + ", ".join(refs) + "]"

    def _format_prior_observations(self, state: dict) -> str:
        obs = state.get("observations", [])
        if not obs:
            return "None yet."
        sorted_obs = sorted(obs, key=lambda o: o.get("intensity", 0.7), reverse=True)[:20]
        lines = []
        for o in sorted_obs:
            intensity = o.get("intensity", 0.7)
            strength = "▓▓▓" if intensity >= 0.8 else "▓▓░" if intensity >= 0.5 else "▓░░"
            scent = o.get("scent_type", "")
            scent_label = f" [{scent}]" if scent else ""
            lines.append(
                f"[{o['agent']} | Round {o['round']} | intensity={intensity:.2f} {strength}{scent_label}]\n"
                f"{o.get('observation', '')}"
            )
        return "\n\n".join(lines)
