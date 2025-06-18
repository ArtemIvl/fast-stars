from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from keyboards.admin_keyboards import (
    back_to_giveaways_keyboard,
    giveaway_info_keyboard,
    manage_giveaways_keyboard,
)
from pytz import timezone
from services.giveaway_scheduler import (
    schedule_giveaway_finish,
    schedule_giveaway_start_notification,
    unschedule_giveaway_finish,
)
from utils.giveaway_requests import (
    create_giveaway,
    delete_giveaway,
    get_all_giveaways,
    get_giveaway_by_id,
    get_tickets_for_giveaway,
)

kyiv_tz = timezone("Europe/Kyiv")

giveaway_admin_router = Router()


class AddGiveawayState(StatesGroup):
    waiting_for_name = State()
    waiting_for_channel_link = State()
    waiting_for_channel_username = State()
    waiting_for_prize_pool = State()
    waiting_for_num_winners = State()
    waiting_for_start_time = State()
    waiting_for_duration = State()


@giveaway_admin_router.callback_query(F.data == "manage_giveaways")
async def manage_giveaways_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    await state.clear()
    async with SessionLocal() as session:
        giveaways = await get_all_giveaways(session)
        await callback.message.edit_text(
            "Управление розыгрышами:", reply_markup=manage_giveaways_keyboard(giveaways)
        )


@giveaway_admin_router.callback_query(F.data.startswith("giveaway_"))
async def info_giveaway_handler(callback: types.CallbackQuery) -> None:
    giveaway_id = int(callback.data.split("_")[1])

    async with SessionLocal() as session:
        giveaway = await get_giveaway_by_id(session, giveaway_id)
        tickets = await get_tickets_for_giveaway(session, giveaway_id)
    total_tickets = len(tickets)
    unique_users = len(set(ticket.user_id for ticket in tickets))
    start = giveaway.start_time.astimezone(kyiv_tz).strftime("%d.%m.%Y %H:%M")
    end = giveaway.end_time.astimezone(kyiv_tz).strftime("%d.%m.%Y %H:%M")
    giveaway_link = f"https://t.me/STARS_FAST_bot?start=giveaway_{giveaway.id}"
    now = datetime.now(kyiv_tz)

    await callback.message.edit_text(
        f"Название: {giveaway.name}\n"
        f"Ссылка на розыгрыш: <code>{giveaway_link}</code>\n\n"
        f"Розыгрыш от админа? <b>{f'Да, <code>{giveaway.channel_link}</code>, {giveaway.username}' if giveaway.channel_link else 'Нет'}</b>\n\n"
        f"Призовой пул: {giveaway.prize_pool}\n"
        f"Победителей: {giveaway.num_of_winners}\n"
        f"Активен? <b>{'Нет' if giveaway.is_finished or giveaway.start_time > now else 'Да'}</b>\n\n"
        f"Начало: <b>{start}</b>\n"
        f"Конец: <b>{end}</b>\n\n"
        f"Всего куплено билетов: {total_tickets}\n"
        f"Всего участников: {unique_users}",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=giveaway_info_keyboard(giveaway),
    )


@giveaway_admin_router.callback_query(F.data == "add_giveaway")
async def add_giveaway_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    sent = await callback.message.edit_text(
        "Введите название розыгрыша:", reply_markup=back_to_giveaways_keyboard()
    )
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddGiveawayState.waiting_for_name)


@giveaway_admin_router.message(AddGiveawayState.waiting_for_name)
async def set_giveaway_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    await state.update_data(name=message.text.strip())
    sent = await message.answer(
        "Введите ссылку на канал:", reply_markup=back_to_giveaways_keyboard()
    )
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddGiveawayState.waiting_for_channel_link)


