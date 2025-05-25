from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from typing import Awaitable, Callable, Dict, Any
from db.session import SessionLocal
from utils.user_requests import get_user_by_telegram_id

class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        telegram_id = event.from_user.id

        async with SessionLocal() as session:
            user = await get_user_by_telegram_id(session, telegram_id)

            if user and user.is_banned:
                text = "❗Вы заблокированы администратором. Обратитесь к администратору для получения дополнительной информации."
                if isinstance(event, CallbackQuery):
                    await event.answer(text, show_alert=True)
                else:
                    await event.answer(text)
                return

        return await handler(event, data)