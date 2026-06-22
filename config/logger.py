import logging
from pathlib import Path

LOG_FILE = Path("reports/app.log")


def setup_logger(name: str = "assistant") -> logging.Logger:
    """
    Central logger configuration for the entire project.
    """

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # avoid duplicate handlers

    logger.setLevel(logging.DEBUG)

    # --- format ---
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- console handler ---
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    # --- file handler ---
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
