import re
from typing import Dict

import httpx


def _extract_csrf_from_html(html: str) -> str | None:
    """
    Parse the CSRF token from a Laravel-style meta tag:
        <meta name="csrf-token" content="TOKEN_VALUE">
    """
    pattern = r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    return match.group(1) if match else None


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