"""
YouTube video downloader plugin powered by yt-dlp.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from app.services.downloader import DownloadResult
from app.services.parser_types import MediaKind, Platform


class YoutubeVideoPlugin:
    def __init__(self, max_height: int = 1080):
        self.max_height = max_height
        self._log = logging.getLogger(self.__class__.__name__)

    async def fetch(self, url: str, target_dir: Path) -> DownloadResult:
        info, file_path = await asyncio.to_thread(self._download, url, target_dir)
        self._log.info(
            "Downloaded video %s (%sp)",
            info.get("id"),
            info.get("height"),
        )
        metadata = self._extract_metadata(info)
        return DownloadResult(
            source_url=url,
            platform=Platform.YOUTUBE,
            kind=MediaKind.VIDEO,
            original_path=file_path,
            metadata=metadata,
            thumbnail_url=info.get("thumbnail"),
        )

    def _download(self, url: str, target_dir: Path) -> tuple[dict[str, Any], Path]:
        target_dir.mkdir(parents=True, exist_ok=True)
        ydl_opts = {
            "format": self._format_selector(),
            "outtmpl": str(target_dir / "%(id)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "restrictfilenames": True,
            "ignoreerrors": False,
            "no_warnings": True,
            "merge_output_format": "mp4",
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ],
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                self._log.debug("yt-dlp extracting video info for %s", url)
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
        except DownloadError as exc:
            raise RuntimeError(f"yt-dlp download failed: {exc}") from exc
        final_path = Path(filename)
        if final_path.suffix.lower() != ".mp4":
            final_path = final_path.with_suffix(".mp4")
        return info, final_path

    def _format_selector(self) -> str:
        limited = self.max_height
        return (
            f"(bestvideo[height<={limited}][ext=mp4]+bestaudio[ext=m4a])"
            f"/(bestvideo[height<={limited}]+bestaudio)"
            f"/best[height<={limited}]/best"
        )

    def _extract_metadata(self, info: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": info.get("title", ""),
            "artist": info.get("uploader") or info.get("channel") or "",
            "duration": info.get("duration") or 0,
            "width": info.get("width"),
            "height": info.get("height"),
        }
