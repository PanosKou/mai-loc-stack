import asyncio
import logging
from typing import Any

from .clients import call_langgraph, scrape_url, searxng_search
from .config import settings
from .failures import ResearchFailure
from .models import ResearchRequest
from .text_utils import clean_text, truncate, clamp


log = logging.getLogger("mcp-agent-hub.skills.web_research.service")
research_semaphore = asyncio.Semaphore(settings.max_concurrent_research)


async def collect_pages(
    search_results: list[dict[str, str]],
    max_chars_per_page: int,
) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []

    for result in search_results:
        url = result["url"]

        try:
            scraped = await scrape_url(url)
            title = clean_text(scraped.get("title")) or result["title"]
            h1 = clean_text(scraped.get("h1"))
            text = clean_text(scraped.get("text"))
            scrape_ok = True
            scrape_error = None
        except ResearchFailure as exc:
            log.warning("scrape_failed url=%s reason=%s", url, exc.reason)
            title = result["title"]
            h1 = ""
            text = result["snippet"]
            scrape_ok = False
            scrape_error = exc.reason
        except Exception:
            log.warning("unexpected_scrape_error url=%s", url)
            title = result["title"]
            h1 = ""
            text = result["snippet"]
            scrape_ok = False
            scrape_error = "unexpected_scrape_error"

        pages.append(
            {
                "title": title,
                "h1": h1,
                "url": url,
                "text": truncate(text, max_chars_per_page),
                "scrape_ok": scrape_ok,
                "scrape_error": scrape_error,
            }
        )

    return pages


def build_context(pages: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    remaining = settings.max_total_context_chars

    for index, page in enumerate(pages, start=1):
        if remaining <= 0:
            break

        title = clean_text(page.get("title"))
        url = clean_text(page.get("url"))
        text = clean_text(page.get("text"))

        header = f"[{index}] {title}\nURL: {url}\nCONTENT:\n"
        available_for_text = max(0, remaining - len(header) - 2)

        if available_for_text <= 0:
            break

        section_text = truncate(text, available_for_text)
        section = header + section_text

        sections.append(section)
        remaining -= len(section)

    return "\n\n".join(sections)


async def run_research(request: ResearchRequest) -> dict[str, Any]:
    async with research_semaphore:
        max_results = clamp(
            request.max_results,
            settings.default_max_results,
            1,
            settings.max_results_hard,
        )

        max_chars_per_page = clamp(
            request.max_chars_per_page,
            settings.default_max_chars_per_page,
            500,
            settings.max_chars_per_page_hard,
        )

        task = clean_text(request.task)

        log.info(
            "research_started task=%r max_results=%s max_chars_per_page=%s llm_base_url=%s model=%s",
            task,
            max_results,
            max_chars_per_page,
            settings.llm_base_url,
            settings.llm_model,
        )

        search_results = await searxng_search(task, max_results=max_results)

        if not search_results:
            log.warning("no_usable_search_results task=%r", task)
            raise ResearchFailure("no_usable_search_results")

        pages = await collect_pages(search_results, max_chars_per_page=max_chars_per_page)
        context = build_context(pages)

        if not context.strip():
            log.warning("no_usable_scrape_context task=%r", task)
            raise ResearchFailure("no_usable_scrape_context")

        answer = await call_langgraph(task=task, context=context)

        log.info(
            "research_finished task=%r results=%s pages=%s",
            task,
            len(search_results),
            len(pages),
        )

        return {
            "mode": "langgraph",
            "model": settings.llm_model,
            "task": task,
            "answer": answer,
            "search_results": search_results,
            "scraped_pages": [
                {
                    "title": page["title"],
                    "url": page["url"],
                    "chars": len(page["text"]),
                    "scrape_ok": page["scrape_ok"],
                    "scrape_error": page["scrape_error"],
                }
                for page in pages
            ],
            "limits": {
                "max_results": max_results,
                "max_chars_per_page": max_chars_per_page,
                "max_total_context_chars": settings.max_total_context_chars,
                "llm_max_tokens": settings.llm_max_tokens,
                "max_concurrent_research": settings.max_concurrent_research,
            },
        }
