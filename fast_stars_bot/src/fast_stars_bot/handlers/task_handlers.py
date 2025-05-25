from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from db.session import SessionLocal
from aiogram.exceptions import TelegramBadRequest
from utils.task_requests import is_task_completed, complete_task, get_all_tasks, is_user_subscribed_to_task
from utils.user_requests import get_user_by_telegram_id
from keyboards.tasks_keyboard import tasks_keyboard, no_tasks_keyboard

router = Router()

def register_task_handlers(dp) -> None:
    dp.include_router(router)


@router.callback_query(F.data == "tasks")
async def tasks_callback(callback: types.CallbackQuery) -> None:
    telegram_id = callback.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        tasks = await get_all_tasks(session)

        tasks_to_show = []
        for task in tasks:
            completed = await is_task_completed(session, user.id, task.id)
            is_subscribed = await is_user_subscribed_to_task(callback.bot, telegram_id, task) if task.requires_subscription else None

            if task.requires_subscription:
                if not is_subscribed and not completed:
                    tasks_to_show.append(task)
                elif not is_subscribed and completed:
                    tasks_to_show.append(task)
            else:
                if not completed:
                    tasks_to_show.append(task)
                
        if not tasks_to_show:
            await callback.message.edit_text("Нет доступных заданий.", reply_markup=no_tasks_keyboard())
            return
        
        await callback.message.edit_text(
            "📋 Доступные задания:\n\n", 
            reply_markup=tasks_keyboard(tasks_to_show)
        )

@router.callback_query(F.data == "check_tasks")
async def check_tasks_callback(callback: types.CallbackQuery) -> None:
    telegram_id = callback.from_user.id
    bot = callback.bot

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        tasks = await get_all_tasks(session)

        completed = []
        tasks_to_show = []

        has_visible_required_task = False
        for task in tasks:
            if task.requires_subscription:
                is_subscribed = await is_user_subscribed_to_task(bot, telegram_id, task)
                if not is_subscribed:
                    has_visible_required_task = True
                    break

        for task in tasks:
            is_completed = await is_task_completed(session, user.id, task.id)

            if task.requires_subscription:
                is_subscribed = await is_user_subscribed_to_task(bot, telegram_id, task)

                if not is_subscribed:
                    tasks_to_show.append(task)

                if not is_completed and is_subscribed:
                    await complete_task(session, user, task)
                    completed.append(task)

            else:
                if not is_completed:
                    tasks_to_show.append(task)

                if not is_completed and not has_visible_required_task:
                    await complete_task(session, user, task)
                    completed.append(task)

        if completed:
            text = "🎉 Вы выполнили задания:\n"
            for task in completed:
                text += f"• {task.title} — +{task.reward:.2f} ⭐\n"
            await callback.answer(f"Задания засчитаны!\n{text}", show_alert=True)
        else:
            await callback.answer("❗️ Вы не выполнили задания.", show_alert=True)

        # Отображение оставшихся заданий
        if not tasks_to_show:
            await callback.message.edit_text("Нет доступных заданий.", reply_markup=no_tasks_keyboard())
        else:
            try:
                await callback.message.edit_text(
                    "📋 Доступные задания:\n\n",
                    reply_markup=tasks_keyboard(tasks_to_show)
                )
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    return
                raise