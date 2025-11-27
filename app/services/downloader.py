# -*- coding: utf-8 -*-
"""
Media downloader stubs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.services.parser import Platform


@dataclass
class DownloadResult:
    source_url: str
    platform: Platform
    original_path: Path
    metadata: dict


class Downloader(Protocol):
    async def download(self, url: str) -> DownloadResult: ...
