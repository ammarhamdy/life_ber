"""Handles loading JSON data from files."""

import json
from pathlib import Path
from typing import Any, List, Dict, Generator
from config.settings import BASE_DIR
from utils.data_handlers import safe_get

DATA_DIR_PATH = BASE_DIR / "data"


class JSONLoader:

    """
    Loads raw JSON data from files.

    Responsibility: File I/O operations only.
    Does NOT validate or parse Jira-specific structure.
    """

    @staticmethod
    def load_from_file(file_path: str) -> Any:
        """
        Load JSON data from a file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data (could be dict, list, etc.)

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save_to_file(data: Any, file_path: str) -> None:
        """
        Save data to a JSON file.

        Args:
            data: Data to serialize
            file_path: Output file path
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def extract_questions(source_json: str) -> Generator[Any, Any, None]:
    raw_data = JSONLoader.load_from_file(source_json)
    categories = safe_get(raw_data, 'chatbot', 'categories')
    if categories:
        for category in categories:
            questions: List[Dict[str, str | List | None]] = safe_get(category, 'questions')
            for question_dict in questions:
                question = safe_get(question_dict, 'question')
                yield question


if __name__ == '__main__':
    for i in extract_questions(DATA_DIR_PATH / "chatbot_questions.json"):
        print(i)
