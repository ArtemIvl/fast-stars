from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from keyboards.admin_keyboards import (delete_channels_keyboard,
                                      manage_channels_keyboard, channel_info_keyboard)
from utils.channel_requests import (add_channel, delete_channel,
                                    get_all_channels, get_channel_by_id, get_channel_completion_count)

channel_admin_router = Router()


class AddChannelState(StatesGroup):
    waiting_for_name = State()
    waiting_for_username = State()
    waiting_for_link = State()


@channel_admin_router.callback_query(F.data == "manage_channels")
async def manage_channels_callback(callback: types.CallbackQuery) -> None:
    async with SessionLocal() as session:
        channels = await get_all_channels(session)
        await callback.message.edit_text(
            "Список каналов:", reply_markup=manage_channels_keyboard(channels)
        )


@channel_admin_router.callback_query(F.data == "add_channel")
async def add_channel_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    await callback.message.answer("Please enter the channel name:")
    await state.set_state(AddChannelState.waiting_for_name)


@channel_admin_router.message(AddChannelState.waiting_for_name)
async def add_channel_name(message: types.Message, state: FSMContext) -> None:
    await state.update_data(channel_name=message.text)
    await message.answer("Please enter @username or chat id:")
    await state.set_state(AddChannelState.waiting_for_username)


@channel_admin_router.message(AddChannelState.waiting_for_username)
async def add_channel_username(message: types.Message, state: FSMContext) -> None:
    # if not message.text.startswith("@"):
    #     await message.answer(
    #         "The username must start with '@'. Please enter a valid channel username:"
    #     )
    #     return
    await state.update_data(channel_username=message.text)
    await message.answer("Please enter the channel link:")
    await state.set_state(AddChannelState.waiting_for_link)


@channel_admin_router.message(AddChannelState.waiting_for_link)
async def add_channel_link(message: types.Message, state: FSMContext) -> None:
    if not message.text.startswith("https://t.me/"):
        await message.answer(
            "The link must start with 'https://t.me/'. Please enter a valid channel link:"
        )
        return

    data = await state.get_data()
    channel_name = data.get("channel_name")
    channel_username = data.get("channel_username")
    channel_link = message.text

    async with SessionLocal() as session:
        await add_channel(
            session, name=channel_name, username=channel_username, link=channel_link
        )
        await message.answer("The channel has successfully been added!")
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
        await callback.message.edit_text(
            "Канал удален!",
            reply_markup=manage_channels_keyboard(await get_all_channels(session)),
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
