import asyncio
from typing import Iterable, AsyncGenerator
from assistant.client import AssistantClient
from assistant.limiter import RateLimiter
from assistant.utils import get_message


class StopKeyFound(Exception):
    """Raised when the response contains the stop key — not retryable."""


class AssistantService:

    ROUTE = "website.home"
    STOP_KEY = "تعذر الاتصال"

    def __init__(
        self,
        client: AssistantClient,
        min_interval: float | int = 25,
        max_retries: int = 4,
        backoff_base: float | int = 3.0,
    ) -> None:
        self._client = client
        self._limiter = RateLimiter(min_interval)
        self._max_retries = max_retries
        self._backoff_base = backoff_base

    @staticmethod
    def _history(message: str) -> list[dict[str, str]]:
        return [
            {
                "role": "user",
                "content": message,
            }
        ]

    async def ask(
            self,
            message: str,
    ) -> dict[str, str | None] | None:
        """Send one message with proactive throttling and exponential-backoff retry."""
        for attempt in range(self._max_retries):
            await self._limiter.acquire()
            try:
                result = await self._client.send_message(
                    message=message,
                    route_name=self.ROUTE,
                    history=self._history(message),
                )

                answer = get_message(result)
                if answer and self.STOP_KEY in answer:
                    raise StopKeyFound()

                return {
                    "client": message,
                    "chat": answer,
                }

            except StopKeyFound:
                raise

            except Exception:
                if attempt == self._max_retries - 1:
                    return None
                await asyncio.sleep(
                    self._backoff_base ** (attempt + 1)
                )

        return None

    async def chats(
        self,
        messages: Iterable[str],
    ) -> AsyncGenerator[dict[str, str | None] | None, None]:
        """Yield results for each message in *messages* sequentially."""
        for message in messages:
            yield await self.ask(message)