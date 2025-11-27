# -*- coding: utf-8 -*-
"""
Post-processing stubs (conversion, metadata).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PostProcessResult:
    audio_path: Path
    thumb_path: Path | None = None


async def convert_and_tag(source: Path, metadata: dict) -> PostProcessResult:
    # TODO: Implement ffmpeg conversion and metadata embedding.
    return PostProcessResult(audio_path=source, thumb_path=None)
