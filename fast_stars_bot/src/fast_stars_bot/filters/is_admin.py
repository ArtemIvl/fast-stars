from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from db.session import SessionLocal
from utils.user_requests import get_user_by_telegram_id

class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        telegram_id = event.from_user.id

        async with SessionLocal() as session:
            user = await get_user_by_telegram_id(session, telegram_id)

            return user is not None and user.is_admin