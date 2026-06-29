from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from fastmcp import FastMCP


class AgentHubSkill(ABC):
    """Base interface for MCP Agent Hub skills."""

    name: str
    tool_names: tuple[str, ...] = ()

    def set_skill_registry(self, skills: Sequence[AgentHubSkill]) -> None:
        """Receive the discovered skill registry before tool registration."""

    @abstractmethod
    def register(self, mcp: FastMCP) -> None:
        """Register this skill's MCP tools."""
