import asyncio

from aiogram import F, Router, types
from db.session import SessionLocal
from keyboards.stats_keyboard import stats_keyboard
from utils.user_requests import get_total_users, get_users_registered_today
from utils.withdrawal_requests import get_total_withdrawn_stars

router = Router()


def register_stats_handlers(dp) -> None:
    dp.include_router(router)


@router.callback_query(F.data == "stats")
async def stats_callback(callback: types.CallbackQuery) -> None:
    async with SessionLocal() as session:
        total_users, users_today, withdrawn_total = await asyncio.gather(
            get_total_users(session),
            get_users_registered_today(session),
            get_total_withdrawn_stars(session),
        )

    withdrawn_total -= (
        100_000  # estimation of declined withdrawals (before they were tracked)
    )

    text = (
        "<b>📊 Статистика нашего бота:</b>\n\n"
        f"— <b>👨 Активных пользователей: {total_users}</b>\n"
        f"— <b>👶 Новых за сегодня: {users_today}</b>\n\n"
        f"— <b>📤 Выплачено всего: {withdrawn_total}</b>\n\n"
        f"— 📅 Бот создан <b>09.02.2025</b>"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=stats_keyboard()
    )
