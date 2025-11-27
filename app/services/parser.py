# -*- coding: utf-8 -*-
"""
URL parser and platform detector.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Final


class Platform(str, Enum):
    YOUTUBE_MUSIC = "YouTube Music"
    UNKNOWN = "Unknown"


YTM_DOMAINS: Final[tuple[str, ...]] = ("music.youtube.com", "youtu.be")


def detect_platform(url: str) -> Platform:
    normalized = url.strip()
    if not normalized:
        return Platform.UNKNOWN
    if _is_youtube_music(normalized):
        return Platform.YOUTUBE_MUSIC
    return Platform.UNKNOWN


def _is_youtube_music(url: str) -> bool:
    if any(domain in url for domain in YTM_DOMAINS):
        return True
    pattern = re.compile(r"https?://(www\.)?youtube\.com/watch\?v=")
    return bool(pattern.search(url))
