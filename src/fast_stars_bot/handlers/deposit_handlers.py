import random
from decimal import Decimal

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config.settings import settings
from db.session import SessionLocal
from keyboards.deposit_keyboard import confirm_payment_keyboard, deposit_keyboard
from utils.deposit_requests import (
    confirm_deposit,
    create_deposit,
    get_latest_pending_deposit,
)
from utils.tonapi import check_deposit_received
from utils.user_requests import get_all_admins, get_user_by_telegram_id

router = Router()


def register_deposit_handlers(dp) -> None:
    dp.include_router(router)


class DepositState(StatesGroup):
    waiting_for_payment_confirmation = State()


TON_WALLET_ADDRESS = settings.TON_WALLET_ADDRESS

DEPOSIT_OPTIONS = {
    "50": 0.4,
    "100": 0.75,
    "555": 4.0,
}


@router.callback_query(F.data == "deposit")
async def deposit_callback(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        f"<b>💰 Пополнение баланса</b>\n\n"
        f"Здесь вы можете пополнить <b>игровой баланс</b> в нашем боте и тем самым <b>поддержать развитие проекта.</b>\n\n"
        f"🔹 Выберите количество звёзд, на которое хотите пополнить баланс.\n"
        f"🔹 Оплата происходит в криптовалюте <b>TON</b>.\n\n"
        f"👇 Выберите сумму ниже и следуйте инструкции.",
        parse_mode="HTML",
        reply_markup=deposit_keyboard(),
    )


@router.callback_query(F.data.startswith("deposit_"))
async def handle_deposit_selection(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    amount = int(Decimal(callback.data.split("_")[1]))
    ton_amount = DEPOSIT_OPTIONS.get(str(amount))
    if not ton_amount:
        await callback.answer("Ошибка суммы.", show_alert=True)
        return

    comment_code = random.randint(1000, 9999)
    telegram_id = callback.from_user.id

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        await create_deposit(session, user.id, amount, ton_amount, str(comment_code))

    await state.update_data(comment=str(comment_code))
    await state.set_state(DepositState.waiting_for_payment_confirmation)

    text = (
        f"💳 Для пополнения на {amount}⭐ отправьте <b>{ton_amount} TON</b> на адрес:\n\n"
        f"<code>{TON_WALLET_ADDRESS}</code>\n\n"
        f"🔹 <b>Обязательно укажите комментарий:</b> <code>{comment_code}</code>\n\n"
        f"После оплаты нажмите кнопку “✅ Я оплатил”."
    )

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=confirm_payment_keyboard()
    )


@router.callback_query(
    DepositState.waiting_for_payment_confirmation, F.data == "confirm_deposit"
)
async def confirm_deposit_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    telegram_id = callback.from_user.id

    await callback.message.answer("⏳ Проверяем поступление средств...")

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        deposit = await get_latest_pending_deposit(session, user.id)
        if not deposit:
            await callback.message.answer("⚠️ Не найден активный депозит.")
            await state.clear()
            return

        ton_received = await check_deposit_received(
            expected_amount=deposit.ton,
            expected_comment=deposit.comment,
        )

        if ton_received:
            deposit = await confirm_deposit(session, user.id, deposit.comment)
            if deposit:
                await callback.message.answer(
                    f"✅ Поступило {ton_received}, благодарим за покупку!\n\n"
                    f"{deposit.stars}⭐️ зачислено на ваш баланс."
                )

                admins = await get_all_admins(session)
                for admin in admins:
                    await callback.bot.send_message(
                        admin.telegram_id,
                        f"💰 Новый депозит успешно получен!\n\n"
                        f"👤 Пользователь: @{user.username or '—'}\n"
                        f"🆔 Telegram ID: {user.telegram_id}\n"
                        f"💵 Сумма: {deposit.ton} TON ({deposit.stars}⭐)\n"
                        f"📎 Комментарий: <code>{deposit.comment}</code>",
                        parse_mode="HTML",
                    )
            else:
                await callback.message.answer("⚠️ Не удалось подтвердить депозит.")
        else:
            await callback.message.answer(
                "❌ Средства пока не поступили. Попробуйте ещё раз через несколько минут.",
                reply_markup=confirm_payment_keyboard(),
            )
    await state.clear()
