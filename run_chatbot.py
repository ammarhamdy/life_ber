


async def main():
    async with AssistantClient(...) as client:

        questions = load_questions(DATASET_FILE)

        writer = ChatWriter(REPORT_FILE)

        async for result in client.ask_many(questions):
            writer.write(result)