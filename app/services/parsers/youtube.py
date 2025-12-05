"""
YouTube and YouTube Music URL parsing helpers.
"""

from __future__ import annotations

from typing import Final
from urllib.parse import ParseResult, parse_qs

from app.services.parser_types import MediaKind, ParsedLink, Platform

MUSIC_HOSTS: Final[tuple[str, ...]] = ("music.youtube.com",)
YOUTUBE_HOSTS: Final[tuple[str, ...]] = (
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
)


def parse_music(parsed: ParseResult, original: str) -> ParsedLink | None:
    host = (parsed.hostname or "").lower()
    if host not in MUSIC_HOSTS:
        return None
    return _parse(parsed, original=original, platform=Platform.YOUTUBE_MUSIC)


def parse_youtube(parsed: ParseResult, original: str) -> ParsedLink | None:
    host = (parsed.hostname or "").lower()
    if host not in YOUTUBE_HOSTS:
        return None
    return _parse(parsed, original=original, platform=Platform.YOUTUBE)


def _parse(parsed: ParseResult, original: str, platform: Platform) -> ParsedLink | None:
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    qs = parse_qs(parsed.query or "")

    video_id = None
    playlist_id = None

    if host == "youtu.be":
        video_id = path.lstrip("/") or None
    elif path.startswith("/watch") or path == "/":
        video_id = _first(qs.get("v"))
        playlist_id = _first(qs.get("list"))
    elif path.startswith("/playlist"):
        playlist_id = _first(qs.get("list"))

    if not video_id and not playlist_id:
        return None

    kind = MediaKind.TRACK if video_id else MediaKind.PLAYLIST
    canonical_url = _canonicalize(platform=platform, video_id=video_id, playlist_id=playlist_id)

    return ParsedLink(
        platform=platform,
        kind=kind,
        original_url=original,
        canonical_url=canonical_url,
        video_id=video_id,
        playlist_id=playlist_id,
    )


def _canonicalize(platform: Platform, video_id: str | None, playlist_id: str | None) -> str:
    base = (
        "https://music.youtube.com"
        if platform is Platform.YOUTUBE_MUSIC
        else "https://www.youtube.com"
    )
    if video_id:
        suffix = f"/watch?v={video_id}"
        if playlist_id:
            suffix += f"&list={playlist_id}"
        return f"{base}{suffix}"
    if playlist_id:
        return f"{base}/playlist?list={playlist_id}"
    return base


def _first(items: list[str] | None) -> str | None:
    return items[0] if items else None
