from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from decimal import Decimal, InvalidOperation
from keyboards.admin_keyboards import manage_tasks_keyboard, delete_tasks_keyboard, task_info_keyboard, back_to_tasks_keyboard
from utils.task_requests import add_task, get_all_tasks, get_task_by_id, get_task_completion_count, delete_task
from services.notifications import notify_vip_users_about_new_task

from db.session import SessionLocal

task_admin_router = Router()

class AddTaskState(StatesGroup):
    waiting_for_task_title = State()
    waiting_for_task_url = State()
    waiting_for_task_username = State()
    waiting_for_task_reward = State()
    waiting_for_subscription_status = State()

@task_admin_router.callback_query(F.data == "manage_tasks")
async def manage_tasks_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    async with SessionLocal() as session:
        tasks = await get_all_tasks(session)
        await callback.message.edit_text(
            "Управление заданиями:", reply_markup=manage_tasks_keyboard(tasks)
        )

@task_admin_router.callback_query(F.data == "add_task")
async def add_task_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    sent = await callback.message.edit_text("Введите название задания:", reply_markup=back_to_tasks_keyboard())
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddTaskState.waiting_for_task_title)

@task_admin_router.message(AddTaskState.waiting_for_task_title)
async def add_task_title(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    title = message.text.strip()
    await state.update_data(task_title=title)
    sent = await message.answer("Введите ссылку на задание:", reply_markup=back_to_tasks_keyboard())
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddTaskState.waiting_for_task_url)

@task_admin_router.message(AddTaskState.waiting_for_task_url)
async def add_task_title(message: types.Message, state: FSMContext) -> None:
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
            reply_markup=back_to_tasks_keyboard()
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        return
    await state.update_data(task_url=url)
    sent = await message.answer("Введите @username или chat_id:", reply_markup=back_to_tasks_keyboard())
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddTaskState.waiting_for_task_username)

@task_admin_router.message(AddTaskState.waiting_for_task_username)
async def add_task_url(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    username = message.text.strip()
    await state.update_data(task_username=username)
    sent = await message.answer("Введите вознаграждение за выполнение задания (в звёздах ⭐):", reply_markup=back_to_tasks_keyboard())
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddTaskState.waiting_for_task_reward)

@task_admin_router.message(AddTaskState.waiting_for_task_reward)
async def add_task_reward(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    try:
        reward = Decimal(message.text)
        if reward <= 0:
            sent = await message.answer("Вознаграждение должно быть больше 0. Попробуйте снова.", reply_markup=back_to_tasks_keyboard())
            await state.update_data(last_bot_message_id=sent.message_id)
            return
        await state.update_data(task_reward=reward)
        sent = await message.answer("Задание требует подписки? (да/нет):", reply_markup=back_to_tasks_keyboard())
        await state.update_data(last_bot_message_id=sent.message_id)
        await state.set_state(AddTaskState.waiting_for_subscription_status)
    except InvalidOperation:
        sent = await message.answer("Некорректный ввод. Пожалуйста, введите число.", reply_markup=back_to_tasks_keyboard())
        await state.update_data(last_bot_message_id=sent.message_id)
        return

@task_admin_router.message(AddTaskState.waiting_for_subscription_status)
async def add_task_subscription_status(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    subscription = message.text.strip().lower()
    if subscription not in ["да", "нет"]:
        sent = await message.answer("Пожалуйста, введите 'да' или 'нет'.", reply_markup=back_to_tasks_keyboard())
        await state.update_data(last_bot_message_id=sent.message_id)
        return
    await state.update_data(subscription=subscription)

    data = await state.get_data()
    task_title = data.get("task_title")
    task_url = data.get("task_url")
    task_username = data.get("task_username")
    task_reward = data.get("task_reward")
    requires_subscription = data.get("subscription") == "да"

    async with SessionLocal() as session:
        new_task = await add_task(session, title=task_title, url=task_url, username=task_username, reward=task_reward, requires_subscription=requires_subscription)
        await notify_vip_users_about_new_task(message.bot, new_task)
        tasks = await get_all_tasks(session) 

    await message.answer("Задание успешно добавлено!", reply_markup=manage_tasks_keyboard(tasks))
    await state.clear()


@task_admin_router.callback_query(F.data == "delete_task")
async def delete_task_callback(callback: types.CallbackQuery) -> None:
    async with SessionLocal() as session:
        tasks = await get_all_tasks(session)
    await callback.message.edit_text(
        "Выберите задание для удаления:", reply_markup=delete_tasks_keyboard(tasks)
    )

@task_admin_router.callback_query(F.data.startswith("del_task_"))
async def delete_task_handler(callback: types.CallbackQuery) -> None:
    task_id = int(callback.data.split("_")[2])
    async with SessionLocal() as session:
        await delete_task(session, task_id)
        tasks = await get_all_tasks(session)
        await callback.message.edit_text(
            "Задание удалено!",
            reply_markup=manage_tasks_keyboard(tasks),
        )

@task_admin_router.callback_query(F.data.startswith("task_"))
async def info_task_handler(callback: types.CallbackQuery) -> None:
    task_id = int(callback.data.split("_")[1])
    async with SessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        completion_count = await get_task_completion_count(session, task_id)
        await callback.message.edit_text(
            f"Название задания: {task.title}\n"
            f"Ссылка на задание: {task.url}\n"
            f"Награда за задание: {task.reward}\n"
            f"Username или chat_id: {task.username}\n"
            f"Требуется подписка: {'Да' if task.requires_subscription else 'Нет'}\n"
            f"Количество выполнений: {completion_count}",
            disable_web_page_preview=True,
            reply_markup=task_info_keyboard(task),
        )
