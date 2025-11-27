# -*- coding: utf-8 -*-
"""
Common parser data structures and enums.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Platform(str, Enum):
    YOUTUBE_MUSIC = "YouTube Music"
    YOUTUBE = "YouTube"
    UNKNOWN = "Unknown"


class MediaKind(str, Enum):
    TRACK = "track"
    PLAYLIST = "playlist"
    VIDEO = "video"
    UNKNOWN = "unknown"


@dataclass
class ParsedLink:
    platform: Platform
    kind: MediaKind
    original_url: str
    canonical_url: str
    video_id: Optional[str] = None
    playlist_id: Optional[str] = None
