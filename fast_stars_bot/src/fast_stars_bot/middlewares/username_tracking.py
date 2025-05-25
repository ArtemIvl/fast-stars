from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from db.session import SessionLocal
from utils.user_requests import get_user_by_telegram_id

class UserTrackingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        from_user = event.from_user
        if not from_user:
            return await handler(event, data)

        async with SessionLocal() as session:
            user = await get_user_by_telegram_id(session, from_user.id)
            if user:
                if user.username != from_user.username:
                    user.username = from_user.username
                    await session.commit()

        return await handler(event, data)