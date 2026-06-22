from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict


DEFAULT_REPORT_PATH = Path("reports/chats.v3.txt")


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def format_chat_line(result: Dict[str, Optional[str]]) -> str:
    """
    Convert a chat result into a consistent text line format.
    """
    client = result.get("client") or "<unknown>"
    chat = result.get("chat") or "<empty>"
    return f"[{_timestamp()}] USER: {client}\nAI: {chat}\n{'-' * 60}\n"


def write_chat_line(
    result: Dict[str, Optional[str]],
    file_path: Path = DEFAULT_REPORT_PATH,
    mode: str = "a",
) -> None:
    """
    Append a single chat result into a report file.

    Args:
        result: {"client": str, "chat": str}
        file_path: target report file
        mode: file mode (default append)
    """
    _ensure_dir(file_path)
    line = format_chat_line(result)
    with file_path.open(mode, encoding="utf-8") as f:
        f.write(line)


def write_batch(
    results: list[Dict[str, Optional[str]]],
    file_path: Path = DEFAULT_REPORT_PATH,
) -> None:
    """
    Write multiple results in one go.
    Useful for batch runs / offline evaluation.
    """
    _ensure_dir(file_path)
    with file_path.open("a", encoding="utf-8") as f:
        for result in results:
            f.write(format_chat_line(result))