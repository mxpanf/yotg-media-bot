"""
YouTube Music loader plugin using yt-dlp.
"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from app.services.downloader import DownloadResult
from app.services.metadata import fetch_clean_metadata
from app.services.parser_types import Platform


class YoutubeMusicPlugin:
    def __init__(self, audio_format: str = "bestaudio/best"):
        self.audio_format = audio_format
        self._log = logging.getLogger(self.__class__.__name__)

    async def fetch(self, url: str, target_dir: Path) -> DownloadResult:
        info, file_path = await asyncio.to_thread(self._download, url, target_dir)
        self._log.info("Downloaded track %s to %s", info.get("id"), file_path)
        metadata = self._extract_metadata(info)
        metadata = await self._enrich_metadata(metadata)
        return DownloadResult(
            source_url=url,
            platform=Platform.YOUTUBE_MUSIC,
            original_path=file_path,
            metadata=metadata,
            thumbnail_url=metadata.get("thumbnail_url") or info.get("thumbnail"),
        )

    def _download(self, url: str, target_dir: Path) -> tuple[dict[str, Any], Path]:
        target_dir.mkdir(parents=True, exist_ok=True)
        ydl_opts = {
            "format": self.audio_format,
            "outtmpl": str(target_dir / "%(id)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "restrictfilenames": True,
            "ignoreerrors": False,
            "no_warnings": True,
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                self._log.debug("yt-dlp extracting info for %s", url)
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
        except DownloadError as exc:
            raise RuntimeError(f"yt-dlp download failed: {exc}") from exc
        return info, Path(filename)

    def _extract_metadata(self, info: dict[str, Any]) -> dict[str, Any]:
        artists = info.get("artists") or []
        artist = ", ".join(artists) if isinstance(artists, list) else info.get("artist")
        return {
            "title": info.get("title", ""),
            "artist": artist or info.get("uploader") or "",
            "album": info.get("album") or "",
            "duration": info.get("duration") or 0,
        }

    async def _enrich_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        raw_title = metadata.get("title") or ""
        title = self._sanitize_title(raw_title)
        artist = metadata.get("artist") or ""
        query = f"{artist} - {title}" if artist else title
        if not query:
            return metadata
        clean = await fetch_clean_metadata(query)
        if not clean:
            self._log.debug("Apple metadata not found for query: %s", query)
            fallback = metadata.copy()
            fallback["title"] = title
            return fallback
        self._log.info("Apple metadata matched: %s", query)
        enriched = metadata.copy()
        enriched["artist"] = clean.get("artist") or enriched.get("artist", "")
        enriched["title"] = clean.get("title") or title or enriched.get("title", "")
        enriched["album"] = clean.get("album") or enriched.get("album", "")
        enriched["genre"] = clean.get("genre") or enriched.get("genre", "")
        enriched["year"] = clean.get("year") or enriched.get("year", "")
        cover = clean.get("cover_url")
        if cover:
            enriched["thumbnail_url"] = cover
        return enriched

    def _sanitize_title(self, title: str) -> str:
        """Strip common noise like 'Official Video', 'Lyrics', resolutions, etc."""
        noise_keywords = (
            "official",
            "music video",
            "video oficial",
            "lyrics",
            "lyric",
            "audio",
            "mv",
            "clip",
            "hd",
            "4k",
            "1080p",
            "explicit",
            "clean version",
            "topic",
        )

        def _remove_noisy_brackets(text: str) -> str:
            pattern = re.compile(r"[\(\[\{](.*?)[\)\]\}]", flags=re.IGNORECASE)
            result = text
            for match in list(pattern.finditer(text)):
                content = match.group(1).lower()
                if any(keyword in content for keyword in noise_keywords):
                    result = result.replace(match.group(0), "")
            return result

        cleaned = _remove_noisy_brackets(title)
        cleaned = re.sub(
            r"(?:\s*[-|–—]\s*(?:official.*|lyrics?.*|music video.*|audio.*|video.*|mv.*|hd.*|4k.*|1080p.*|topic.*))$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -–—\t")
        return cleaned or title
