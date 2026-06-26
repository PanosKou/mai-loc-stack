import logging
import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from skills import discover_skills


load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8094"))

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

log = logging.getLogger("mcp-agent-hub")


def create_mcp_server() -> FastMCP:
    """Create the MCP Agent Hub server and register discovered skills."""

    mcp = FastMCP("agent-hub")
    skills = discover_skills()

    for skill in skills:
        skill.register(mcp)
        log.info(
            "registered skill=%s tools=%s",
            skill.name,
            ",".join(skill.tool_names) if skill.tool_names else "unknown",
        )

    return mcp


mcp = create_mcp_server()


if __name__ == "__main__":
    log.info("Starting MCP Agent Hub on %s:%s", HOST, PORT)
    mcp.run(
        transport="http",
        host=HOST,
        port=PORT,
    )
