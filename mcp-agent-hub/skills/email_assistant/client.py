import logging
from typing import Any

import httpx

from .config import settings


log = logging.getLogger("mcp-agent-hub.skills.email_assistant.client")


class EmailWorkflowClient:
    async def post(self, action: str, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not url:
            log.warning("email_%s_webhook_not_configured", action)
            return {
                "error": f"email {action} workflow is not configured",
                "action": action,
            }

        try:
            async with httpx.AsyncClient(timeout=settings.email_request_timeout_seconds) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

            if response.status_code >= 400:
                log.warning("email_%s_workflow_failed status_code=%s", action, response.status_code)
                return {
                    "error": f"email {action} workflow failed",
                    "action": action,
                    "status_code": response.status_code,
                }

            try:
                data = response.json()
            except ValueError:
                log.warning("email_%s_workflow_invalid_json", action)
                return {
                    "error": f"email {action} workflow returned invalid json",
                    "action": action,
                }

            if isinstance(data, dict):
                return data

            return {
                "result": data,
                "action": action,
            }

        except Exception:
            log.exception("email_%s_workflow_call_failed", action)
            return {
                "error": f"email {action} workflow call failed",
                "action": action,
            }

    async def search(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post("search", settings.email_search_webhook_url, payload)

    async def read(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post("read", settings.email_read_webhook_url, payload)

    async def draft_reply(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post("draft_reply", settings.email_draft_reply_webhook_url, payload)
