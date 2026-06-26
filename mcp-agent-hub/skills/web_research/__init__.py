import logging
from typing import Any

from fastmcp import FastMCP
from pydantic import ValidationError

from ..base import AgentHubSkill
from .failures import ResearchFailure
from .models import ResearchRequest
from .research_service import run_research


log = logging.getLogger("mcp-agent-hub.skills.web_research")


class WebResearchSkill(AgentHubSkill):
    name = "web_research"
    tool_names = ("advanced_web_research",)

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool
        async def advanced_web_research(
            task: str,
            max_results: int = 2,
            max_chars_per_page: int | None = None,
        ) -> dict[str, Any]:
            """
            Perform source-backed local web research.

            This skill owns the full web research pipeline:
            SearXNG search → n8n scrape workflow → LangGraph summarisation.

            Args:
                task: Research question or instruction.
                max_results: Number of search results to inspect.
                max_chars_per_page: Optional per-page scrape text limit.

            Returns:
                JSON object containing answer, search results, scraped pages, and source URLs.
            """

            safe_task = (task or "").strip()

            if not safe_task:
                return {"error": "No research task provided."}

            try:
                request = ResearchRequest(
                    task=safe_task,
                    max_results=max_results,
                    max_chars_per_page=max_chars_per_page,
                )
            except ValidationError:
                return {"error": "Invalid research task provided."}

            log.info(
                "advanced_web_research called task=%r max_results=%s",
                safe_task,
                max_results,
            )

            try:
                return await run_research(request)
            except ResearchFailure as exc:
                log.warning("advanced_web_research failed reason=%s", exc.reason)
                return {
                    "error": "web research failed",
                    "reason": exc.reason,
                }
            except Exception:
                log.exception("advanced_web_research failed unexpectedly")
                return {"error": "advanced_web_research failed"}
