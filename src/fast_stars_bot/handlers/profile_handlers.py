from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from db.session import SessionLocal
from keyboards.profile_keyboard import profile_keyboard
from utils.user_requests import get_user_by_telegram_id
from utils.vip_requests import is_user_vip
from aiogram.exceptions import TelegramBadRequest

router = Router()


def register_profile_handlers(dp) -> None:
    dp.include_router(router)


@router.callback_query(F.data == "profile")
async def profile_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    telegram_id = callback.from_user.id
    username = callback.from_user.username
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        is_vip = await is_user_vip(session, user.id)
        text = (
            "<b>👤 Ваш профиль: \n\n"
            f"🆔 Ваш ID: {telegram_id}\n"
            f"🕐 Дата регистрации: {user.reg_date}\n"
            f"🔗 Ваш username: {username}\n"
            f"💰 Ваш баланс: {user.stars:.2f}</b>⭐️"
        )
        if is_vip:
            text += "\n\n<b>💎 Вы - VIP пользователь!</b>"
       
    try:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=profile_keyboard(),
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise