"""
Common parser data structures and enums.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
    video_id: str | None = None
    playlist_id: str | None = None
