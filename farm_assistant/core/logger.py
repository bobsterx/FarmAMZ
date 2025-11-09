from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from colorama import Fore, Style, init

init(autoreset=True)


def _colored(level: str, message: str) -> str:
    color = {
        "OK": Fore.GREEN,
        "INFO": Fore.CYAN,
        "WARN": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED,
        "ADVICE": Fore.MAGENTA,
    }.get(level.upper(), Fore.WHITE)
    return f"{color}[{level.upper()}]{Style.RESET_ALL} {message}"


class FarmLogger:
    def __init__(self, log_file: Path = Path("logs/farm_log.txt")):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("farm_assistant")
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file, encoding="utf-8")
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log(self, level: str, message: str, payload: Dict[str, Any] | None = None) -> None:
        print(_colored(level, message))
        entry = {"level": level, "message": message}
        if payload:
            entry["payload"] = payload
        self.logger.info(json.dumps(entry, ensure_ascii=False))

    def log_json(self, payload: Dict[str, Any]) -> None:
        self.logger.info(json.dumps(payload, ensure_ascii=False))
