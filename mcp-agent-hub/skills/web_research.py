import logging
import os
from typing import Any

import httpx
from fastmcp import FastMCP

from .base import AgentHubSkill


log = logging.getLogger("mcp-agent-hub.skills.web_research")


class WebResearchSkill(AgentHubSkill):
    name = "web_research"
    tool_names = ("advanced_web_research",)

    def __init__(self) -> None:
        self.bridge_url = (
            os.getenv("WEB_RESEARCH_BRIDGE_URL")
            or os.getenv("HERMES_BRIDGE_URL")
            or "http://127.0.0.1:8092/research"
        ).strip()
        self.request_timeout_seconds = float(os.getenv("WEB_RESEARCH_TIMEOUT_SECONDS", "420"))

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool
        async def advanced_web_research(
            task: str,
            max_results: int = 2,
            max_chars_per_page: int | None = None,
        ) -> dict[str, Any]:
            """
            Perform source-backed local web research through the web-research backend.

            This calls the local web-research-bridge backend, which performs:
            SearXNG search → n8n scrape workflow → LangGraph summarisation.

            Args:
                task: Research question or instruction.
                max_results: Number of search results to inspect. Clamped to 1-5.
                max_chars_per_page: Optional per-page scrape text limit. Leave empty to use backend default.

            Returns:
                JSON object containing answer, search results, scraped pages, and source URLs.
            """

            safe_task = (task or "").strip()

            if not safe_task:
                return {"error": "No research task provided."}

            try:
                safe_max_results = int(max_results)
            except Exception:
                safe_max_results = 2

            safe_max_results = max(1, min(safe_max_results, 5))

            payload: dict[str, Any] = {
                "task": safe_task,
                "max_results": safe_max_results,
            }

            if max_chars_per_page is not None:
                try:
                    payload["max_chars_per_page"] = int(max_chars_per_page)
                except Exception:
                    pass

            log.info(
                "advanced_web_research called task=%r max_results=%s bridge_url=%s",
                safe_task,
                safe_max_results,
                self.bridge_url,
            )

            try:
                async with httpx.AsyncClient(timeout=self.request_timeout_seconds) as client:
                    response = await client.post(
                        self.bridge_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as exc:
                log.exception("advanced_web_research backend returned HTTP error")
                return {
                    "error": "web research backend returned HTTP error",
                    "status_code": exc.response.status_code,
                    "body": exc.response.text[:1000],
                }

            except Exception as exc:
                log.exception("advanced_web_research failed")
                return {
                    "error": "advanced_web_research failed",
                    "exception_type": type(exc).__name__,
                    "message": str(exc),
                }
