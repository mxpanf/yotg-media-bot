# -*- coding: utf-8 -*-
"""
Handlers for private chats.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.i18n import I18n
from app.services.parser import Platform, detect_platform

private_router = Router(name="private")


def get_user_locale(message: Message, fallback: str = "ru") -> str:
    return (message.from_user and message.from_user.language_code) or fallback


@private_router.message(Command("start", "help"))
async def handle_start(message: Message, i18n: I18n) -> None:
    locale = get_user_locale(message, i18n.default_locale)
    await message.answer(i18n.gettext("start.greeting", locale=locale))


@private_router.message(F.text)
async def handle_link(message: Message, i18n: I18n) -> None:
    locale = get_user_locale(message, i18n.default_locale)
    text = message.text or ""
    platform = detect_platform(text)
    if platform == Platform.UNKNOWN:
        await message.answer(i18n.gettext("error.unsupported", locale=locale))
        return
    await message.answer(
        i18n.gettext("status.type_detected", locale=locale, kind=platform.value)
    )
    # TODO: Implement pipeline: download, post-process, upload.
