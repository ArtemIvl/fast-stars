import logging
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, Update

logger = logging.getLogger("bot.timing")


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        start = time.monotonic()

        handler_name = handler.__name__
        event_type = type(event).__name__

        # Детали действия
        if isinstance(event, Message):
            details = f"Message(text={event.text})"
        elif isinstance(event, CallbackQuery):
            details = f"CallbackQuery(data={event.data})"
        else:
            details = "Unknown event"

        result = await handler(event, data)

        duration = (time.monotonic() - start) * 1000  # ms
        logger.info(f"{event_type} by {handler_name} ({details}) in {duration:.1f} ms")

        return result
