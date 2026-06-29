import logging
import os
from typing import Any, Literal

import httpx
from fastmcp import FastMCP

from .base import AgentHubSkill


log = logging.getLogger("mcp-agent-hub.skills.personal_assistant")

AssistantMode = Literal[
    "general_assistant",
    "hospitality_assistant",
    "read_only",
    "draft_only",
]


class PersonalAssistantSkill(AgentHubSkill):
    name = "personal_assistant"
    tool_names = ("personal_assistant_task",)

    def __init__(self) -> None:
        self.webhook_url = os.getenv("PERSONAL_ASSISTANT_WEBHOOK_URL", "").strip()
        self.request_timeout_seconds = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "90"))

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool
        async def personal_assistant_task(
            task: str,
            mode: AssistantMode = "general_assistant",
        ) -> str:
            """
            Run a personal assistant task through the local n8n backend.

            Args:
                task: Self-contained task request.
                mode: Assistant profile/mode. Use general_assistant for secretary-style tasks. Use hospitality_assistant for Hut AI hospitality, travel, bookings, guest, hotel, Airbnb, Booking.com, and property operations tasks. read_only and draft_only are accepted for backwards compatibility and map to the n8n default behaviour.

            Returns:
                Personal assistant backend response.
            """

            safe_task = (task or "").strip()
            safe_mode = (mode or "general_assistant").strip().lower()

            allowed_modes = {
                "general_assistant",
                "hospitality_assistant",
                "read_only",
                "draft_only",
            }

            if not safe_task:
                return "No task provided."

            if safe_mode not in allowed_modes:
                return (
                    "Unsupported mode. Use general_assistant or hospitality_assistant. "
                    "Legacy modes read_only and draft_only are also accepted."
                )

            if not self.webhook_url:
                return "PERSONAL_ASSISTANT_WEBHOOK_URL is not configured."

            payload = {
                "task": safe_task,
                "mode": safe_mode,
                "source": "mcp-agent-hub",
            }

            log.info("personal_assistant_task called mode=%s task=%r", safe_mode, safe_task)

            try:
                async with httpx.AsyncClient(timeout=self.request_timeout_seconds) as client:
                    response = await client.post(
                        self.webhook_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )

                response.raise_for_status()

                try:
                    data: Any = response.json()
                except Exception:
                    return response.text.strip()

                if isinstance(data, dict):
                    for key in ("answer", "summary", "result", "message"):
                        value = data.get(key)
                        if isinstance(value, str) and value.strip():
                            return value.strip()

                    return str(data)

                return str(data)

            except Exception as exc:
                log.exception("personal_assistant_task failed")
                return f"personal_assistant_task failed: {type(exc).__name__}: {exc}"
