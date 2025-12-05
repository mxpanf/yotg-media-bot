import asyncio
from pathlib import Path

import pytest

from app.plugins.youtube_video import YoutubeVideoPlugin
from app.services.parser_types import MediaKind, Platform


def test_format_selector_respects_max_height() -> None:
    plugin = YoutubeVideoPlugin(max_height=720)
    fmt = plugin._format_selector()
    assert "height<=720" in fmt
    assert "best[height<=720]" in fmt


def test_fetch_returns_video_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plugin = YoutubeVideoPlugin()

    fake_info = {
        "id": "abc123",
        "title": "Test Video",
        "uploader": "Tester",
        "duration": 42,
        "width": 1920,
        "height": 1080,
        "thumbnail": "http://example.com/thumb.jpg",
    }
    fake_file = tmp_path / "abc123.mkv"
    fake_file.write_text("content")

    async def fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    def fake_download(url: str, target_dir: Path):
        assert url == "https://www.youtube.com/watch?v=abc123"
        assert target_dir == tmp_path
        return fake_info, fake_file.with_suffix(".mp4")

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(plugin, "_download", fake_download)

    async def _run() -> None:
        nonlocal result
        result = await plugin.fetch("https://www.youtube.com/watch?v=abc123", tmp_path)

    result: object | None = None
    asyncio.run(_run())

    assert result is not None
    assert result.platform is Platform.YOUTUBE
    assert result.kind is MediaKind.VIDEO
    assert result.original_path.suffix == ".mp4"
    assert result.metadata["title"] == fake_info["title"]
    assert result.metadata["height"] == fake_info["height"]
