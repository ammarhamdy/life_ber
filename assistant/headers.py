import random
from typing import Mapping

firefox_versions = list(range(120, 128))

os_options = [
    "X11; Linux x86_64",
    "X11; Ubuntu; Linux x86_64",
    "Windows NT 10.0; Win64; x64",
]

languages = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.8",
    "en-US,en;q=0.7,ar;q=0.3",
]

accepts = [
    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "text/html,application/xml;q=0.9,*/*;q=0.8",
]

encodings = [
    "gzip, deflate, br",
    "gzip, deflate",
]


def default_headers(base_url:  str) -> dict[str, str]:
    return {
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Origin": base_url,
                "Referer": f"{base_url}/",
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
                ),
            }


def random_agent() -> str:
    version = random.choice(firefox_versions)
    os_part = random.choice(os_options)
    return f"Mozilla/5.0 ({os_part}; rv:{version}.0) Gecko/20100101 Firefox/{version}.0"


def random_headers(
        base_url: str,
        accept: str | None = None,
        accept_encoding: str | None = None,
        accept_language: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    headers = {
        "User-Agent": random_agent(),
        "Accept": accept or random.choice(accepts),
        "Accept-Language": accept_language or random.choice(languages),
        "Accept-Encoding": accept_encoding or random.choice(encodings),
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": base_url,
        "Referer": f"{base_url}/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    if extra_headers:
        headers.update(extra_headers)

    return headers
