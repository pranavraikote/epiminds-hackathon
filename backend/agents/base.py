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
            "temperature": 1,
            "max_output_tokens": 2048,
        },
    )
    return json.loads(response.text)


class BaseAgent:
    name: str = "base_agent"
    role: str = ""
    focus: str = ""

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
        return combined[:10]

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

    def _format_prior_observations(self, state: dict) -> str:
        obs = state.get("observations", [])
        if not obs:
            return "None yet."
        sorted_obs = sorted(obs, key=lambda o: o.get("signal", 1.0), reverse=True)[:12]
        lines = []
        for o in sorted_obs:
            sig = o.get("signal", 1.0)
            strength = "▓▓▓" if sig >= 1.5 else "▓▓░" if sig >= 1.0 else "▓░░"
            lines.append(
                f"[{o['agent']} | Round {o['round']} | signal={sig:.2f} {strength}]\n"
                f"{o.get('observation', '')}"
            )
        return "\n\n".join(lines)
