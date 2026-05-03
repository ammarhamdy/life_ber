import asyncio
import pprint
from typing import AsyncIterator, Iterable
from clients.http_client import AssistantClient
from clients.utils import get_message
from config.settings import BASE_URL
from infrastructure.loaders.json_loader import extract_questions, DATA_DIR_PATH


class TalkerClient(AssistantClient):

    _ROUTE = "website.home"

    def __init__(self) -> None:
        super().__init__(BASE_URL)

    def _build_history(self, message: str) -> list[dict[str, str]]:
        return [{"role": "user", "content": message}]

    async def _ask(self, message: str) -> dict[str, str | None]:
        """Send one message and return a normalised result dict."""
        result = await self.send_message(
            message=message,
            route_name=self._ROUTE,
            history=self._build_history(message),
        )
        return {
            "client": message,
            "chat":   get_message(result),
        }

    async def chat(self, message: str) -> dict[str, str | None]:
        """Send a single message and return the result."""
        return await self._ask(message)

    async def chats(self, messages: Iterable[str]) -> AsyncIterator[dict[str, str | None]]:
        """Yield results for each message in *messages* sequentially."""
        for message in messages:
            yield await self._ask(message)


async def start() -> None:
    async with TalkerClient() as client:
        questions = extract_questions(DATA_DIR_PATH / "chatbot_questions.json")
        with open(DATA_DIR_PATH / "chats.txt", 'w') as file:
            async for result in client.chats(questions):
                pprint.pprint(result, stream=file)


if __name__ == "__main__":
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("\nInterrupted by user")