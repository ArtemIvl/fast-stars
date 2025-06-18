from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from db.session import SessionLocal
from keyboards.menu_keyboard import menu_keyboard
from utils.user_requests import get_user_by_telegram_id

router = Router()


def register_menu_handlers(dp) -> None:
    dp.include_router(router)


def get_menu_text(user) -> str:
    return (
        "<b>Чтобы получить больше ⭐️, выполняйте задания и приглашайте друзей!👥\n\n"
        "‼️ За накрутку рефералов — БАН без выплат! ‼️\n\n"
        f"Баланс: {user.stars:.2f}⭐️</b>"
    )


@router.message(F.text.in_({"/menu", "⭐️ Меню"}))
async def menu_callback(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    telegram_id = message.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)

    await message.answer(
        get_menu_text(user),
        parse_mode="HTML",
        reply_markup=menu_keyboard(),
    )


@router.callback_query(F.data == "back")
async def back_menu_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    telegram_id = callback.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)

    try:
        await callback.message.edit_text(
            get_menu_text(user),
            parse_mode="HTML",
            reply_markup=menu_keyboard(),
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise
