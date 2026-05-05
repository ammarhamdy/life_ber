import asyncio
import pprint
import time
from typing import Iterable, Any, AsyncGenerator

import httpx

from clients.http_client import AssistantClient
from clients.utils import get_message
from config.settings import BASE_URL
from infrastructure.loaders.json_loader import extract_questions, DATA_DIR_PATH


class RateLimiter:
    """Proactive token-bucket style limiter: ensures a minimum gap between calls."""

    def __init__(self, min_interval: float) -> None:
        self._min_interval = min_interval
        self._last_called: float = 0.0

    async def acquire(self) -> None:
        elapsed = time.monotonic() - self._last_called
        wait = self._min_interval - elapsed
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_called = time.monotonic()


class TalkerClient(AssistantClient):

    _ROUTE = "website.home"
    _MIN_INTERVAL: float = 1.5
    _MAX_RETRIES: int = 4
    _BACKOFF_BASE: float = 2.0

    def __init__(self) -> None:
        super().__init__(BASE_URL)
        self._limiter = RateLimiter(self._MIN_INTERVAL)

    @staticmethod
    def _build_history(message: str) -> list[dict[str, str]]:
        return [{"role": "user", "content": message}]

    async def _ask(self, message: str) -> dict[str, str | None] | None:
        """Send one message with proactive throttling and exponential-backoff retry."""
        for attempt in range(self._MAX_RETRIES):
            await self._limiter.acquire()
            try:
                result = await self.send_message(
                    message=message,
                    route_name=self._ROUTE,
                    history=self._build_history(message),
                )
                return {
                    "client": message,
                    "chat":   get_message(result),
                }
            except httpx.HTTPStatusError:
                if attempt == self._MAX_RETRIES - 1:
                    raise
                backoff = self._BACKOFF_BASE ** attempt     # 2s → 4s → 8s → 16s
                await asyncio.sleep(backoff)
        return None

    async def chat(self, message: str) -> dict[str, str | None] | None:
        """Send a single message and return the result."""
        return await self._ask(message)

    async def chats(self, messages: Iterable[str]) -> AsyncGenerator[dict[str, str | None] | None, Any]:
        """Yield results for each message in *messages* sequentially."""
        for message in messages:
            yield await self._ask(message)


async def start() -> None:
    async with TalkerClient() as client:
        questions = extract_questions(DATA_DIR_PATH / "chatbot_questions.json")
        with open(DATA_DIR_PATH / "chats.txt", "w") as file:
            async for result in client.chats(questions):
                pprint.pprint(result)
                pprint.pprint(result, stream=file)


if __name__ == "__main__":
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("\nInterrupted by user")