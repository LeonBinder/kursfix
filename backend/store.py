"""Kurskonfiguration als JSON-Datei, damit sie den Neustart überlebt."""
from __future__ import annotations

import json
from pathlib import Path

from .models import AppConfig

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONFIG_FILE = DATA_DIR / "config.json"


def load_config(path: Path = CONFIG_FILE) -> AppConfig:
    try:
        return AppConfig.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return AppConfig()


def save_config(config: AppConfig, path: Path = CONFIG_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
