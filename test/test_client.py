import asyncio
from typing import Iterable, Any, AsyncGenerator
from assistant.client import AssistantClient
from assistant.limiter import RateLimiter
from assistant.utils import get_message, format_chat
from config.settings import BASE_URL
from datasets.json_loader import extract_questions, DATA_DIR_PATH


class StopKeyFound(Exception):
    """Raised when the response contains the stop key — not retryable."""


class TalkerClient(AssistantClient):

    _ROUTE = "website.home"
    _MIN_INTERVAL: float = 25
    _MAX_RETRIES: int = 4
    _BACKOFF_BASE: float = 3.0
    _KEY_STOPPER = "تعذر الاتصال"

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
                answer = get_message(result)
                if answer and self._KEY_STOPPER in answer:
                    raise StopKeyFound(f"Stop key found in response for: {message!r}")
                return {"client": message, "chat": answer}

            except Exception:
                print(f"attempt: {attempt}")
                if attempt == self._MAX_RETRIES - 1:
                    break
                    # raise
                backoff = self._BACKOFF_BASE ** (attempt + 1)
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
                if result:
                    formated_result = format_chat(result)
                    print(formated_result)
                    file.write(formated_result)


if __name__ == "__main__":
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("\nInterrupted by user")