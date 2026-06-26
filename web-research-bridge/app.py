import logging
import os
from typing import Any

from fastapi import FastAPI

from config import settings
from models import ResearchRequest
from research_service import run_research


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

log = logging.getLogger("web-research-bridge")

app = FastAPI(title="Web Research Bridge", version="0.3.0")


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "mode": "langgraph",
        "searxng_url": settings.searxng_url,
        "scrape_url": settings.scrape_url,
        "llm_base_url": settings.llm_base_url,
        "llm_model": settings.llm_model,
        "max_concurrent_research": settings.max_concurrent_research,
    }


@app.post("/research")
async def research(request: ResearchRequest) -> dict[str, Any]:
    return await run_research(request)
