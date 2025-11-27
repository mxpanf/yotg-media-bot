#!/usr/bin/env python3

"""
Entry point for the bot.
"""

from __future__ import annotations

import asyncio

from aiogram import Dispatcher

from app.bot import create_bot, create_dispatcher, setup_logging
from app.config import AppConfig
from app.i18n import I18n, load_translations
from app.plugins import YoutubeMusicPlugin
from app.services.parser import Platform
from app.services.storage import Storage


async def main() -> None:
    setup_logging()
    config = AppConfig()
    i18n = I18n(load_translations(), default_locale=config.locale_default)
    storage = Storage(config.tmp_dir)
    storage.ensure()
    plugins = {
        Platform.YOUTUBE_MUSIC: YoutubeMusicPlugin(),
    }
    bot = create_bot(config)
    dispatcher: Dispatcher = create_dispatcher(
        config=config,
        i18n=i18n,
        storage=storage,
        plugins=plugins,
    )
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
