"""Utility for sending periodic chat actions instead of manual status messages."""

from __future__ import annotations

import asyncio

from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message


class StatusNotifier:
    """Continuously emits chat actions (typing/uploading) until completion."""

    def __init__(self, origin: Message):
        self._origin = origin
        self._action_task: asyncio.Task[None] | None = None
        self._current_action: ChatAction = ChatAction.TYPING

    async def push(
        self,
        key: str | None = None,
        *,
        action: ChatAction = ChatAction.TYPING,
        **kwargs: object,
    ) -> None:
        await self._ensure_action(action)

    async def delete(self) -> None:
        await self._stop_action()

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
