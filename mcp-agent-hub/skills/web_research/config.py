import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    searxng_url: str = os.getenv("SEARXNG_URL", "http://127.0.0.1:8080/search")
    scrape_url: str = os.getenv("SCRAPE_URL", "http://192.168.1.81:5678/webhook/scrape-url")

    # This must be LangGraph, not Ollama.
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/")
    llm_model: str = os.getenv("LLM_MODEL", "onyx-fast")
    llm_api_key: str = os.getenv("LLM_API_KEY", "local-dummy-key")

    default_max_results: int = int(os.getenv("DEFAULT_MAX_RESULTS", "1"))
    max_results_hard: int = int(os.getenv("MAX_RESULTS_HARD", "2"))

    default_max_chars_per_page: int = int(os.getenv("DEFAULT_MAX_CHARS_PER_PAGE", "2500"))
    max_chars_per_page_hard: int = int(os.getenv("MAX_CHARS_PER_PAGE_HARD", "5000"))
    max_total_context_chars: int = int(os.getenv("MAX_TOTAL_CONTEXT_CHARS", "6000"))

    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "384"))
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    search_timeout_seconds: float = float(os.getenv("SEARCH_TIMEOUT_SECONDS", "15"))
    scrape_timeout_seconds: float = float(os.getenv("SCRAPE_TIMEOUT_SECONDS", "25"))
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

    max_concurrent_research: int = int(os.getenv("MAX_CONCURRENT_RESEARCH", "1"))


settings = Settings()
