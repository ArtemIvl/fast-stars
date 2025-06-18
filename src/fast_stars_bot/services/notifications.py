# utils/notifications.py
from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
)
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.models.task import Task
from db.session import SessionLocal
from utils.task_requests import is_user_subscribed_to_task
from utils.vip_requests import get_all_vip_users


async def notify_vip_users_about_new_task(bot: Bot, task: Task) -> None:
    async with SessionLocal() as session:
        vip_users = await get_all_vip_users(session)
        for user in vip_users:
            try:
                is_subscribed = await is_user_subscribed_to_task(
                    bot, user.telegram_id, task
                )
                if is_subscribed and task.requires_subscription:
                    continue

                await bot.send_message(
                    user.telegram_id,
                    "🎉 Доступно новое задание! Проверьте его в меню заданий 👇",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Перейти к заданиям", callback_data="tasks"
                                )
                            ]
                        ]
                    ),
                )
            except TelegramForbiddenError:
                print(f"Бот заблокирован пользователем {user.telegram_id}.")
                continue
            except TelegramNotFound:
                print(f"Чат с пользователем {user.telegram_id} не найден.")
                continue
            except TelegramBadRequest as e:
                print(f"Некорректный запрос Telegram для {user.telegram_id}: {e}")
                continue
            except Exception as e:
                print(
                    f"Неизвестная ошибка при отправке пользователю {user.telegram_id}: {e}"
                )
                continue
