from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from keyboards.admin_keyboards import (
    back_to_channels_keyboard,
    channel_info_keyboard,
    delete_channels_keyboard,
    manage_channels_keyboard,
)
from utils.channel_requests import (
    add_channel,
    delete_channel,
    get_all_channels,
    get_channel_by_id,
    get_channel_completion_count,
)

channel_admin_router = Router()


class AddChannelState(StatesGroup):
    waiting_for_name = State()
    waiting_for_username = State()
    waiting_for_link = State()
    waiting_for_subscription_status = State()


@channel_admin_router.callback_query(F.data == "manage_channels")
async def manage_channels_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    await state.clear()
    async with SessionLocal() as session:
        channels = await get_all_channels(session)
        await callback.message.edit_text(
            "Список каналов:", reply_markup=manage_channels_keyboard(channels)
        )


@channel_admin_router.callback_query(F.data == "add_channel")
async def add_channel_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    sent = await callback.message.edit_text(
        "Введите название канала:", reply_markup=back_to_channels_keyboard()
    )
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddChannelState.waiting_for_name)


@channel_admin_router.message(AddChannelState.waiting_for_name)
async def add_channel_name(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    await state.update_data(channel_name=message.text)
    sent = await message.answer(
        "Введите @username или chat id:", reply_markup=back_to_channels_keyboard()
    )
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddChannelState.waiting_for_username)


@channel_admin_router.message(AddChannelState.waiting_for_username)
async def add_channel_username(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    await state.update_data(channel_username=message.text)
    sent = await message.answer(
        "Введите ссылку на канал:", reply_markup=back_to_channels_keyboard()
    )
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddChannelState.waiting_for_link)


@channel_admin_router.message(AddChannelState.waiting_for_link)
async def add_channel_link(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    url = message.text.strip()
    if not url.startswith("https://t.me/"):
        sent = await message.answer(
            "Ссылка должна начинаться с 'https://t.me/'. Пожалуйста, введите корректную ссылку:",
            reply_markup=back_to_channels_keyboard(),
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        return
    await state.update_data(channel_link=url)
    sent = await message.answer(
        "Канал требует подписки? (да/нет):", reply_markup=back_to_channels_keyboard()
    )
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddChannelState.waiting_for_subscription_status)


@channel_admin_router.message(AddChannelState.waiting_for_subscription_status)
async def add_channel_subscription_status(
    message: types.Message, state: FSMContext
) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    subscription = message.text.strip().lower()
    if subscription not in ["да", "нет"]:
        sent = await message.answer(
            "Пожалуйста, введите 'да' или 'нет'.",
            reply_markup=back_to_channels_keyboard(),
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        return
    await state.update_data(subscription=subscription)

    data = await state.get_data()
    channel_name = data.get("channel_name")
    channel_username = data.get("channel_username")
    channel_link = data.get("channel_link")
    requires_subscription = data.get("subscription") == "да"

    async with SessionLocal() as session:
        await add_channel(
            session,
            name=channel_name,
            username=channel_username,
            link=channel_link,
            requires_subscription=requires_subscription,
        )
        channels = await get_all_channels(session)
        await message.answer(
            "Канал был успешно добавлен!",
            reply_markup=manage_channels_keyboard(channels),
        )
        await state.clear()


@channel_admin_router.callback_query(F.data == "remove_channel")
async def remove_channel_callback(callback: types.CallbackQuery) -> None:
    async with SessionLocal() as session:
        channels = await get_all_channels(session)
    await callback.message.edit_text(
        "Выберите канал для удаления:", reply_markup=delete_channels_keyboard(channels)
    )


@channel_admin_router.callback_query(F.data.startswith("del_channel_"))
async def delete_channel_handler(callback: types.CallbackQuery) -> None:
    channel_id = int(callback.data.split("_")[2])
    async with SessionLocal() as session:
        await delete_channel(session, channel_id)
        channels = await get_all_channels(session)
        await callback.message.edit_text(
            "Канал удален!", reply_markup=manage_channels_keyboard(channels)
        )


@channel_admin_router.callback_query(F.data.startswith("channel_"))
async def info_channel_handler(callback: types.CallbackQuery) -> None:
    channel_id = int(callback.data.split("_")[1])
    async with SessionLocal() as session:
        channel = await get_channel_by_id(session, channel_id)
        completion_count = await get_channel_completion_count(session, channel_id)
        await callback.message.edit_text(
            f"Название канала: {channel.name}\n"
            f"Юзернейм канала: {channel.username}\n"
            f"Ссылка на канал: {channel.link}\n"
            f"Количество подписок: {completion_count}",
            disable_web_page_preview=True,
            reply_markup=channel_info_keyboard(channel),
        )
