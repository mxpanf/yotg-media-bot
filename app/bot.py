"""
Bot and dispatcher factory.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from app.config import AppConfig
from app.handlers import private_router
from app.i18n import I18n
from app.services.access import AccessControl
from app.services.downloader import Downloader
from app.services.parser import Platform
from app.services.preferences import UserPreferences
from app.services.storage import Storage


def create_bot(config: AppConfig) -> Bot:
    return Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(
    *,
    config: AppConfig,
    i18n: I18n,
    storage: Storage,
    plugins: Mapping[Platform, Downloader],
    preferences: UserPreferences,
    access_control: AccessControl,
) -> Dispatcher:
    dp = Dispatcher()
    dp.workflow_data.update(
        {
            "config": config,
            "i18n": i18n,
            "storage": storage,
            "plugins": plugins,
            "preferences": preferences,
            "access_control": access_control,
        }
    )
    dp.include_router(private_router)
    return dp


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


async def setup_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Restart bot and reset language"),
        BotCommand(command="help", description="Usage instructions"),
        BotCommand(command="settings", description="Language settings"),
    ]
    await bot.set_my_commands(commands)
