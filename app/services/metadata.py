# -*- coding: utf-8 -*-
"""
External metadata enrichment (e.g., Apple Music).
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

import aiohttp

log = logging.getLogger(__name__)


class CleanMetadata(TypedDict, total=False):
    artist: str
    title: str
    album: str
    cover_url: str
    genre: str
    year: str


async def fetch_clean_metadata(query: str) -> CleanMetadata | None:
    """
    Query Apple iTunes Search API for cleaned metadata.
    """
    url = "https://itunes.apple.com/search"
    params = {
        "term": query,
        "media": "music",
        "entity": "song",
        "limit": 1,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    log.debug("Apple metadata: status %s for %s", resp.status, query)
                    return None
                data: dict[str, Any] = await resp.json()
    except Exception as exc:  # network / JSON errors
        log.debug("Apple metadata request failed for %s: %s", query, exc)
        return None

    if not data or data.get("resultCount", 0) == 0:
        return None
    track = data["results"][0]
    cover = track.get("artworkUrl100") or ""
    cover_hd = cover.replace("100x100", "600x600") if cover else ""
    return {
        "artist": track.get("artistName", ""),
        "title": track.get("trackName", ""),
        "album": track.get("collectionName", ""),
        "cover_url": cover_hd,
        "genre": track.get("primaryGenreName", ""),
        "year": (track.get("releaseDate") or "")[:4],
    }
