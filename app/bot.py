# -*- coding: utf-8 -*-
"""
Bot and dispatcher factory.
"""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import AppConfig
from app.handlers import private_router
from app.i18n import I18n, load_translations


def create_bot(config: AppConfig, i18n: I18n) -> Bot:
    return Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(i18n: I18n) -> Dispatcher:
    dp = Dispatcher()
    dp.workflow_data.update({"i18n": i18n})
    dp.include_router(private_router)
    return dp


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO)
