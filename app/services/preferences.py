"""
Persistent storage for per-user preferences (currently locale selection).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class UserPreferences:
    def __init__(self, storage_path: Path, default_locale: str):
        self._path = storage_path
        self._default_locale = default_locale
        self._lock = threading.Lock()
        self._data: dict[str, Any] = {}
        self._load()

    def get_locale(self, user_id: int | str) -> str | None:
        return self._data.get(str(user_id))

    def ensure_locale(self, user_id: int | str, locale: str | None = None) -> str:
        existing = self.get_locale(user_id)
        if existing:
            return existing
        chosen = locale or self._default_locale
        self.set_locale(user_id, chosen)
        return chosen

    def set_locale(self, user_id: int | str, locale: str) -> None:
        with self._lock:
            self._data[str(user_id)] = locale
            self._save_locked()

    def _load(self) -> None:
        if not self._path.exists():
            self._data = {}
            return
        try:
            content = self._path.read_text(encoding="utf-8")
            self._data = json.loads(content)
        except Exception:
            self._data = {}

    def _save_locked(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(self._data, ensure_ascii=False, indent=2)
        self._path.write_text(data, encoding="utf-8")
