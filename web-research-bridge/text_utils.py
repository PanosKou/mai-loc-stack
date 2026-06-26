import re
from typing import Any
from urllib.parse import urlparse


def clamp(value: int | None, default: int, minimum: int, maximum: int) -> int:
    if value is None:
        value = default

    try:
        value = int(value)
    except Exception:
        value = default

    return max(minimum, min(value, maximum))


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate(text: str, max_chars: int) -> str:
    text = clean_text(text)

    if len(text) <= max_chars:
        return text

    return text[:max_chars].rstrip() + "..."


def is_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def extract_answer(llm_response: dict[str, Any]) -> str:
    choices = llm_response.get("choices") or []

    if not choices:
        return ""

    first = choices[0]
    message = first.get("message") or {}
    content = message.get("content")

    if content:
        return str(content).strip()

    text = first.get("text")

    if text:
        return str(text).strip()

    return ""
