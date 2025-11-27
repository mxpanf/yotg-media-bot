"""
Handlers for private chats.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message

from app.i18n import I18n
from app.services.downloader import Downloader
from app.services.parser import Platform, parse_url
from app.services.postprocess import convert_and_tag
from app.services.status_notifier import StatusNotifier
from app.services.storage import Storage

private_router = Router(name="private")
log = logging.getLogger(__name__)


def get_user_locale(message: Message, fallback: str = "ru") -> str:
    return (message.from_user and message.from_user.language_code) or fallback


@private_router.message(Command("start", "help"))
async def handle_start(message: Message, i18n: I18n) -> None:
    locale = get_user_locale(message, i18n.default_locale)
    await message.answer(i18n.gettext("start.greeting", locale=locale))


@private_router.message(F.text)
async def handle_link(
    message: Message,
    i18n: I18n,
    storage: Storage,
    plugins: Mapping[Platform, Downloader],
) -> None:
    locale = get_user_locale(message, i18n.default_locale)
    text = message.text or ""
    log.info(
        "Handling link from user=%s text=%s",
        message.from_user.id if message.from_user else "unknown",
        text,
    )
    notifier = StatusNotifier(message, i18n, locale)
    await notifier.push("status.processing")
    parsed = parse_url(text)
    platform = parsed.platform
    if platform == Platform.UNKNOWN:
        await notifier.delete()
        await message.answer(i18n.gettext("error.unsupported", locale=locale))
        return
    await notifier.push(
        "status.type_detected",
        kind=platform.value,
    )
    plugin = plugins.get(platform)
    if not plugin:
        await notifier.delete()
        await message.answer(i18n.gettext("error.unsupported", locale=locale))
        return

    try:
        with storage.job_scope("ytm") as job_dir:
            log.debug("Starting download for %s (%s)", parsed.canonical_url, platform)
            await notifier.push("status.downloading")
            download = await plugin.fetch(parsed.canonical_url, job_dir)

            await notifier.push("status.converting")
            log.debug("Converting %s", download.original_path.name)
            processed = await convert_and_tag(
                source=download.original_path,
                metadata=download.metadata,
                work_dir=job_dir,
                thumbnail_url=download.thumbnail_url,
            )

            await notifier.push("status.metadata")
            caption = build_caption(download.metadata)

            await notifier.push("status.uploading", action=ChatAction.UPLOAD_DOCUMENT)
            log.info("Uploading audio for %s", download.metadata.get("title"))
            await message.answer_audio(
                audio=FSInputFile(processed.audio_path),
                caption=caption,
                performer=download.metadata.get("artist"),
                title=download.metadata.get("title"),
                thumbnail=(FSInputFile(processed.thumb_path) if processed.thumb_path else None),
            )
    except Exception as exc:
        log.exception("Failed to process link: %s", exc)
        await message.answer(i18n.gettext("error.generic", locale=locale))
        raise
    finally:
        await notifier.delete()


def build_caption(metadata: Mapping[str, Any]) -> str:
    title = metadata.get("title") or ""
    artist = metadata.get("artist") or ""
    album = metadata.get("album") or ""
    parts = [value for value in (title, artist, album) if value]
    return " • ".join(parts) or "Audio"
