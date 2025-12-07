import asyncio
from pathlib import Path
from typing import Any

from aiogram.exceptions import TelegramAPIError

from app.handlers.private import (
    handle_deop,
    handle_forward_access,
    handle_link,
    handle_op,
    handle_remove,
)
from app.i18n import I18n, load_translations
from app.services.access import AccessControl
from app.services.downloader import DownloadResult
from app.services.parser_types import MediaKind, Platform
from app.services.preferences import UserPreferences


class FakeUser:
    def __init__(self, user_id: int, language_code: str | None = "en") -> None:
        self.id = user_id
        self.language_code = language_code


class FakeBot:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, Any]] = []
        self.chat_actions: list[dict[str, Any]] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.sent_messages.append({"chat_id": chat_id, "text": text})

    async def send_chat_action(self, chat_id: int, action: Any) -> None:
        self.chat_actions.append({"chat_id": chat_id, "action": action})


class FakeMessage:
    def __init__(
        self,
        text: str | None,
        from_user: FakeUser,
        bot: FakeBot,
        forward_from: FakeUser | None = None,
        raise_on_video: bool = False,
    ) -> None:
        self.text = text
        self.from_user = from_user
        self.forward_from = forward_from
        self.bot = bot
        self.responses: list[dict[str, Any]] = []
        self.raise_on_video = raise_on_video

    async def answer(self, text: str, **kwargs: Any) -> None:
        self.responses.append({"text": text, **kwargs})

    async def answer_audio(self, **kwargs: Any) -> None:
        self.responses.append({"audio": kwargs})

    async def answer_video(self, **kwargs: Any) -> None:
        if self.raise_on_video:
            raise TelegramAPIError(method="sendVideo", message="too large")
        self.responses.append({"video": kwargs})


class StubVideoPlugin:
    def __init__(self, download_path: Path) -> None:
        self.download_path = download_path

    async def fetch(self, url: str, target_dir: Path) -> DownloadResult:
        return DownloadResult(
            source_url=url,
            platform=Platform.YOUTUBE,
            kind=MediaKind.VIDEO,
            original_path=self.download_path,
            metadata={"title": "Video", "duration": 10, "width": 640, "height": 360},
        )


class DummyStorage:
    def __init__(self, base: Path) -> None:
        self.base = base

    def job_scope(self, prefix: str = "job"):
        class _Ctx:
            def __init__(self, path: Path) -> None:
                self.path = path

            def __enter__(self) -> Path:
                self.path.mkdir(parents=True, exist_ok=True)
                return self.path

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        return _Ctx(self.base / f"{prefix}_test")


def build_context(tmp_path: Path) -> dict[str, Any]:
    i18n = I18n(load_translations(), default_locale="en")
    preferences = UserPreferences(tmp_path / "prefs.json", "en")
    access = AccessControl(tmp_path / "access.json", root_admin_id=1)
    return {"i18n": i18n, "preferences": preferences, "access": access}


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_forward_grants_access(tmp_path: Path) -> None:
    ctx = build_context(tmp_path)
    bot = FakeBot()
    admin = FakeUser(1, "en")
    target = FakeUser(99, "ru")
    message = FakeMessage(text=None, from_user=admin, forward_from=target, bot=bot)

    run(
        handle_forward_access(
            message=message,
            i18n=ctx["i18n"],
            preferences=ctx["preferences"],
            access_control=ctx["access"],
        )
    )

    assert ctx["access"].is_allowed(99)
    assert bot.sent_messages and bot.sent_messages[0]["chat_id"] == 99
    assert message.responses  # admin got feedback


def test_op_promotes_and_grants_access(tmp_path: Path) -> None:
    ctx = build_context(tmp_path)
    bot = FakeBot()
    root = FakeUser(1, "en")
    message = FakeMessage(text="/op 55", from_user=root, bot=bot)

    run(
        handle_op(
            message=message,
            i18n=ctx["i18n"],
            preferences=ctx["preferences"],
            access_control=ctx["access"],
        )
    )

    assert ctx["access"].is_admin(55)
    assert ctx["access"].is_allowed(55)


def test_deop_removes_admin_but_keeps_access(tmp_path: Path) -> None:
    ctx = build_context(tmp_path)
    bot = FakeBot()
    root = FakeUser(1, "en")
    ctx["access"].promote(77)
    message = FakeMessage(text="/deop 77", from_user=root, bot=bot)

    run(
        handle_deop(
            message=message,
            i18n=ctx["i18n"],
            preferences=ctx["preferences"],
            access_control=ctx["access"],
        )
    )

    assert not ctx["access"].is_admin(77)
    assert ctx["access"].is_allowed(77)


def test_remove_strips_access_and_admin(tmp_path: Path) -> None:
    ctx = build_context(tmp_path)
    bot = FakeBot()
    admin = FakeUser(2, "en")
    ctx["access"].promote(admin.id)
    ctx["access"].promote(88)  # make admin to later remove
    ctx["access"].add_user(88)
    message = FakeMessage(text="/remove 88", from_user=admin, bot=bot)

    run(
        handle_remove(
            message=message,
            i18n=ctx["i18n"],
            preferences=ctx["preferences"],
            access_control=ctx["access"],
        )
    )

    assert not ctx["access"].is_allowed(88)
    assert not ctx["access"].is_admin(88)


def test_handle_link_too_large_video_reports_error(tmp_path: Path) -> None:
    ctx = build_context(tmp_path)
    ctx["access"].add_user(5)
    bot = FakeBot()
    user = FakeUser(5, "en")
    video_file = tmp_path / "vid.mp4"
    video_file.write_bytes(b"X" * 100)
    plugins = {Platform.YOUTUBE: StubVideoPlugin(video_file)}
    message = FakeMessage(
        text="https://www.youtube.com/watch?v=vid",
        from_user=user,
        bot=bot,
        raise_on_video=True,
    )

    run(
        handle_link(
            message=message,
            i18n=ctx["i18n"],
            storage=DummyStorage(tmp_path),
            plugins=plugins,
            preferences=ctx["preferences"],
            access_control=ctx["access"],
        )
    )

    assert any("too large" in resp.get("text", "").lower() for resp in message.responses)


def test_handle_link_unsupported_platform(tmp_path: Path) -> None:
    ctx = build_context(tmp_path)
    ctx["access"].add_user(5)
    bot = FakeBot()
    user = FakeUser(5, "en")
    message = FakeMessage(text="https://example.com/foo", from_user=user, bot=bot)

    run(
        handle_link(
            message=message,
            i18n=ctx["i18n"],
            storage=DummyStorage(tmp_path),
            plugins={},
            preferences=ctx["preferences"],
            access_control=ctx["access"],
        )
    )

    assert any(
        "Link is not supported".lower() in resp.get("text", "").lower()
        for resp in message.responses
    )


def test_handle_link_missing_plugin(tmp_path: Path) -> None:
    ctx = build_context(tmp_path)
    ctx["access"].add_user(5)
    bot = FakeBot()
    user = FakeUser(5, "en")
    message = FakeMessage(text="https://www.youtube.com/watch?v=vid", from_user=user, bot=bot)

    run(
        handle_link(
            message=message,
            i18n=ctx["i18n"],
            storage=DummyStorage(tmp_path),
            plugins={},  # no plugin for YOUTUBE
            preferences=ctx["preferences"],
            access_control=ctx["access"],
        )
    )

    assert any(
        "Link is not supported".lower() in resp.get("text", "").lower()
        for resp in message.responses
    )
