import asyncio
from pathlib import Path

import pytest

from app.plugins.youtube_music import YoutubeMusicPlugin
from app.services.parser_types import MediaKind, Platform


def test_sanitize_title_removes_noise() -> None:
    plugin = YoutubeMusicPlugin()
    cleaned = plugin._sanitize_title("My Song (Official Video) [1080p]")
    assert cleaned == "My Song"


def test_fetch_returns_track_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plugin = YoutubeMusicPlugin()

    fake_info = {
        "id": "ytm123",
        "title": "Test Title",
        "artists": ["Artist1", "Artist2"],
        "album": "Test Album",
        "duration": 123,
        "thumbnail": "http://example.com/thumb.jpg",
    }
    fake_file = tmp_path / "ytm123.webm"
    fake_file.write_text("content")

    async def fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    def fake_download(url: str, target_dir: Path):
        assert url == "https://music.youtube.com/watch?v=ytm123"
        assert target_dir == tmp_path
        return fake_info, fake_file

    async def fake_enrich(metadata):
        return metadata

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(plugin, "_download", fake_download)
    monkeypatch.setattr(plugin, "_enrich_metadata", fake_enrich)

    async def _run() -> None:
        nonlocal result
        result = await plugin.fetch("https://music.youtube.com/watch?v=ytm123", tmp_path)

    result: object | None = None
    asyncio.run(_run())

    assert result is not None
    assert result.platform is Platform.YOUTUBE_MUSIC
    assert result.kind is MediaKind.TRACK
    assert result.metadata["title"] == "Test Title"
    assert result.metadata["artist"] == "Artist1, Artist2"
    assert result.original_path == fake_file
