import asyncio
from assistant.client import AssistantClient
from assistant.service import AssistantService
from config.settings import BASE_URL
from datasets.json_loader import extract_questions, DATA_DIR_PATH
from reports.writer import write_chat_line
from config.logger import logger


async def main() -> None:

    questions = extract_questions(
        DATA_DIR_PATH / "chatbot_questions.json"
    )

    async with AssistantClient(
        base_url=BASE_URL,
        verify_ssl=False,
        debug=False,
    ) as client:
        service = AssistantService(client)
        async for result in service.chats(questions):
            if not result:
                continue
            write_chat_line(result)
            logger.debug( f"[OK] {result['client']} -> {result['chat']}")


if __name__ == "__main__":
    asyncio.run(main())