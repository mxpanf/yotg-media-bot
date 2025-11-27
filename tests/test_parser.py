"""
Parser tests for URL detection.
"""

import pytest

from app.services.parser import MediaKind, Platform, parse_url

VALID_MUSIC_TRACKS = [
    "https://music.youtube.com/watch?v=2TP6tKYUuhk",
    "https://music.youtube.com/watch?v=b33JQptLmxs&list=RDAMVM2TP6tKYUuhk",
    "https://music.youtube.com/watch?v=7SElSZNVFLU",
    "https://music.youtube.com/watch?v=7SElSZNVFLU&si=5tjR4W6gvMZjVm7O&t=11",
    "https://music.youtube.com/watch?v=_fW2rw8SwoA&si=dng6gtprnXeZIKTV",
    "music.youtube.com/watch?v=2TP6tKYUuhk",
]

VALID_MUSIC_PLAYLISTS = [
    "https://music.youtube.com/playlist?list=PLxxxxxxxx",
]

VALID_YOUTUBE_TRACKS = [
    "https://www.youtube.com/watch?v=_fW2rw8SwoA",
    "https://youtu.be/_fW2rw8SwoA",
    "www.youtube.com/watch?v=_fW2rw8SwoA&list=OLAK5uy_kpQQ2Zbr6XNbWjaXvAUu-9nHzTTQJeczo",
    "m.youtube.com/watch?v=_fW2rw8SwoA&t=10s",
]

VALID_YOUTUBE_PLAYLISTS = [
    "https://www.youtube.com/playlist?list=PL123456789",
    "youtube.com/playlist?list=PLzzzzzzzz",
]

INVALID_URLS = [
    "https://example.com/not-supported",
    "https://music.youtube.com/watch?",  # no video id
    "youtu.be/",  # missing id
    " ",  # blank
    "spotify.com/track/123",  # other service
]


@pytest.mark.parametrize("url", VALID_MUSIC_TRACKS)
def test_parse_youtube_music_track(url: str) -> None:
    parsed = parse_url(url)
    assert parsed.platform is Platform.YOUTUBE_MUSIC
    assert parsed.kind is MediaKind.TRACK
    assert parsed.video_id
    assert parsed.canonical_url.startswith("https://music.youtube.com/watch?v=")


@pytest.mark.parametrize("url", VALID_MUSIC_PLAYLISTS)
def test_parse_youtube_music_playlist(url: str) -> None:
    parsed = parse_url(url)
    assert parsed.platform is Platform.YOUTUBE_MUSIC
    assert parsed.kind is MediaKind.PLAYLIST
    assert parsed.playlist_id
    assert parsed.canonical_url.startswith("https://music.youtube.com/playlist?list=")


@pytest.mark.parametrize("url", VALID_YOUTUBE_TRACKS)
def test_parse_youtube_track(url: str) -> None:
    parsed = parse_url(url)
    assert parsed.platform is Platform.YOUTUBE
    assert parsed.kind is MediaKind.TRACK
    assert parsed.video_id
    assert parsed.canonical_url.startswith("https://www.youtube.com/watch?v=")


@pytest.mark.parametrize("url", VALID_YOUTUBE_PLAYLISTS)
def test_parse_youtube_playlist(url: str) -> None:
    parsed = parse_url(url)
    assert parsed.platform is Platform.YOUTUBE
    assert parsed.kind is MediaKind.PLAYLIST
    assert parsed.playlist_id
    assert parsed.canonical_url.startswith("https://www.youtube.com/playlist?list=")


@pytest.mark.parametrize("url", INVALID_URLS)
def test_parse_unknown(url: str) -> None:
    parsed = parse_url(url)
    assert parsed.platform is Platform.UNKNOWN
    assert parsed.kind is MediaKind.UNKNOWN
