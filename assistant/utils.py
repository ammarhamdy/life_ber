import re
from typing import Dict


CSRF_PATTERNS =  tuple([
        r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']',
        r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']csrf-token["\']',
        r'<meta\s+name=["\']_token["\']\s+content=["\']([^"\']+)["\']',
        r'<input[^>]+name=["\']_token["\']\s+value=["\']([^"\']+)["\']',
    ])


def extract_csrf_from_html(html: str, patterns= CSRF_PATTERNS) -> str | None:
    for pattern in patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def get_message(res: dict) -> str | None:
    """
    Safely extract data.content.message from API response.
    Returns None if anything is missing or invalid.
    """

    if not isinstance(res, dict):
        return None

    data = res.get("data")
    if not isinstance(data, dict):
        return None

    content = data.get("content")
    if not isinstance(content, dict):
        return None

    message = content.get("message")
    if isinstance(message, str):
        return message.strip()

    return None


def format_chat(chat: dict[str, str | None]) -> str:
    return (
        f"Client:\n{chat['client']}\n\n"
        f"Bot:\n{chat['chat']}\n"
    )


def safe_get(obj: Dict, *keys, default=None):
    """Safely navigate nested dictionary keys"""
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key, {})
        else:
            return default
    return obj if obj != {} else default