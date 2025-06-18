from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from db.models.cube_game import GameStatus
from db.session import SessionLocal
from utils.cube_requests import get_active_game_by_user
from utils.user_requests import get_user_by_telegram_id

ALLOWED_CALLBACK_PREFIXES = ("throw_cube_", "cube_bet_")


class BlockActionsWhilePlayingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        telegram_id = None
        if isinstance(event, Message):
            telegram_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            telegram_id = event.from_user.id
            if any(
                event.data.startswith(prefix) for prefix in ALLOWED_CALLBACK_PREFIXES
            ):
                return await handler(event, data)

        if not telegram_id:
            return await handler(event, data)

        async with SessionLocal() as session:
            user = await get_user_by_telegram_id(session, telegram_id)
            if not user:
                return await handler(event, data)
            game = await get_active_game_by_user(session, user.id)
            if game:
                if isinstance(event, CallbackQuery):
                    if event.data.startswith("cancel_game_"):
                        if game.status == GameStatus.WAITING:
                            return await handler(event, data)
                        return
                    return
                elif isinstance(event, Message):
                    return

        return await handler(event, data)
