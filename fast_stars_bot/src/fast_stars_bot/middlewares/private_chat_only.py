from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message


class PrivateChatOnlyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        chat = event.chat if isinstance(event, Message) else event.message.chat

        if chat.type != "private":
            try:
                await event.answer("Бот доступен только в личных сообщениях ❌")
            except TelegramBadRequest:
                pass
            return

        return await handler(event, data)
