# -*- coding: utf-8 -*-
"""
URL parser facade: delegates to platform-specific parsers.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.services.parser_types import MediaKind, ParsedLink, Platform

# Absolute import keeps tooling happy when running from project root.
from app.services.parsers import youtube

__all__ = ["Platform", "MediaKind", "ParsedLink", "detect_platform", "parse_url"]


def detect_platform(url: str) -> Platform:
    return parse_url(url).platform


def parse_url(url: str) -> ParsedLink:
    normalized = (url or "").strip()
    if not normalized:
        return ParsedLink(
            platform=Platform.UNKNOWN,
            kind=MediaKind.UNKNOWN,
            original_url=url,
            canonical_url=url,
        )

    parsed = urlparse(normalized if "://" in normalized else f"https://{normalized}")

    for parser in (youtube.parse_music, youtube.parse_youtube):
        parsed_link = parser(parsed, normalized)
        if parsed_link:
            return parsed_link

    return ParsedLink(
        platform=Platform.UNKNOWN,
        kind=MediaKind.UNKNOWN,
        original_url=url,
        canonical_url=normalized,
    )
