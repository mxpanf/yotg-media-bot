"""
Handlers for private chats.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.i18n import I18n
from app.services.access import AccessControl
from app.services.downloader import Downloader
from app.services.parser import MediaKind, Platform, parse_url
from app.services.postprocess import convert_and_tag, shrink_video
from app.services.preferences import UserPreferences
from app.services.status_notifier import StatusNotifier
from app.services.storage import Storage

private_router = Router(name="private")
log = logging.getLogger(__name__)

LOCALE_CALLBACK_PREFIX = "locale:"
TELEGRAM_MAX_UPLOAD_BYTES = 48_000_000  # Bot API upload limit is 50MB; keep margin


def _normalize_locale(locale: str | None) -> str | None:
    if not locale:
        return None
    candidate = locale.split("-")[0].lower().strip()
    return candidate or None


def _preferred_locale(message: Message, i18n: I18n) -> str:
    user_locale = _normalize_locale(message.from_user.language_code if message.from_user else None)
    if user_locale and user_locale in i18n.available_locales:
        return user_locale
    return i18n.default_locale


def ensure_user_locale(message: Message, i18n: I18n, preferences: UserPreferences) -> str:
    fallback = _preferred_locale(message, i18n)
    user_id = message.from_user.id if message.from_user else None
    if user_id is None:
        return fallback
    stored = preferences.get_locale(user_id)
    if stored and stored in i18n.available_locales:
        return stored
    return preferences.ensure_locale(user_id, fallback)


def _user_id(message: Message) -> int | None:
    return message.from_user.id if message.from_user else None


def _has_access(message: Message, access_control: AccessControl) -> bool:
    return access_control.is_allowed(_user_id(message))


def _is_admin(message: Message, access_control: AccessControl) -> bool:
    return access_control.is_admin(_user_id(message))


@private_router.message(F.forward_from)
async def handle_forward_access(
    message: Message,
    i18n: I18n,
    preferences: UserPreferences,
    access_control: AccessControl,
) -> None:
    user = message.from_user
    forwarded = message.forward_from
    if not user or not forwarded:
        return
    if not access_control.is_admin(user.id):
        return
    locale = ensure_user_locale(message, i18n, preferences)
    target_id = forwarded.id
    if access_control.is_allowed(target_id):
        await message.answer(i18n.gettext("admin.access_exists", locale=locale, user_id=target_id))
        return
    added = access_control.add_user(target_id)
    if not added and not access_control.is_allowed(target_id):
        await message.answer(i18n.gettext("admin.error_generic", locale=locale))
        return
    await message.answer(
        i18n.gettext("admin.access_granted_admin", locale=locale, user_id=target_id)
    )
    forward_locale = _normalize_locale(getattr(forwarded, "language_code", None))
    await _notify_access_granted(
        bot=message.bot,
        user_id=target_id,
        i18n=i18n,
        preferences=preferences,
        locale_hint=forward_locale or i18n.default_locale,
    )


@private_router.message(Command("start"))
async def handle_start(
    message: Message,
    i18n: I18n,
    preferences: UserPreferences,
    access_control: AccessControl,
) -> None:
    if not _has_access(message, access_control):
        return
    locale = ensure_user_locale(message, i18n, preferences)
    await message.answer(i18n.gettext("start.greeting", locale=locale))


@private_router.message(Command("help"))
async def handle_help(
    message: Message,
    i18n: I18n,
    preferences: UserPreferences,
    access_control: AccessControl,
) -> None:
    if not _has_access(message, access_control):
        return
    locale = ensure_user_locale(message, i18n, preferences)
    text = i18n.gettext("help.body", locale=locale)
    user_id = _user_id(message)
    if user_id and access_control.is_admin(user_id):
        text = f"{text}\n\n{i18n.gettext('help.admin', locale=locale)}"
    await message.answer(text)


@private_router.message(Command("settings"))
async def handle_settings(
    message: Message,
    i18n: I18n,
    preferences: UserPreferences,
    access_control: AccessControl,
) -> None:
    if not _has_access(message, access_control):
        return
    locale = ensure_user_locale(message, i18n, preferences)
    current_label = i18n.gettext(f"settings.locale.{locale}", locale=locale)
    text = i18n.gettext("settings.prompt", locale=locale, locale_label=current_label)
    keyboard = build_locale_keyboard(i18n, locale, locale)
    await message.answer(text, reply_markup=keyboard)


@private_router.message(Command("add"))
async def handle_add(
    message: Message,
    i18n: I18n,
    preferences: UserPreferences,
    access_control: AccessControl,
) -> None:
    if not _is_admin(message, access_control):
        locale = ensure_user_locale(message, i18n, preferences)
        await message.answer(i18n.gettext("admin.only_admin", locale=locale))
        return
    locale = ensure_user_locale(message, i18n, preferences)
    target_id = _parse_user_id_arg(message)
    if target_id is None:
        await message.answer(i18n.gettext("admin.missing_id", locale=locale))
        return
    if access_control.is_allowed(target_id):
        await message.answer(i18n.gettext("admin.access_exists", locale=locale, user_id=target_id))
        return
    added = access_control.add_user(target_id)
    if not added and not access_control.is_allowed(target_id):
        await message.answer(i18n.gettext("admin.error_generic", locale=locale))
        return
    await message.answer(
        i18n.gettext("admin.access_granted_admin", locale=locale, user_id=target_id)
    )
    await _notify_access_granted(
        bot=message.bot,
        user_id=target_id,
        i18n=i18n,
        preferences=preferences,
        locale_hint=i18n.default_locale,
    )


@private_router.message(Command("remove"))
async def handle_remove(
    message: Message,
    i18n: I18n,
    preferences: UserPreferences,
    access_control: AccessControl,
) -> None:
    if not _is_admin(message, access_control):
        locale = ensure_user_locale(message, i18n, preferences)
        await message.answer(i18n.gettext("admin.only_admin", locale=locale))
        return
    locale = ensure_user_locale(message, i18n, preferences)
    target_id = _parse_user_id_arg(message)
    if target_id is None:
        await message.answer(i18n.gettext("admin.missing_id", locale=locale))
        return
    if access_control.is_root(target_id):
        await message.answer(i18n.gettext("admin.cannot_root", locale=locale))
        return
    removed = access_control.remove_user(target_id)
    if not removed:
        await message.answer(i18n.gettext("admin.not_found", locale=locale, user_id=target_id))
        return
    await message.answer(i18n.gettext("admin.removed", locale=locale, user_id=target_id))


@private_router.message(Command("op"))
async def handle_op(
    message: Message,
    i18n: I18n,
    preferences: UserPreferences,
    access_control: AccessControl,
) -> None:
    user_id = _user_id(message)
    locale = ensure_user_locale(message, i18n, preferences)
    if not access_control.is_root(user_id):
        await message.answer(i18n.gettext("admin.only_root", locale=locale))
        return
    target_id = _parse_user_id_arg(message)
    if target_id is None:
        await message.answer(i18n.gettext("admin.missing_id", locale=locale))
        return
    if access_control.is_root(target_id):
        await message.answer(i18n.gettext("admin.cannot_root", locale=locale))
        return
    if access_control.is_admin(target_id):
        await message.answer(i18n.gettext("admin.already_admin", locale=locale, user_id=target_id))
        return
    promoted = access_control.promote(target_id)
    if not promoted:
        await message.answer(i18n.gettext("admin.error_generic", locale=locale))
        return
    await message.answer(i18n.gettext("admin.promoted", locale=locale, user_id=target_id))
    await _notify_access_granted(
        bot=message.bot,
        user_id=target_id,
        i18n=i18n,
        preferences=preferences,
        locale_hint=i18n.default_locale,
        text_override="admin.promoted_user",
    )


@private_router.message(Command("deop"))
async def handle_deop(
    message: Message,
    i18n: I18n,
    preferences: UserPreferences,
    access_control: AccessControl,
) -> None:
    user_id = _user_id(message)
    locale = ensure_user_locale(message, i18n, preferences)
    if not access_control.is_root(user_id):
        await message.answer(i18n.gettext("admin.only_root", locale=locale))
        return
    target_id = _parse_user_id_arg(message)
    if target_id is None:
        await message.answer(i18n.gettext("admin.missing_id", locale=locale))
        return
    if access_control.is_root(target_id):
        await message.answer(i18n.gettext("admin.cannot_root", locale=locale))
        return
    if not access_control.is_admin(target_id):
        await message.answer(i18n.gettext("admin.not_admin", locale=locale, user_id=target_id))
        return
    demoted = access_control.demote(target_id)
    if not demoted:
        await message.answer(i18n.gettext("admin.error_generic", locale=locale))
        return
    await message.answer(i18n.gettext("admin.demoted", locale=locale, user_id=target_id))


@private_router.message(F.text)
async def handle_link(
    message: Message,
    i18n: I18n,
    storage: Storage,
    plugins: Mapping[Platform, Downloader],
    preferences: UserPreferences,
    access_control: AccessControl,
) -> None:
    if (message.text or "").startswith("/"):
        return
    if not _has_access(message, access_control):
        return
    locale = ensure_user_locale(message, i18n, preferences)
    text = message.text or ""
    log.info(
        "Handling link from user=%s text=%s",
        message.from_user.id if message.from_user else "unknown",
        text,
    )
    notifier = StatusNotifier(message)
    parsed = parse_url(text)
    platform = parsed.platform
    if platform == Platform.UNKNOWN:
        await notifier.delete()
        await message.answer(i18n.gettext("error.unsupported", locale=locale))
        return
    plugin = plugins.get(platform)
    if not plugin:
        await notifier.delete()
        await message.answer(i18n.gettext("error.unsupported", locale=locale))
        return

    upload_action = (
        ChatAction.UPLOAD_VIDEO if platform is Platform.YOUTUBE else ChatAction.UPLOAD_AUDIO
    )
    await notifier.push(action=upload_action)

    try:
        job_prefix = platform.name.lower()
        with storage.job_scope(job_prefix) as job_dir:
            log.debug("Starting download for %s (%s)", parsed.canonical_url, platform)
            download = await plugin.fetch(parsed.canonical_url, job_dir)
            if download.kind is MediaKind.VIDEO:
                caption = build_caption(download.metadata)
                video_path = await shrink_video(
                    download.original_path, job_dir, TELEGRAM_MAX_UPLOAD_BYTES
                )
                await notifier.push(action=ChatAction.UPLOAD_VIDEO)
                log.info("Uploading video for %s", download.metadata.get("title"))
                try:
                    await message.answer_video(
                        video=FSInputFile(video_path),
                        caption=caption,
                        duration=int(download.metadata.get("duration") or 0) or None,
                        width=download.metadata.get("width"),
                        height=download.metadata.get("height"),
                        supports_streaming=True,
                    )
                except TelegramAPIError as exc:
                    log.warning("Video upload failed: %s", exc)
                    await message.answer(
                        i18n.gettext(
                            "error.too_large",
                            locale=locale,
                            limit_mb=int(TELEGRAM_MAX_UPLOAD_BYTES / 1024 / 1024),
                        )
                    )
            else:
                log.debug("Converting %s", download.original_path.name)
                processed = await convert_and_tag(
                    source=download.original_path,
                    metadata=download.metadata,
                    work_dir=job_dir,
                    thumbnail_url=download.thumbnail_url,
                )

                caption = build_caption(download.metadata)

                await notifier.push(action=ChatAction.UPLOAD_AUDIO)
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


@private_router.callback_query(F.data.startswith(LOCALE_CALLBACK_PREFIX))
async def handle_locale_change(
    callback: CallbackQuery,
    i18n: I18n,
    preferences: UserPreferences,
) -> None:
    user = callback.from_user
    if not user or not callback.data:
        await callback.answer(
            i18n.gettext("settings.invalid", locale=i18n.default_locale), show_alert=True
        )
        return
    requested = callback.data.split(":", maxsplit=1)[1]
    if requested not in i18n.available_locales:
        await callback.answer(
            i18n.gettext("settings.invalid", locale=i18n.default_locale), show_alert=True
        )
        return
    current = preferences.get_locale(user.id) or i18n.default_locale
    if current == requested:
        label = i18n.gettext(f"settings.locale.{current}", locale=current)
        await callback.answer(
            i18n.gettext("settings.no_change", locale=current, locale_label=label)
        )
        return
    preferences.set_locale(user.id, requested)
    label = i18n.gettext(f"settings.locale.{requested}", locale=requested)
    text = i18n.gettext("settings.updated", locale=requested, locale_label=label)
    keyboard = build_locale_keyboard(i18n, requested, requested)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer(i18n.gettext("settings.updated_to", locale=requested))


def build_locale_keyboard(
    i18n: I18n,
    locale_for_labels: str,
    active_locale: str,
) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for code in i18n.available_locales:
        label = i18n.gettext(f"settings.locale.{code}", locale=locale_for_labels)
        prefix = "✅ " if code == active_locale else ""
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{prefix}{label}",
                    callback_data=f"{LOCALE_CALLBACK_PREFIX}{code}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_caption(metadata: Mapping[str, Any]) -> str:
    title = metadata.get("title") or ""
    artist = metadata.get("artist") or ""
    album = metadata.get("album") or ""
    parts = [value for value in (title, artist, album) if value]
    return " • ".join(parts) or "Audio"


def _parse_user_id_arg(message: Message) -> int | None:
    text = (message.text or "").strip()
    parts = text.split()
    if len(parts) < 2:
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


async def _notify_access_granted(
    bot: Bot | None,
    user_id: int,
    i18n: I18n,
    preferences: UserPreferences,
    locale_hint: str | None,
    text_override: str | None = None,
) -> None:
    if bot is None:
        return
    locale = preferences.ensure_locale(user_id, locale_hint or i18n.default_locale)
    try:
        await bot.send_message(
            chat_id=user_id,
            text=i18n.gettext(text_override or "admin.access_granted_user", locale=locale),
        )
    except TelegramAPIError:
        pass
