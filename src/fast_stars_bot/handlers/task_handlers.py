from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from db.session import SessionLocal
from aiogram.exceptions import TelegramBadRequest
from utils.task_requests import is_task_completed, get_tasks_by_ids, get_all_tasks, is_user_subscribed_to_task, complete_task
from utils.user_requests import get_user_by_telegram_id
from keyboards.tasks_keyboard import tasks_keyboard, no_tasks_keyboard

router = Router()

def register_task_handlers(dp) -> None:
    dp.include_router(router)

@router.callback_query(F.data == "tasks")
async def tasks_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    telegram_id = callback.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        tasks = await get_all_tasks(session)
        bot = callback.bot

        tasks_to_show = []
        for task in tasks:
            completed = await is_task_completed(session, user.id, task.id)
            subscribed = await is_user_subscribed_to_task(bot, telegram_id, task) if task.requires_subscription else None

            if task.requires_subscription:
                if not subscribed:
                    tasks_to_show.append(task)
            else:
                if not completed:
                    tasks_to_show.append(task)

        if not tasks_to_show:
            await callback.message.edit_text(
                "<b>📌 Вкладка «Задания»</b>\n"
                "В этой вкладке время от времени появляются новые задания. Они доступны ограниченное время — от 30 минут и дольше.\n\n"
                "🔔 Чтобы не пропускать задания — заходите сюда почаще!\n\n"
                "💎 А если хотите получать <b>автоматические уведомления о новых заданиях</b> — активируйте <b>VIP-пакет</b> в разделе <b>«Мой профиль» → «VIP-пакет»</b>.",
                parse_mode="HTML",
                reply_markup=no_tasks_keyboard()
                )
            return
        
        task_ids = [task.id for task in tasks_to_show]
        await state.update_data(tasks_to_show_ids=task_ids)

        try:
            await callback.message.edit_text(
                "<b>📌 Вкладка «Задания»</b>\n"
                "В этой вкладке время от времени появляются новые задания. Они доступны ограниченное время — от 30 минут и дольше.\n\n"
                "🔔 Чтобы не пропускать задания — заходите сюда почаще!\n\n"
                "💎 А если хотите получать <b>автоматические уведомления о новых заданиях</b> — активируйте <b>VIP-пакет</b> в разделе <b>«Мой профиль» → «VIP-пакет»</b>.",
                parse_mode="HTML", 
                reply_markup=tasks_keyboard(tasks_to_show)
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise

@router.callback_query(F.data == "check_tasks")
async def check_tasks_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    telegram_id = callback.from_user.id
    bot = callback.bot

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        data = await state.get_data()
        task_ids = data.get("tasks_to_show_ids", [])
        tasks = await get_tasks_by_ids(session, task_ids)

        completed_now = []
        already_rewarded = []
        tasks_to_show = []
        has_visible_required_task = any(t.requires_subscription for t in tasks)

        for task in tasks:
            completed = await is_task_completed(session, user.id, task.id)
            subscribed = await is_user_subscribed_to_task(bot, telegram_id, task) if task.requires_subscription else None

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
        text_parts = []
        if completed_now:
            text = "🎉 Вы выполнили задания:\n"
            text += "\n".join(f"• {t.title} — +{t.reward:.2f} ⭐" for t in completed_now)
            text_parts.append(text)

        if already_rewarded:
            text = "⚠️ За следующие задания вы уже получали награду ранее:\n"
            text += "\n".join(f"• {t.title}" for t in already_rewarded)
            text_parts.append(text)

        if not text_parts:
            await callback.answer("❗️ Вы не выполнили задания.", show_alert=True)
        else:
            await callback.answer("\n\n".join(text_parts), show_alert=True)

        # Если остались задания для показа
        if not tasks_to_show:
            await callback.message.edit_text(
                "<b>📌 Вкладка «Задания»</b>\n"
                "В этой вкладке время от времени появляются новые задания. Они доступны ограниченное время — от 30 минут и дольше.\n\n"
                "🔔 Чтобы не пропускать задания — заходите сюда почаще!\n\n"
                "💎 А если хотите получать <b>автоматические уведомления о новых заданиях</b> — активируйте <b>VIP-пакет</b> в разделе <b>«Мой профиль» → «VIP-пакет»</b>.",
                parse_mode="HTML",
                reply_markup=no_tasks_keyboard()
            )
            await state.update_data(tasks_to_show_ids=[])
        else:
            await state.update_data(tasks_to_show_ids=[t.id for t in tasks_to_show])
            try:
                await callback.message.edit_text(
                    "<b>📌 Вкладка «Задания»</b>\n"
                    "В этой вкладке время от времени появляются новые задания. Они доступны ограниченное время — от 30 минут и дольше.\n\n"
                    "🔔 Чтобы не пропускать задания — заходите сюда почаще!\n\n"
                    "💎 А если хотите получать <b>автоматические уведомления о новых заданиях</b> — активируйте <b>VIP-пакет</b> в разделе <b>«Мой профиль» → «VIP-пакет»</b>.",
                    parse_mode="HTML",
                    reply_markup=tasks_keyboard(tasks_to_show)
                )
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    return
                raise