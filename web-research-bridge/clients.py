from typing import Any

import httpx
from fastapi import HTTPException

from config import settings
from text_utils import clean_text, extract_answer, is_http_url


async def searxng_search(query: str, max_results: int) -> list[dict[str, str]]:
    timeout = httpx.Timeout(settings.search_timeout_seconds)
    limits = httpx.Limits(max_connections=3, max_keepalive_connections=1)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        response = await client.post(
            settings.searxng_url,
            data={
                "q": query,
                "format": "json",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "SearXNG request failed",
                "status_code": response.status_code,
                "body": response.text[:1000],
            },
        )

    payload = response.json()
    raw_results = payload.get("results") or []

    results: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for item in raw_results:
        url = clean_text(item.get("url"))

        if not url or not is_http_url(url) or url in seen_urls:
            continue

        seen_urls.add(url)

        title = clean_text(item.get("title")) or url
        snippet = clean_text(item.get("content") or item.get("description") or "")

        results.append(
            {
                "title": title,
                "url": url,
                "snippet": snippet,
            }
        )

        if len(results) >= max_results:
            break

    return results


async def scrape_url(url: str) -> dict[str, Any]:
    timeout = httpx.Timeout(settings.scrape_timeout_seconds)
    limits = httpx.Limits(max_connections=2, max_keepalive_connections=1)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        response = await client.post(
            settings.scrape_url,
            json={"url": url},
            headers={"Content-Type": "application/json"},
        )

    if response.status_code >= 400:
        raise RuntimeError(f"n8n scrape failed: status={response.status_code} body={response.text[:500]}")

    payload = response.json()

    if isinstance(payload, list):
        if not payload:
            return {}
        payload = payload[0]

    if not isinstance(payload, dict):
        return {}

    return payload


async def call_langgraph(task: str, context: str) -> str:
    endpoint = f"{settings.llm_base_url}/chat/completions"

    system_prompt = (
        "You are the summarisation step of a local web research pipeline. "
        "Use only the supplied source snippets. "
        "Keep the answer short, technical, and precise. "
        "Prefer official documentation when present. "
        "Cite sources inline using [1], [2], etc. "
        "If the sources are insufficient, say that clearly."
    )

    user_prompt = (
        f"Research task:\n{task}\n\n"
        f"Source snippets:\n{context}\n\n"
        "Return a short answer followed by a compact Sources section."
    )

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "stream": False,
    }

    timeout = httpx.Timeout(settings.llm_timeout_seconds)
    limits = httpx.Limits(max_connections=1, max_keepalive_connections=1)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        response = await client.post(
            endpoint,
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "LangGraph chat completion failed",
                "status_code": response.status_code,
                "endpoint": endpoint,
                "body": response.text[:1000],
            },
        )

    answer = extract_answer(response.json())

    if not answer:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "LangGraph returned an empty answer",
                "endpoint": endpoint,
            },
        )

    return answer
