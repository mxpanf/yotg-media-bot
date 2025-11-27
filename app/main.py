#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry point for the bot.
"""

from __future__ import annotations

import asyncio

from aiogram import Dispatcher

from app.bot import create_bot, create_dispatcher, setup_logging
from app.config import AppConfig
from app.i18n import I18n, load_translations


async def main() -> None:
    setup_logging()
    config = AppConfig()
    i18n = I18n(load_translations(), default_locale=config.locale_default)
    bot = create_bot(config, i18n)
    dispatcher: Dispatcher = create_dispatcher(i18n)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