@giveaway_admin_router.message(AddGiveawayState.waiting_for_channel_link)
async def set_giveaway_channel_link(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    url = message.text.strip()
    if not url.startswith("https://"):
        sent = await message.answer(
            "Ссылка должна начинаться с 'https://. Пожалуйста, введите корректную ссылку:",
            reply_markup=back_to_giveaways_keyboard(),
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        return
    await state.update_data(channel_url=url)
    sent = await message.answer(
        "Введите @username или chat_id (с -):",
        reply_markup=back_to_giveaways_keyboard(),
    )
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddGiveawayState.waiting_for_channel_username)


@giveaway_admin_router.message(AddGiveawayState.waiting_for_channel_username)
async def add_task_url(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    username = message.text.strip()
    await state.update_data(channel_username=username)
    sent = await message.answer(
        "Введите призовой фонд (в звёздах ⭐):",
        reply_markup=back_to_giveaways_keyboard(),
    )
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddGiveawayState.waiting_for_prize_pool)


@giveaway_admin_router.message(AddGiveawayState.waiting_for_prize_pool)
async def set_giveaway_prize_pool(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    try:
        prize = Decimal(message.text.strip())
        if prize <= 0:
            sent = await message.answer(
                "Вознаграждение должно быть больше 0. Попробуйте снова.",
                reply_markup=back_to_giveaways_keyboard(),
            )
            await state.update_data(last_bot_message_id=sent.message_id)
            return
        await state.update_data(prize_pool=prize)
        sent = await message.answer(
            "Введите количество победителей:", reply_markup=back_to_giveaways_keyboard()
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        await state.set_state(AddGiveawayState.waiting_for_num_winners)
    except InvalidOperation:
        sent = await message.answer(
            "Некорректный ввод. Пожалуйста, введите число.",
            reply_markup=back_to_giveaways_keyboard(),
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        return


@giveaway_admin_router.message(AddGiveawayState.waiting_for_num_winners)
async def set_giveaway_num_winners(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    try:
        winners = int(message.text)
        if winners <= 0:
            sent = await message.answer(
                "Количество победителей должно быть больше 0. Попробуйте снова.",
                reply_markup=back_to_giveaways_keyboard(),
            )
            await state.update_data(last_bot_message_id=sent.message_id)
            return
        await state.update_data(num_of_winners=winners)
        sent = await message.answer(
            "Введите дату и время начала розыгрыша (в формате ДД.ММ.ГГГГ / ЧЧ:ММ) по Киеву:",
            reply_markup=back_to_giveaways_keyboard(),
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        await state.set_state(AddGiveawayState.waiting_for_start_time)
    except ValueError:
        sent = await message.answer(
            "Количество победителей должно быть целым числом. Попробуйте снова.",
            reply_markup=back_to_giveaways_keyboard(),
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        return


@giveaway_admin_router.message(AddGiveawayState.waiting_for_start_time)
async def set_giveaway_start_time(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    try:
        # Пример: 10.06.2025 / 18:30
        raw = message.text.strip()
        date_str, time_str = raw.split("/")
        start_dt = kyiv_tz.localize(
            datetime.strptime(
                date_str.strip() + " " + time_str.strip(), "%d.%m.%Y %H:%M"
            )
        )

        if start_dt <= datetime.now(kyiv_tz):
            sent = await message.answer(
                "⛔ Дата начала должна быть в будущем. Попробуйте снова.",
                reply_markup=back_to_giveaways_keyboard(),
            )
            await state.update_data(last_bot_message_id=sent.message_id)
            return
        await state.update_data(start_time=start_dt)
        sent = await message.answer(
            "⏳ Введите длительность розыгрыша в формате: <b>дней часов минут</b>\nПример: <code>3 5 30</code>",
            parse_mode="HTML",
            reply_markup=back_to_giveaways_keyboard(),
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        await state.set_state(AddGiveawayState.waiting_for_duration)
    except Exception as e:
        print(str(e))
        sent = await message.answer(
            "❗Неверный формат. Введите дату в формате: <code>ДД.ММ.ГГГГ / ЧЧ:ММ</code>",
            parse_mode="HTML",
            reply_markup=back_to_giveaways_keyboard(),
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        return


@giveaway_admin_router.message(AddGiveawayState.waiting_for_duration)
async def set_giveaway_duration(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    try:
        parts = list(map(int, message.text.strip().split()))
        if len(parts) not in [2, 3]:
            raise ValueError("Неверный формат ввода")

        days, hours = parts[0], parts[1]
        minutes = parts[2] if len(parts) == 3 else 0

        if days < 0 or hours < 0 or minutes < 0:
            sent = await message.answer(
                "Дни, часы и минуты не могут быть меньше 0. Попробуйте снова.",
                reply_markup=back_to_giveaways_keyboard(),
            )
            await state.update_data(last_bot_message_id=sent.message_id)
            return

        giveaway_name = data.get("name")
        channel_url = data.get("channel_url")
        channel_username = data.get("channel_username")
        prize_pool = data.get("prize_pool")
        num_of_winners = data.get("num_of_winners")
        start_time = data.get("start_time")
        end_time = start_time + timedelta(days=days, hours=hours, minutes=minutes)

        async with SessionLocal() as session:
            giveaway = await create_giveaway(
                session=session,
                name=giveaway_name,
                start_time=start_time,
                end_time=end_time,
                prize_pool=prize_pool,
                channel_link=channel_url,
                channel_username=channel_username,
                num_of_winners=num_of_winners,
            )
            schedule_giveaway_finish(giveaway.id, giveaway.end_time, message.bot)
            schedule_giveaway_start_notification(
                giveaway.id, giveaway.start_time, message.bot
            )

        sent = await message.answer(
            "✅ Розыгрыш успешно создан!", reply_markup=back_to_giveaways_keyboard()
        )
        await state.clear()
    except Exception as e:
        print(str(e))
        sent = await message.answer(
            "❗ Введите 2 или 3 числа через пробел (дни часы [минуты]), например: <code>2 3</code> или <code>1 5 30</code>",
            parse_mode="HTML",
            reply_markup=back_to_giveaways_keyboard(),
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        return


@giveaway_admin_router.callback_query(F.data.startswith("del_giveaway_"))
async def delete_giveaway_handler(callback: types.CallbackQuery) -> None:
    giveaway_id = int(callback.data.split("_")[2])
    async with SessionLocal() as session:
        unschedule_giveaway_finish(giveaway_id)
        await delete_giveaway(session, giveaway_id)
        print(f"giveaway {giveaway_id} was deleted")
        giveaways = await get_all_giveaways(session)
        await callback.message.edit_text(
            "Задание удалено!",
            reply_markup=manage_giveaways_keyboard(giveaways),
        )
