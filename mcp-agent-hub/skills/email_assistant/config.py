import os
from dataclasses import dataclass


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    email_search_webhook_url: str = os.getenv("EMAIL_SEARCH_WEBHOOK_URL", "").strip()
    email_read_webhook_url: str = os.getenv("EMAIL_READ_WEBHOOK_URL", "").strip()
    email_draft_reply_webhook_url: str = os.getenv("EMAIL_DRAFT_REPLY_WEBHOOK_URL", "").strip()

    email_default_max_results: int = env_int("EMAIL_DEFAULT_MAX_RESULTS", 5)
    email_max_results_hard: int = env_int("EMAIL_MAX_RESULTS_HARD", 10)
    email_request_timeout_seconds: float = env_float("EMAIL_REQUEST_TIMEOUT_SECONDS", 90.0)


settings = Settings()
