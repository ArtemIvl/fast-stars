from utils.giveaway_requests import get_tickets_for_giveaway, buy_tickets_for_giveaway, get_tickets_per_user, get_all_active_giveaways, get_giveaway_by_id
from utils.user_requests import get_user_by_telegram_id
from aiogram import F, Router, types
from db.session import SessionLocal
from datetime import datetime, timedelta
from aiogram.fsm.context import FSMContext
from keyboards.giveaway_keyboard import giveaway_tickets_keyboard, giveaways_keyboard
import asyncio
from pytz import timezone

router = Router()

kyiv_tz = timezone("Europe/Kyiv")

def register_giveaway_handlers(dp) -> None:
    dp.include_router(router)

def plural_ru(number: int, forms: tuple[str, str, str]) -> str:
    if 11 <= number % 100 <= 14:
        return forms[2]
    if number % 10 == 1:
        return forms[0]
    if 2 <= number % 10 <= 4:
        return forms[1]
    return forms[2]

def format_timedelta_ru(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60

    parts = []
    if days > 0:
        parts.append(f"{days} {plural_ru(days, ('день', 'дня', 'дней'))}")
    if hours > 0:
        parts.append(f"{hours} {plural_ru(hours, ('час', 'часа', 'часов'))}")
    if minutes > 0:
        parts.append(f"{minutes} {plural_ru(minutes, ('минута', 'минуты', 'минут'))}")

    return " ".join(parts) if parts else "менее минуты"

@router.callback_query(F.data == "giveaways")
async def giveaways_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    async with SessionLocal() as session:
        giveaways = await get_all_active_giveaways(session)
        await callback.message.edit_text(
            "Cписок всех розыгрышей:",
            reply_markup=giveaways_keyboard(giveaways)
        )

@router.callback_query(F.data.startswith("view_giveaway_"))
async def view_giveaway_callback(callback: types.CallbackQuery) -> None:
    giveaway_id = int(callback.data.split("_")[2])
    telegram_id = callback.from_user.id
    async with SessionLocal() as session:
        giveaway = await get_giveaway_by_id(session, giveaway_id)
        tickets = await get_tickets_for_giveaway(session, giveaway.id)
        user = await get_user_by_telegram_id(session, telegram_id)
        tickets_bought = await get_tickets_per_user(session, giveaway.id, user.id)
        end = giveaway.end_time.astimezone(kyiv_tz).strftime("%d.%m.%Y %H:%M")

    text = (
        "<b>🎁 Розыгрыш 1000⭐️ на 50 победителей! 🎉</b>\n"
        "<blockquote>Испытай удачу и выиграй часть призового фонда!</blockquote>\n\n"
        "<b>Купи билет всего за 1⭐ и получи шанс стать одним из 50 счастливчиков!🏆</b>\n"
        "<blockquote>❗️Чем больше билетов — тем выше шанс на победу!🔥</blockquote>\n\n"
        "<b>📌 Условия участия:</b>\n"
        "• 1 билет = 1⭐\n"
        "• Количество билетов не ограничено\n"
        f"• Победителей — {giveaway.num_of_winners} человек\n"
        f"• Итоги — {end}\n"
        "• Выбор победителей — автоматически и прозрачно🫡\n\n"
        "<b>🏆 Распределение призов</b>:\n"
        "🥇 1 место — 120 ⭐\n"
        "🥈 2 место — 90 ⭐\n"
        "🥉 3 место — 70 ⭐\n"
        "4–10 места — по 40 ⭐\n"
        "11–20 места — по 20 ⭐\n"
        "21–50 места — по 8 ⭐\n\n"
        "🧠 Победители определяются случайным образом ботом\n"
        "⭐ Все призы автоматически начисляются на игровой баланс\n"
        "📢 Сразу после розыгрыша бот отправит список победителей в рассылке🫡\n\n"
    )

    unique_users = len(set(ticket.user_id for ticket in tickets))
    remaining_time = format_timedelta_ru(giveaway.end_time - datetime.now(kyiv_tz))

    text += (
        "<blockquote>✨ Не упусти шанс — участвуй прямо сейчас!\n"
    )

    if tickets_bought == 0:
        text += (
            f"🎟 Вы пока не принимаете участие в розыгрыше"
        )
    else:
        text += (
            f"🎟 У тебя уже: <b>{tickets_bought} билет(-ов)</b>"
        )

    text += (
        f"\n👥 Участников: <b>{unique_users}</b>\n"
        f"⏰ До окончания: <b>{remaining_time}</b></blockquote>"
        "\n\n<b>🛒 Выбери количество билетов для покупки ниже:👇🏻</b>"
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=giveaway_tickets_keyboard(giveaway)
    )

@router.callback_query(F.data.startswith("buy_tickets_"))
async def buy_giveaway_ticket(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[-1])
    giveaway_id = int(callback.data.split("_")[2])

    invoice = await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Билет(-ы) на розыгрыш",
        description="Покупка билетов для участия в розыгрыше",
        payload=f"giveaway_tickets_{giveaway_id}",
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice(label="Билеты", amount=amount)],
        start_parameter=f"giveaway_tickets_{giveaway_id}"
    )

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

@router.message(F.successful_payment, F.successful_payment.invoice_payload.startswith("giveaway_tickets_"))
async def successful_giveaway_payment(message: types.Message) -> None:
    amount = int(message.successful_payment.total_amount)
    giveaway_id = int(message.successful_payment.invoice_payload.split("_")[2])
    telegram_id = message.from_user.id

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        giveaway = await get_giveaway_by_id(session, giveaway_id)
        await buy_tickets_for_giveaway(session, giveaway.id, user.id, amount)

    message = await message.answer(
        f"Вы успешно приобрели {amount} билет(-ов)! ✅"
    )

    async def delete_message_later():
        await asyncio.sleep(10)
        try:
            await message.bot.delete_message(message.from_user.id, message.message_id)
        except Exception:
            pass

    asyncio.create_task(delete_message_later())
