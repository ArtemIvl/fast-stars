import asyncio
from decimal import Decimal

from aiogram import F, Router, types
from aiogram.enums import DiceEmoji
from aiogram.fsm.context import FSMContext
from db.session import SessionLocal
from keyboards.slot_machine_keyboard import (
    back_to_slot_machine_keyboard,
    slot_machine_keyboard,
)
from utils.slot_machine_requests import log_slot_machine_spin
from utils.user_requests import get_user_by_telegram_id

router = Router()


def register_slot_machine_settings(dp) -> None:
    dp.include_router(router)


@router.callback_query(F.data == "slot_machine")
async def basketball_game_callback(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        "<b>🎰 Добро пожаловать в игру Slot Machine!</b>\n"
        "<blockquote>Почувствуй азарт и сорви джекпот прямо в Telegram!</blockquote>\n\n"
        "<b>🔹 Как играть:</b>\n"
        "<blockquote>1️⃣ Выбери количество спинов: <b>1, 5 или 10</b>.\n"
        "2️⃣ Со счёта списывается соответствующее количество звёзд ⭐️.\n"
        "3️⃣ Запускай барабаны — и испытай удачу!</blockquote>\n"
        "4️⃣ 🎰 <b>Выпало три 777 — множитель Х15!</b>\n"
        "5️⃣ 📍 <b>Если выпадает 2 семёрки — получаешь 1⭐️</b>\n"
        "6️⃣ 💥 <b>Выпало любые 3 одинаковых символа — множитель Х5!</b>\n"
        "7️⃣ 🧨 <b>Если не выпало 3 одинаковых фрукта или две 77</b> — увы, ты ничего не выигрываешь.\n\n"
        "<b>💡 Чем больше спинов — тем выше шанс сорвать крупный выигрыш!👇🏻</b>",
        parse_mode="HTML",
        reply_markup=slot_machine_keyboard(),
    )


@router.callback_query(F.data.startswith("slot_machine_"))
async def basketball_payment(callback: types.CallbackQuery, state: FSMContext) -> None:
    amount = int(callback.data.split("_")[-1])

    invoice = await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Покупка спинов",
        description="Оплата за слот машину",
        payload=f"slot_machine_{amount}",
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice(label="Спины", amount=amount)],
        start_parameter="slot_machine",
    )

    async def delete_invoice_later():
        await asyncio.sleep(15)
        try:
            await callback.bot.delete_message(callback.from_user.id, invoice.message_id)
        except Exception:
            pass

    asyncio.create_task(delete_invoice_later())


@router.pre_checkout_query(lambda q: True)
async def pre_checkout_query_handler(
    pre_checkout_query: types.PreCheckoutQuery,
) -> None:
    await pre_checkout_query.bot.answer_pre_checkout_query(
        pre_checkout_query.id,
        ok=True,
    )


@router.message(
    F.successful_payment,
    F.successful_payment.invoice_payload.startswith("slot_machine"),
)
async def successful_slot_machine_payment(message: types.Message) -> None:
    number_of_spins = int(message.successful_payment.total_amount)
    telegram_id = message.from_user.id
    total_reward = Decimal(0)
    results_text = []

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)

        for i in range(number_of_spins):
            sent_dice = await message.answer_dice(emoji=DiceEmoji.SLOT_MACHINE)
            result = sent_dice.dice.value

            if result in (1, 22, 43):
                reward = Decimal(5)
            elif result in (16, 32, 48, 52, 56, 60, 61, 62, 63):
                reward = Decimal(1)
            elif result == 64:
                reward = Decimal(15)
            else:
                reward = Decimal(0)

            await log_slot_machine_spin(session, user, reward)
            total_reward += reward
            results_text.append(
                f"🎰 Результат #{i+1}: {'+{}⭐'.format(reward) if reward > 0 else 'ничего'}"
            )
            await asyncio.sleep(3)

    text = (
        "🎰 <b>Результаты прокрутов:</b>\n\n"
        + "\n".join(results_text)
        + f"\n\n💰 <b>Общий выигрыш:</b> {total_reward}⭐"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=back_to_slot_machine_keyboard(number_of_spins),
    )
