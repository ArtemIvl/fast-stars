import asyncio
from decimal import Decimal

from aiogram import F, Router, types
from aiogram.enums import DiceEmoji
from db.session import SessionLocal
from keyboards.basketball_keyboard import (back_to_basketball_keyboard,
                                           basketball_keyboard)
from utils.basketball_requests import log_basketball_game
from utils.user_requests import get_user_by_telegram_id
from aiogram.fsm.context import FSMContext
from utils.game_settings_requests import get_game_setting

router = Router()


def register_basketball_handlers(dp) -> None:
    dp.include_router(router)


@router.callback_query(F.data == "basketball_game")
async def basketball_game_callback(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        "🏀 <b>Добро пожаловать в игру Basket Game</b>\n\n"
        "<b>Правила очень простые:</b>\n"
        "       1. Выбираешь ставку: 1⭐, 2⭐ или 5⭐.\n"
        "       2. Выбранное количество звёзд снимается с твоего Telegram-баланса.\n"
        "       3. Бросаешь мяч в кольцо🏀.\n"
        "       4. Если попадаешь — получаешь выигрыш Х1.5 на игровой баланс в боте.\n"
        "       5. Если промах — ничего не выигрываешь.\n\n"
        "<blockquote>✅ <b>Пример:</b>\n"
        "Ты выбрал ставку 1⭐ — с баланса списывается 1⭐.\n"
        "Если попал — получаешь 1.5⭐ на игровой баланс.\n"
        "Если нет — теряешь ставку</blockquote>",
        parse_mode="HTML",
        reply_markup=basketball_keyboard(),
    )


@router.callback_query(F.data.startswith("basketball_bet_"))
async def basketball_payment(callback: types.CallbackQuery, state: FSMContext) -> None:
    amount = int (callback.data.split("_")[-1])
    
    invoice = await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Бросок мяча",
        description="Оплата за игру в баскетбол",
        payload=f"basketball_game_{amount}",
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice(label="Ставка", amount=amount)],
        start_parameter="basketball_game",
    )

    await state.update_data(invoice_msg_id=invoice.message_id)

    async def delete_invoice_later():
        await asyncio.sleep(15)
        try:
            await callback.bot.delete_message(callback.from_user.id, invoice.message_id)
        except Exception:
            pass

    asyncio.create_task(delete_invoice_later())

@router.pre_checkout_query(lambda q: True)
async def pre_checkout_query_handler(pre_checkout_query: types.PreCheckoutQuery) -> None:
    await pre_checkout_query.bot.answer_pre_checkout_query(
        pre_checkout_query.id,
        ok=True,
    )

@router.message(F.successful_payment)
async def successful_basketball_payment(message: types.Message, state: FSMContext) -> None:
    amount = Decimal(message.successful_payment.total_amount)
    telegram_id = message.from_user.id

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)

        data = await state.get_data()
        invoice_msg_id = data.get("invoice_msg_id")
        if invoice_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=invoice_msg_id)
            except Exception:
                pass

        
        sent_dice = await message.answer_dice(emoji=DiceEmoji.BASKETBALL)
        result = sent_dice.dice.value
        win = result == 4 or result == 5
        multiplier = await get_game_setting(session, "basketball_multiplier")
        if multiplier is None:
            multiplier = Decimal("1.5")

        await log_basketball_game(session, user, amount, win, multiplier)
        await asyncio.sleep(3)

        if win:
            reward = amount * multiplier
            await message.answer(
                f"✅ Победа! +{reward:.2f} ⭐\nВаш баланс: {user.stars:.2f}",
                reply_markup=back_to_basketball_keyboard(amount),
            )
        else:
            await message.answer(
                f"❌ Неудача! -{amount:.2f} Telegram Stars",
                reply_markup=back_to_basketball_keyboard(amount),
            )