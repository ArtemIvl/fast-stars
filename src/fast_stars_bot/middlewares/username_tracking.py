from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from db.session import SessionLocal
from utils.user_requests import get_user_by_telegram_id, update_user_username


class UserTrackingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        telegram_id = event.from_user.id
        current_username = event.from_user.username

        if not current_username:
            text = "❗У вас не установлен username в Telegram. Установите его в настройках чтобы продолжать пользоваться нашим ботом."
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            else:
                await event.answer(text)
            return

        async with SessionLocal() as session:
            user = await get_user_by_telegram_id(session, telegram_id)
            if user and user.username != current_username:
                await update_user_username(session, user, current_username)

        return await handler(event, data)
