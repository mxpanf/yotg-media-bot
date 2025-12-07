import asyncio
from pathlib import Path

import pytest

from app.services.postprocess import convert_and_tag, shrink_video


def test_shrink_video_skips_if_under_limit(tmp_path: Path) -> None:
    source = tmp_path / "video.mp4"
    source.write_bytes(b"x" * 1024)  # small file
    result = asyncio.run(shrink_video(source, tmp_path, size_limit=10_000))
    assert result == source


def test_shrink_video_returns_source_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "video.mp4"
    source.write_bytes(b"x" * 1024 * 1024)

    async def fake_proc(*args, **kwargs):
        class P:
            returncode = 1

            async def communicate(self):
                return (b"", b"err")

        return P()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_proc)
    result = asyncio.run(shrink_video(source, tmp_path, size_limit=1))
    assert result == source  # fallback to original on failure


def test_convert_and_tag_saves_mp3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Create a fake source file
    source = tmp_path / "track.wav"
    source.write_bytes(b"fake")
    metadata = {"title": "t", "artist": "a", "album": "al"}

    class FakeProc:
        returncode = 0

        async def communicate(self):
            # create fake output file
            output = tmp_path / "track.mp3"
            output.write_bytes(b"mp3")
            return (b"", b"")

    async def fake_proc(*args, **kwargs):
        return FakeProc()

    async def fake_download_thumb(url, work_dir):
        return None

    async def fake_write_id3(audio_path, metadata, thumb):
        return None

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_proc)
    monkeypatch.setattr("app.services.postprocess._download_thumbnail", fake_download_thumb)
    monkeypatch.setattr("app.services.postprocess._write_id3", fake_write_id3)

    result = asyncio.run(convert_and_tag(source, metadata, tmp_path, thumbnail_url=None))
    assert result.audio_path.exists()
    assert result.audio_path.suffix == ".mp3"
