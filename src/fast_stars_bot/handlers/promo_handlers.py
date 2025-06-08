from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from utils.promo_requests import activate_promo
from utils.user_requests import get_user_by_telegram_id
from keyboards.profile_keyboard import back_to_profile_keyboard
from aiogram import Bot

router = Router()

def register_promo_handlers(dp) -> None:
    dp.include_router(router)

class PromoState(StatesGroup):
    waiting_for_promo_code = State()

@router.callback_query(F.data == "promo_code")
async def activate_promo_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("<b>Введите промокод:</b>", parse_mode="HTML", reply_markup=back_to_profile_keyboard())
    await state.set_state(PromoState.waiting_for_promo_code)

@router.message(PromoState.waiting_for_promo_code)
async def activate_promo_code(message: types.Message, state: FSMContext) -> None:
    code = message.text.strip()
    telegram_id = message.from_user.id
    bot = message.bot

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        success, error_msg, reward = await activate_promo(session, user, code, bot)

        if success:
            await message.answer(f"<b>✅ Промокод успешно активирован! Вы получили {reward:.2f}⭐️.</b>", parse_mode="HTML")
        else:
            await message.answer(f"<b>{error_msg}</b>", parse_mode="HTML")

        if error_msg == 'Забанен за попытку использования VIP промо.':
            return
        else:
            await message.answer("<b>Введите промокод:</b>", parse_mode="HTML", reply_markup=back_to_profile_keyboard())
