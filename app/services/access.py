"""
Persistent access control (allowed users and admin roles).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Literal

Role = Literal["user", "admin"]


class AccessControl:
    def __init__(self, storage_path: Path, root_admin_id: int):
        self._path = storage_path
        self._lock = threading.Lock()
        self._root_admin_id = root_admin_id
        self._data: dict[str, Role] = {}
        self._load()
        self._ensure_root_admin()

    def is_root(self, user_id: int | None) -> bool:
        return user_id is not None and user_id == self._root_admin_id

    def is_admin(self, user_id: int | None) -> bool:
        if user_id is None:
            return False
        return self.is_root(user_id) or self._data.get(str(user_id)) == "admin"

    def is_allowed(self, user_id: int | None) -> bool:
        if user_id is None:
            return False
        if self.is_admin(user_id):
            return True
        return self._data.get(str(user_id)) == "user"

    def add_user(self, user_id: int) -> bool:
        with self._lock:
            key = str(user_id)
            previous = self._data.get(key)
            if previous == "admin":
                return False
            if previous == "user":
                return False
            self._data[key] = "user"
            self._save_locked()
            return True

    def remove_user(self, user_id: int) -> bool:
        if self.is_root(user_id):
            return False
        with self._lock:
            removed = self._data.pop(str(user_id), None)
            self._save_locked()
            return removed is not None

    def promote(self, user_id: int) -> bool:
        if self.is_root(user_id):
            return False
        with self._lock:
            key = str(user_id)
            previous = self._data.get(key)
            self._data[key] = "admin"
            self._save_locked()
            return previous != "admin"

    def demote(self, user_id: int) -> bool:
        if self.is_root(user_id):
            return False
        with self._lock:
            key = str(user_id)
            if key not in self._data:
                return False
            self._data[key] = "user"
            self._save_locked()
            return True

    def _ensure_root_admin(self) -> None:
        key = str(self._root_admin_id)
        with self._lock:
            if self._root_admin_id == 0:
                return
            if self._data.get(key) != "admin":
                self._data[key] = "admin"
                self._save_locked()

    def _load(self) -> None:
        if not self._path.exists():
            self._data = {}
            return
        try:
            content = self._path.read_text(encoding="utf-8")
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                self._data = {
                    str(k): ("admin" if v == "admin" else "user") for k, v in parsed.items()
                }
            else:
                self._data = {}
        except Exception:
            self._data = {}

    def _save_locked(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._data, ensure_ascii=False, indent=2)
        self._path.write_text(payload, encoding="utf-8")
