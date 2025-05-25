from aiogram import Router, types, F
from db.session import SessionLocal
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
from datetime import datetime, timedelta
from services.broadcast import send_broadcast, delayed_broadcast
from keyboards.admin_keyboards import audience_keyboard, time_choice_keyboard, admin_back_keyboard

message_admin_router = Router()

class BroadcastState(StatesGroup):
    choosing_audience = State()
    entering_message = State()
    choosing_time = State()
    waiting_to_send = State()

@message_admin_router.callback_query(F.data == "send_message")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastState.choosing_audience)
    await callback.message.edit_text("Кому отправить сообщение?", reply_markup=audience_keyboard())

@message_admin_router.callback_query(F.data.in_(["audience_all", "audience_vip"]))
async def choose_audience(callback: types.CallbackQuery, state: FSMContext):
    audience = "vip" if callback.data == "audience_vip" else "all"
    await state.update_data(audience=audience)
    await state.set_state(BroadcastState.entering_message)
    await callback.message.edit_text("Введите сообщение для рассылки (поддерживается форматирование Telegram):")

@message_admin_router.message(BroadcastState.entering_message)
async def receive_message_text(message: types.Message, state: FSMContext):
    data = {
        "text": message.text or message.caption,
        "entities": message.entities or message.caption_entities,
        "photo": message.photo[-1].file_id if message.photo else None
    }
    await state.update_data(**data)
    await state.set_state(BroadcastState.choosing_time)
    await message.answer("Когда отправить сообщение? Введите время в формате ЧЧ:ММ или выберите:", reply_markup=time_choice_keyboard())

@message_admin_router.callback_query(F.data == "send_now")
async def send_now(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("Отправка запущена...")
    await send_broadcast(callback.bot, data)
    await callback.message.edit_text("Рассылка завершена.", reply_markup=admin_back_keyboard())
    await state.clear()

@message_admin_router.message(BroadcastState.choosing_time)
async def schedule_send(message: types.Message, state: FSMContext):
    try:
        t = datetime.strptime(message.text.strip(), "%H:%M").time()
        await message.answer(f"Сообщение будет отправлено в {t.strftime('%H:%M')}", reply_markup=admin_back_keyboard())
        data = await state.get_data()
        now = datetime.now()
        send_at = datetime.combine(now.date(), t)
        if send_at < now:
            send_at = datetime.combine(now.date(), t) + timedelta(days=1)
        delay = (send_at - now).total_seconds()

        asyncio.create_task(delayed_broadcast(message.bot, delay, data))
        await state.clear()
    except ValueError:
        await message.answer("Неверный формат времени. Введите в формате ЧЧ:ММ")