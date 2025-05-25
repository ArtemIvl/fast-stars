from typing import Any, Awaitable, Callable, Dict
import random
from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from db.session import SessionLocal
from utils.channel_requests import get_all_channels
from utils.subscription_requests import is_user_subscribed_to_all
from utils.user_requests import get_user_by_telegram_id
from aiogram.fsm.context import FSMContext

from keyboards.channels_keyboard import channels_keyboard


class SubscriptionRequiredMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        telegram_id = event.from_user.id
        state: FSMContext = data.get("state")

        async with SessionLocal() as session:
            channels = await get_all_channels(session)

            is_subscribed = await is_user_subscribed_to_all(
                event.bot, telegram_id, channels
            )

            if not is_subscribed:
                if isinstance(event, Message) and event.text and event.text.startswith("/start"):
                    parts = event.text.split()
                    if len(parts) > 1:
                        try:
                            referrer_id = int(parts[1])
                            await state.update_data(referrer_id=referrer_id)
                        except ValueError:
                            pass
                text = (
                    "<b>🔔 Чтобы пользоваться ботом и начать зарабатывать ⭐️, вам нужно подписаться на эти каналы.</b>\n\n"
                    "📌 За каждую подписку, выполненное задание или приглашённого друга вы будете получать ⭐️ или TON.\n\n"
                    "<b>✅ Пожалуйста, подпишитесь на все каналы, чтобы перейти в главное меню👇🏻</b>"
                )
                random.shuffle(channels)
                kb = channels_keyboard(channels)
                if isinstance(event, CallbackQuery):
                    try:
                        await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
                    except TelegramBadRequest:
                        await event.answer("❗️Пожалуйста подпишитесь на все КАНАЛЫ🤝", show_alert=True)
                else:
                    await event.answer(text, parse_mode="HTML", reply_markup=kb)
                return

            user = await get_user_by_telegram_id(session, telegram_id)

            if not user:
                if isinstance(event, Message) and (
                    (event.text and event.text.startswith("/start")) or event.contact
                ):
                    return await handler(event, data)
                elif isinstance(event, CallbackQuery) and event.data == "check_subs":
                    return await handler(event, data)
                else:
                    text = (
                        "❗Пожалуйста, сначала введите /start и завершите регистрацию."
                    )
                    if isinstance(event, CallbackQuery):
                        await event.answer(text, show_alert=True)
                    else:
                        await event.answer(text)
                    return

        return await handler(event, data)
