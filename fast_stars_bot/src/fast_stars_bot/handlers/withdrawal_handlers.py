from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from utils.user_requests import get_user_by_telegram_id, get_all_admins
from utils.withdrawal_requests import create_withdrawal_request, get_withdrawal_by_id
from decimal import Decimal, InvalidOperation
from keyboards.withdrawal_keyboard import withdrawal_keyboard, back_to_withdrawal_keyboard
from keyboards.profile_keyboard import back_to_profile_keyboard
from keyboards.admin_keyboards import withdraw_info_keyboard
from handlers.admin_handlers.withdraw_admin import generate_detailed_withdraw_text

router = Router()

def register_withdrawal_handlers(dp) -> None:
    dp.include_router(router)

class WithdrawalStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_swap_amount = State()
    waiting_for_ton_address = State()


@router.callback_query(F.data == "withdraw")
async def withdrawal_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        f"💰 Вывод и обмен звёзд\n\n"
        f"Вы можете:\n"
        f"🔹 Вывести звёзды на свой кошелёк – минимальная сумма вывода 50.0⭐️.\n"
        f"🔹 Обменять звёзды на TON – минимальная сумма обмена 150.0⭐️.\n"
        f"♾️ Конвертация звёзд в TON производится по курсу на сайте Fragment.\n\n"
        f"Выберите нужный вариант ниже! 👇🏻",
        reply_markup=withdrawal_keyboard()
    )

@router.callback_query(F.data == "withdraw_stars")
async def withdraw_stars_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    telegram_id = callback.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user.stars < 50:
            await callback.answer(
                "Вывод доступен от 50.0 ⭐️",
                show_alert=True,
            )
            return
        await callback.message.edit_text(
            "Введите сумму для вывода (от 50.0 ⭐️):",
            reply_markup=back_to_withdrawal_keyboard()
        )
        await state.set_state(WithdrawalStates.waiting_for_amount)

@router.callback_query(F.data == "withdraw_ton")
async def withdraw_ton_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    telegram_id = callback.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session,telegram_id)
        if user.stars < 150:
            await callback.answer(
                "Вывод доступен от 150.0 ⭐️",
                show_alert=True,
            )
            return
        await callback.message.edit_text(
            "Введите сумму для вывода (от 150.0 ⭐️):",
            reply_markup=back_to_withdrawal_keyboard()
        )
        await state.set_state(WithdrawalStates.waiting_for_swap_amount)

@router.message(WithdrawalStates.waiting_for_swap_amount)
async def handle_swap_amount(message: types.Message, state: FSMContext) -> None:
    try:
        amount = Decimal(message.text)
        if amount < 150:
            await message.answer("Минимальная сумма вывода 150.0 ⭐️.")
            return
        await state.update_data(swap_amount=message.text)
        await state.set_state(WithdrawalStates.waiting_for_ton_address)
        await message.answer(
            "Введите адрес TON-кошелька для вывода:",
            reply_markup=back_to_withdrawal_keyboard()
        )
    except (ValueError, InvalidOperation):
        await message.answer("Пожалуйста, введите корректную сумму для вывода.")

@router.message(WithdrawalStates.waiting_for_ton_address)
async def handle_ton_address(message: types.Message, state: FSMContext) -> None:
    try:
        ton_address = str(message.text)
        # add checks for valid ton address format
        async with SessionLocal() as session:
            telegram_id = message.from_user.id
            user = await get_user_by_telegram_id(session, telegram_id)
            data = await state.get_data()
            amount = Decimal(data.get("swap_amount"))
            if user.stars < amount:
                await message.answer("Недостаточно звёзд для вывода.")
                return
            
            withdrawal_id = await create_withdrawal_request(session, user.id, amount, ton_address)
            withdrawal = await get_withdrawal_by_id(session, withdrawal_id)
            admins = await get_all_admins(session)
            detailed_text = await generate_detailed_withdraw_text(session, withdrawal, user)
            for admin in admins:
                await message.bot.send_message(
                    admin.telegram_id,
                    detailed_text,
                    parse_mode="HTML",
                    reply_markup=withdraw_info_keyboard(withdrawal_id, user.id),
                )
        
        await message.answer(
            "✅ Запрос на вывод звёзд успешно отправлен!\n"
            "Ожидайте подтверждения от администрации.",
            reply_markup=back_to_profile_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректный адрес для вывода.")


@router.message(WithdrawalStates.waiting_for_amount)
async def handle_withdrawal_amount(message: types.Message, state: FSMContext) -> None:
    try:
        amount = Decimal(message.text)
        if amount < 50:
            await message.answer("Минимальная сумма вывода 50.0 ⭐️.")
            return
        
        async with SessionLocal() as session:
            telegram_id = message.from_user.id
            user = await get_user_by_telegram_id(session, telegram_id)
            if user.stars < amount:
                await message.answer("Недостаточно звёзд для вывода.")
                return
            
            withdrawal_id = await create_withdrawal_request(session, user.id, amount)
            withdrawal = await get_withdrawal_by_id(session, withdrawal_id)
            admins = await get_all_admins(session)
            detailed_text = await generate_detailed_withdraw_text(session, withdrawal, user)
            for admin in admins:
                await message.bot.send_message(
                    admin.telegram_id,
                    detailed_text,
                    parse_mode="HTML",
                    reply_markup=withdraw_info_keyboard(withdrawal_id, user.id),
                )
        
        await message.answer(
            "✅ Запрос на вывод звёзд успешно отправлен!\n"
            "Ожидайте подтверждения от администрации.",
            reply_markup=back_to_profile_keyboard()
        )
        await state.clear()
    except (ValueError, InvalidOperation):
        await message.answer("Пожалуйста, введите корректную сумму для вывода.")


