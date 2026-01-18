from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_CONFIGURED = False


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def setup_logging(
    *,
    level: Optional[str] = None,
    log_file: Optional[str | Path] = None,
) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    resolved_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    numeric_level = getattr(logging, resolved_level, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setLevel(numeric_level)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    resolved_log_file = (
        Path(log_file)
        if log_file is not None
        else (_project_root() / "logs" / "app.log")
    )
    resolved_log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=str(resolved_log_file),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name if name else "novelAI")

