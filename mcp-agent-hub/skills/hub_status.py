from __future__ import annotations

from typing import Sequence

from fastmcp import FastMCP

from .base import AgentHubSkill


class HubStatusSkill(AgentHubSkill):
    name = "hub_status"
    tool_names = ("hub_status",)

    def __init__(self) -> None:
        self.skills: Sequence[AgentHubSkill] = ()

    def set_skill_registry(self, skills: Sequence[AgentHubSkill]) -> None:
        self.skills = skills

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool
        async def hub_status() -> str:
            """
            Return Agent Hub service status.
            """

            lines = [
                "Agent Hub is online.",
                "",
                "Registered skills:",
            ]

            for skill in self.skills:
                tools = ", ".join(skill.tool_names) if skill.tool_names else "no tools"
                lines.append(f"- {skill.name}: {tools}")

            return "\n".join(lines)
