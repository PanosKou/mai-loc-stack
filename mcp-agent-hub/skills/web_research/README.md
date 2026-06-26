# Web research skill

This directory owns the full web research capability.

It contains both:

- the MCP-facing `advanced_web_research` tool exposed by the Agent Hub
- the implementation pipeline used by that tool

Pipeline:

```text
advanced_web_research
  -> SearXNG search
  -> n8n scrape workflow
  -> LangGraph summarisation
  -> Ollama through LangGraph
```

The skill does not call Ollama directly.

## MCP runtime

The skill is loaded automatically by `mcp-agent-hub/server.py` through dynamic skill discovery.

## Optional HTTP runtime

If a HTTP `/research` endpoint is still needed for compatibility, run it from the `mcp-agent-hub` directory:

```bash
uvicorn skills.web_research.app:app --host 0.0.0.0 --port 8092
```

This replaces the old top-level `web-research-bridge/` service directory.
