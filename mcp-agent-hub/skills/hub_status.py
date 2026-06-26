from fastmcp import FastMCP

from .base import AgentHubSkill


class HubStatusSkill(AgentHubSkill):
    name = "hub_status"
    tool_names = ("hub_status",)

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool
        async def hub_status() -> str:
            """
            Return Agent Hub service status.
            """

            return (
                "Agent Hub is online.\n\n"
                "Configured tools:\n"
                "- hub_status\n"
                "- tts_generate_audio\n"
                "- personal_assistant_task\n\n"
                "Planned tools:\n"
                "- osint_investigate\n"
                "- code_agent_task\n"
                "- opencti_lookup\n"
                "- osiris_query"
            )
