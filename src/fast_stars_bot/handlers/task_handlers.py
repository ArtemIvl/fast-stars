from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from db.session import SessionLocal
from keyboards.tasks_keyboard import no_tasks_keyboard, tasks_keyboard
from utils.task_requests import (
    complete_task,
    get_all_tasks,
    get_tasks_by_ids,
    is_task_completed,
    is_user_subscribed_to_task,
)
from utils.user_requests import get_user_by_telegram_id

router = Router()


def register_task_handlers(dp) -> None:
    dp.include_router(router)


TASKS_HEADER = (
    "<b>📌 Вкладка «Задания»</b>\n"
    "В этой вкладке время от времени появляются новые задания. Они доступны ограниченное время — от 30 минут и дольше.\n\n"
    "🔔 Чтобы не пропускать задания — заходите сюда почаще!\n\n"
    "💎 А если хотите получать <b>автоматические уведомления о новых заданиях</b> — активируйте <b>VIP-пакет</b> в разделе <b>«Мой профиль» → «VIP-пакет»</b>."
)


async def send_tasks_message(
    callback: types.CallbackQuery, tasks, state: FSMContext
) -> None:
    if not tasks:
        await callback.message.edit_text(
            TASKS_HEADER, parse_mode="HTML", reply_markup=no_tasks_keyboard()
        )
        await state.update_data(tasks_to_show_ids=[])
        return

    await state.update_data(tasks_to_show_ids=[task.id for task in tasks])
    try:
        await callback.message.edit_text(
            TASKS_HEADER, parse_mode="HTML", reply_markup=tasks_keyboard(tasks)
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.callback_query(F.data == "tasks")
async def tasks_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    telegram_id = callback.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        tasks = await get_all_tasks(session)

        tasks_to_show = []
        for task in tasks:
            completed = await is_task_completed(session, user.id, task.id)
            if task.requires_subscription:
                subscribed = await is_user_subscribed_to_task(
                    callback.bot, telegram_id, task
                )
                if not subscribed:
                    tasks_to_show.append(task)
            elif not completed:
                tasks_to_show.append(task)

        await send_tasks_message(callback, tasks_to_show, state)


@router.callback_query(F.data == "check_tasks")
async def check_tasks_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    telegram_id = callback.from_user.id

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        data = await state.get_data()
        task_ids = data.get("tasks_to_show_ids", [])
        tasks = await get_tasks_by_ids(session, task_ids)

        completed_now, already_rewarded, tasks_to_show = [], [], []
        has_visible_required_task = any(task.requires_subscription for task in tasks)

        for task in tasks:
            completed = await is_task_completed(session, user.id, task.id)
            subscribed = (
                await is_user_subscribed_to_task(callback.bot, telegram_id, task)
                if task.requires_subscription
                else None
            )

            if task.requires_subscription:
                if subscribed and not completed:
                    # подписался на обязательное задание впервые — считаем выполненным
                    await complete_task(session, user, task)
                    completed_now.append(task)
                elif subscribed and completed:
                    # уже выполнил, повторно награда не нужна — не показываем
                    already_rewarded.append(task)
                else:
                    # еще не подписан на обязательное — показываем
                    tasks_to_show.append(task)
            else:
                # необязательное задание показываем только если нет невыполненных обязательных
                if not completed:
                    tasks_to_show.append(task)

        # Если нет видимых обязательных заданий — выполняем все невыполненные необязательные
        if not has_visible_required_task:
            for task in tasks_to_show:
                completed = await is_task_completed(session, user.id, task.id)
                if not completed:
                    await complete_task(session, user, task)
                    completed_now.append(task)
            tasks_to_show = [t for t in tasks_to_show if t not in completed_now]

        # Формируем текст для поп-апа
        messages = []
        if completed_now:
            msg = "🎉 Вы выполнили задания:\n" + "\n".join(
                f"• {t.title} — +{t.reward:.2f} ⭐" for t in completed_now
            )
            messages.append(msg)
        if already_rewarded:
            msg = "⚠️ За следующие задания вы уже получали награду ранее:\n" + "\n".join(
                f"• {t.title}" for t in already_rewarded
            )
            messages.append(msg)

        if messages:
            await callback.answer("\n\n".join(messages), show_alert=True)
        else:
            await callback.answer("❗️ Вы не выполнили задания.", show_alert=True)

        await send_tasks_message(callback, tasks_to_show, state)
