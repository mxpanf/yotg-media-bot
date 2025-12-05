#!/usr/bin/env python3

"""
Entry point for the bot.
"""

from __future__ import annotations

import asyncio

from aiogram import Dispatcher

from app.bot import create_bot, create_dispatcher, setup_bot_commands, setup_logging
from app.config import AppConfig
from app.i18n import I18n, load_translations
from app.plugins import YoutubeMusicPlugin, YoutubeVideoPlugin
from app.services.access import AccessControl
from app.services.parser import Platform
from app.services.preferences import UserPreferences
from app.services.storage import Storage


async def main() -> None:
    setup_logging()
    config = AppConfig()  # type: ignore[call-arg]
    i18n = I18n(load_translations(), default_locale=config.locale_default)
    storage = Storage(config.tmp_dir)
    storage.ensure()
    config.data_dir.mkdir(parents=True, exist_ok=True)
    preferences = UserPreferences(config.data_dir / "preferences.json", i18n.default_locale)
    access_control = AccessControl(config.data_dir / "access.json", config.root_admin_id)
    plugins = {
        Platform.YOUTUBE_MUSIC: YoutubeMusicPlugin(),
        Platform.YOUTUBE: YoutubeVideoPlugin(),
    }
    bot = create_bot(config)
    await setup_bot_commands(bot)
    dispatcher: Dispatcher = create_dispatcher(
        config=config,
        i18n=i18n,
        storage=storage,
        plugins=plugins,
        preferences=preferences,
        access_control=access_control,
    )
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
