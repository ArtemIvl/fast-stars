import asyncio
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, F, Router, types
from aiogram.types import CallbackQuery, Message
from db.session import SessionLocal
from utils.user_requests import get_user_by_telegram_id

router = Router()


def register_ban_payment_handler(dp) -> None:
    dp.include_router(router)


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
                if isinstance(event, Message) and getattr(
                    event, "successful_payment", None
                ):
                    return await handler(event, data)
                text = "❗Вы были заблокированы. Чтобы вернуть доступ, оплатите 99⭐️ через Telegram Stars."
                chat_id = (
                    event.message.chat.id
                    if isinstance(event, types.CallbackQuery)
                    else event.chat.id
                )

                await event.bot.send_message(chat_id, text)

                invoice_msg = await event.bot.send_invoice(
                    chat_id=chat_id,
                    title="Оплата за разбан",
                    description="Оплата за разблокировку аккаунта",
                    payload=f"unban:{telegram_id}",
                    provider_token="",
                    currency="XTR",
                    prices=[types.LabeledPrice(label="Разблокировка", amount=99)],
                    start_parameter="unban",
                )

                async def delete_invoice_later():
                    await asyncio.sleep(15)
                    try:
                        await event.bot.delete_message(chat_id, invoice_msg.message_id)
                    except Exception:
                        pass

                asyncio.create_task(delete_invoice_later())

                return
        return await handler(event, data)
