from aiogram import Router, F, types
import asyncio
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from utils.user_requests import get_user_by_telegram_id, get_all_admins, has_previous_withdrawals
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

def calculate_commission(amount: Decimal) -> int:
    if amount >= 150:
        return 0
    elif amount >= 100:
        return 3
    elif amount >= 50:
        return 5
    return -1

@router.callback_query(F.data == "withdraw")
async def withdrawal_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        f"<b>💰 Вывод и обмен звёзд</b>\n\n"
        f"Вы можете:\n"
        f"🔹 Вывести звёзды на свой кошелёк – минимальная сумма вывода 50.0⭐️.\n"
        f"🔹 Обменять звёзды на TON – минимальная сумма обмена 150.0⭐️.\n"
        f"♾️ Конвертация звёзд в TON производится по курсу на сайте <b>Fragment</b>.\n"
        f"<blockquote><b>❗️Первый вывод всегда бесплатный.</b>\n"
        f"Дальнейшие выводы:\n"
        f"▪️ от 50 до 99.9⭐️ — комиссия 5 Telegram Stars\n"
        f"▪️ от 100 до 149.9⭐️ — комиссия 3 Telegram Stars\n"
        f"▪️ от 150⭐️ — <b>без комиссии</b>\n\n"
        f"💡 Комиссия списывается <b>только с баланса Telegram Stars</b>, а не с игрового баланса звёзд.</blockquote>\n\n"
        f"Выберите нужный вариант ниже! 👇🏻",
        parse_mode="HTML",
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
            "<b>✅ Запрос на вывод звёзд успешно отправлен!</b>\n\n"
            "Ожидайте подтверждения заявки в течение <b>24 часов</b>🤝",
            parse_mode="HTML",
            reply_markup=back_to_profile_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректный адрес для вывода.")


@router.message(F.text, WithdrawalStates.waiting_for_amount)
async def handle_withdrawal_amount(message: types.Message, state: FSMContext) -> None:
    try:
        amount = Decimal(message.text)
        async with SessionLocal() as session:
            telegram_id = message.from_user.id
            user = await get_user_by_telegram_id(session, telegram_id)
            first_time = not await has_previous_withdrawals(session, user.id)

        commission = 0 if first_time else calculate_commission(amount)
        if commission == -1:
            await message.answer("Минимальная сумма вывода 50.0 ⭐️.")
            return
        
        if commission > 0:
            await state.update_data({
                "withdraw_amount": str(amount),
                "commission": commission
            })
            await message.answer(
                f"Так как вы уже не в первый раз выводите ⭐️, необходимо оплатить комиссию от 3 до 5⭐️👇🏻\n"
                f"<blockquote>Не забывайте, что вывод от 150⭐️ — полностью <b>бесплатный</b>.</blockquote>",
                parse_mode="HTML",
                reply_markup=back_to_withdrawal_keyboard()
            )

            invoice = await message.bot.send_invoice(
                chat_id=message.chat.id,
                title="Комиссия за вывод",
                description=f"Комиссия за вывод {amount:.2f}⭐️",
                payload=f"withdraw_commission:{message.from_user.id}",
                provider_token="",
                currency="XTR", 
                prices=[types.LabeledPrice(label="Комиссия", amount=commission)],
                start_parameter="withdraw",
            )

            await state.update_data(invoice_msg_id=invoice.message_id)

            async def delete_invoice_later():
                await asyncio.sleep(15)
                try:
                    await message.bot.delete_message(message.from_user.id, invoice.message_id)
                except Exception:
                    pass
                
            asyncio.create_task(delete_invoice_later())
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
            "<b>✅ Запрос на вывод звёзд успешно отправлен!</b>\n\n"
            "Ожидайте подтверждения заявки в течение <b>24 часов</b>🤝",
            parse_mode="HTML",
            reply_markup=back_to_profile_keyboard()
        )
        await state.clear()
    except (ValueError, InvalidOperation):
        await message.answer("Пожалуйста, введите корректную сумму для вывода.")


@router.pre_checkout_query(lambda q: True)
async def process_checkout(pre_checkout_query: types.PreCheckoutQuery) -> None:
    await pre_checkout_query.bot.answer_pre_checkout_query(
        pre_checkout_query.id,
        ok=True
    )

@router.message(F.successful_payment, F.successful_payment.invoice_payload.startswith("withdraw_commission:"))
async def successful_withdraw_payment(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    amount = Decimal(data["withdraw_amount"])
    telegram_id = message.from_user.id

    async with SessionLocal() as session:
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
        "<b>✅ Запрос на вывод звёзд успешно отправлен!</b>\n\n"
        "Ожидайте подтверждения заявки в течение <b>24 часов</b>🤝",
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard()
    )
    await state.clear()


