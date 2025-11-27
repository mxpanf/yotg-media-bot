"""
Post-processing: conversion to mp3 and ID3 tagging with cover art.
"""

from __future__ import annotations

import asyncio
import logging
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1, ID3NoHeaderError  # type: ignore[attr-defined]
from mutagen.id3 import error as ID3Error  # type: ignore[attr-defined]
from mutagen.mp3 import MP3

_log = logging.getLogger("postprocess")


@dataclass
class PostProcessResult:
    audio_path: Path
    thumb_path: Path | None = None


async def convert_and_tag(
    source: Path,
    metadata: dict[str, Any],
    work_dir: Path,
    thumbnail_url: str | None,
) -> PostProcessResult:
    output = work_dir / f"{source.stem}.mp3"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-ab",
        "192k",
        str(output),
    ]
    _log.info("Running ffmpeg for %s", source.name)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        _log.error("ffmpeg failed: %s", stderr.decode(errors="ignore"))
        raise RuntimeError("ffmpeg conversion failed")

    thumb_path = await _download_thumbnail(thumbnail_url, work_dir) if thumbnail_url else None
    await _write_id3(output, metadata, thumb_path)
    try:
        source.unlink(missing_ok=True)
    except OSError:
        pass
    return PostProcessResult(audio_path=output, thumb_path=thumb_path)


async def _download_thumbnail(url: str, work_dir: Path) -> Path | None:
    dest = work_dir / "cover.jpg"

    def _fetch() -> None:
        with urllib.request.urlopen(url) as response:
            dest.write_bytes(response.read())

    try:
        await asyncio.to_thread(_fetch)
    except Exception:
        _log.warning("Thumbnail download failed for %s", url)
        return None
    return dest


async def _write_id3(audio_path: Path, metadata: dict[str, Any], thumb_path: Path | None) -> None:
    _log.debug("Writing ID3 tags for %s", audio_path.name)
    audio = MP3(audio_path, ID3=ID3)
    try:
        audio.add_tags()  # type: ignore[no-untyped-call]
    except (ID3Error, ID3NoHeaderError):
        pass
    if audio.tags is None:
        audio.tags = ID3()  # type: ignore[no-untyped-call]

    title = metadata.get("title") or "Unknown Title"
    artist = metadata.get("artist") or "Unknown Artist"
    album = metadata.get("album") or ""

    audio.tags["TIT2"] = TIT2(encoding=3, text=title)  # type: ignore[no-untyped-call]
    audio.tags["TPE1"] = TPE1(encoding=3, text=artist)  # type: ignore[no-untyped-call]
    audio.tags["TALB"] = TALB(encoding=3, text=album)  # type: ignore[no-untyped-call]

    if thumb_path and thumb_path.exists():
        audio.tags.add(
            APIC(  # type: ignore[no-untyped-call]
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=thumb_path.read_bytes(),
            )
        )
    audio.save(v2_version=3)
