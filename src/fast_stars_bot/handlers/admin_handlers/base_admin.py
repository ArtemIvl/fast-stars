from aiogram import F, Router, types
from db.session import SessionLocal
from keyboards.admin_keyboards import admin_keyboard
from utils.user_requests import check_admin
from aiogram.fsm.context import FSMContext

base_admin_router = Router()


@base_admin_router.message(F.text == "/admin")
async def admin_callback(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Добро пожаловать в админ панель!", reply_markup=admin_keyboard()
    )

@base_admin_router.callback_query(F.data == "back_admin")
async def back_admin_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Добро пожаловать в админ панель!", reply_markup=admin_keyboard()
    )
