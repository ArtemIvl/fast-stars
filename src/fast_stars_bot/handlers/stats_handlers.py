from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
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
        total_users = await get_total_users(session)
        users_registered_today = await get_users_registered_today(session)
        total_withdrawn_stars = await get_total_withdrawn_stars(session)
    await callback.message.edit_text(
        f"<b>📊 Статистика нашего бота:</b>\n\n"
        f"— <b>👨 Активных пользователей: {total_users}</b>\n"
        f"— <b>👶 Новых за сегодня: {users_registered_today}</b>\n\n"
        f"— <b>📤 Выплачено всего: {total_withdrawn_stars - 100000}</b>\n\n"
        f"— 📅 Бот создан <b>09.02.2025</b>",
        parse_mode="HTML",
        reply_markup=stats_keyboard()
    )