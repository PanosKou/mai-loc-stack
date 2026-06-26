import logging
from typing import Any

from fastmcp import FastMCP

from ..base import AgentHubSkill
from .client import EmailWorkflowClient
from .config import settings


log = logging.getLogger("mcp-agent-hub.skills.email_assistant")


def clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def clamp_max_results(value: int | None) -> int:
    if value is None:
        value = settings.email_default_max_results

    try:
        value = int(value)
    except Exception:
        value = settings.email_default_max_results

    return max(1, min(value, settings.email_max_results_hard))


def compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if value is not None and value != ""
    }


class EmailAssistantSkill(AgentHubSkill):
    name = "email_assistant"
    tool_names = (
        "email_search",
        "email_read",
        "email_draft_reply",
    )

    def __init__(self) -> None:
        self.client = EmailWorkflowClient()

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool
        async def email_search(
            query: str = "",
            max_results: int | None = None,
            unread_only: bool = False,
            from_address: str | None = None,
            subject: str | None = None,
        ) -> dict[str, Any]:
            """
            Search email messages through the configured n8n email search workflow.

            This is read-only. It must not send, delete, archive, label, or modify email.

            Args:
                query: Provider-specific search query or free-text query.
                max_results: Maximum number of messages to return. Clamped by EMAIL_MAX_RESULTS_HARD.
                unread_only: Restrict results to unread messages when supported by the workflow.
                from_address: Optional sender filter.
                subject: Optional subject filter.

            Returns:
                JSON response from the email search workflow.
            """

            payload = compact_payload(
                {
                    "query": clean_optional(query),
                    "max_results": clamp_max_results(max_results),
                    "unread_only": bool(unread_only),
                    "from_address": clean_optional(from_address),
                    "subject": clean_optional(subject),
                    "source": "mcp-agent-hub",
                }
            )

            log.info("email_search called max_results=%s unread_only=%s", payload["max_results"], unread_only)
            return await self.client.search(payload)

        @mcp.tool
        async def email_read(
            message_id: str,
            include_body: bool = True,
            include_thread: bool = True,
        ) -> dict[str, Any]:
            """
            Read an email message or thread through the configured n8n email read workflow.

            This is read-only. It must not send, delete, archive, label, or modify email.

            Args:
                message_id: Provider message identifier returned by email_search.
                include_body: Include the message body when supported by the workflow.
                include_thread: Include thread context when supported by the workflow.

            Returns:
                JSON response from the email read workflow.
            """

            safe_message_id = clean_optional(message_id)
            if not safe_message_id:
                return {"error": "message_id is required"}

            payload = {
                "message_id": safe_message_id,
                "include_body": bool(include_body),
                "include_thread": bool(include_thread),
                "source": "mcp-agent-hub",
            }

            log.info("email_read called message_id=%s include_thread=%s", safe_message_id, include_thread)
            return await self.client.read(payload)

        @mcp.tool
        async def email_draft_reply(
            message_id: str,
            reply_instructions: str,
            tone: str = "professional",
            create_gmail_draft: bool = True,
        ) -> dict[str, Any]:
            """
            Draft a reply to an existing email through the configured n8n draft workflow.

            This tool is draft-only. It must not send the reply.

            Args:
                message_id: Provider message identifier returned by email_search or email_read.
                reply_instructions: User instructions for the reply draft.
                tone: Desired tone for the reply, for example professional, concise, friendly.
                create_gmail_draft: When true, ask the workflow to create a mailbox draft. It must not send it.

            Returns:
                JSON response from the email draft workflow.
            """

            safe_message_id = clean_optional(message_id)
            safe_instructions = clean_optional(reply_instructions)
            safe_tone = clean_optional(tone) or "professional"

            if not safe_message_id:
                return {"error": "message_id is required"}

            if not safe_instructions:
                return {"error": "reply_instructions is required"}

            payload = {
                "message_id": safe_message_id,
                "reply_instructions": safe_instructions,
                "tone": safe_tone,
                "create_gmail_draft": bool(create_gmail_draft),
                "send_email": False,
                "source": "mcp-agent-hub",
            }

            log.info(
                "email_draft_reply called message_id=%s create_gmail_draft=%s",
                safe_message_id,
                create_gmail_draft,
            )
            return await self.client.draft_reply(payload)
