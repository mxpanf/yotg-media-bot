"""
Utility for maintaining status message updates with persistent chat actions.
"""

from __future__ import annotations

import asyncio

from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

from app.i18n import I18n


class StatusNotifier:
    """
    Keeps a single status message updated while continuously sending chat actions
    (typing/uploading) until the next status or completion.
    """

    def __init__(self, origin: Message, i18n: I18n, locale: str):
        self._origin = origin
        self._i18n = i18n
        self._locale = locale
        self._message: Message | None = None
        self._current_text: str = ""
        self._action_task: asyncio.Task[None] | None = None
        self._current_action: ChatAction = ChatAction.TYPING

    async def push(
        self,
        key: str,
        *,
        action: ChatAction = ChatAction.TYPING,
        **kwargs: object,
    ) -> None:
        await self._ensure_action(action)
        text = self._i18n.gettext(key, locale=self._locale, **kwargs)
        self._current_text = text
        if self._message is None:
            self._message = await self._origin.answer(text)
        else:
            await self._safe_edit(text)

    async def delete(self) -> None:
        await self._stop_action()
        if self._message:
            try:
                await self._message.delete()
            except TelegramAPIError:
                pass
            self._message = None

    async def _ensure_action(self, action: ChatAction) -> None:
        if self._action_task and action == self._current_action:
            return
        await self._stop_action()
        self._current_action = action
        self._action_task = asyncio.create_task(self._action_loop(action))

    async def _stop_action(self) -> None:
        if self._action_task:
            self._action_task.cancel()
            try:
                await self._action_task
            except asyncio.CancelledError:
                pass
            self._action_task = None

    async def _action_loop(self, action: ChatAction) -> None:
        try:
            while True:
                await self._send_action(action)
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            return

    async def _send_action(self, action: ChatAction) -> None:
        bot = self._origin.bot
        if bot is None:
            return
        try:
            await bot.send_chat_action(
                chat_id=self._origin.chat.id,
                action=action,
            )
        except TelegramAPIError:
            pass

    async def _safe_edit(self, text: str) -> None:
        if not self._message:
            return
        try:
            if self._message.text != text:
                await self._message.edit_text(text)
        except TelegramAPIError:
            pass
