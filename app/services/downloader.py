"""
Media downloader stubs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.services.parser_types import Platform


@dataclass
class DownloadResult:
    source_url: str
    platform: Platform
    original_path: Path
    metadata: dict[str, Any]
    thumbnail_url: str | None = None


class Downloader(Protocol):
    async def fetch(self, url: str, target_dir: Path) -> DownloadResult: ...
