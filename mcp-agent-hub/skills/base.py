from abc import ABC, abstractmethod

from fastmcp import FastMCP


class AgentHubSkill(ABC):
    """Base interface for MCP Agent Hub skills."""

    name: str
    tool_names: tuple[str, ...] = ()

    @abstractmethod
    def register(self, mcp: FastMCP) -> None:
        """Register this skill's MCP tools."""
