# -*- coding: utf-8 -*-
"""
YouTube Music loader plugin stub.
"""

from __future__ import annotations

from app.services.downloader import DownloadResult
from app.services.parser import Platform


class YoutubeMusicPlugin:
    platform = Platform.YOUTUBE_MUSIC

    async def fetch(self, url: str) -> DownloadResult:
        # TODO: Implement yt-dlp integration.
        raise NotImplementedError
