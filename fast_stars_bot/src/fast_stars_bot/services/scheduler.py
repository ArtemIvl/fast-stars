from datetime import date

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from db.session import SessionLocal
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound, TelegramBadRequest
from pytz import timezone
from utils.daily_bonus_requests import get_last_claim
from utils.vip_requests import get_all_vip_users

scheduler = AsyncIOScheduler()
kyiv_tz = timezone("Europe/Kyiv")


def setup_daily_reminders(bot: Bot) -> None:
    scheduler.add_job(
        send_daily_reminders,
        CronTrigger(hour=9, minute=0, timezone=kyiv_tz),
        kwargs={"bot": bot},
    )
    scheduler.start()


async def send_daily_reminders(bot: Bot) -> None:
    async with SessionLocal() as session:
        vip_users = await get_all_vip_users(session)
        for user in vip_users:
            last_claim = await get_last_claim(session, user.id)
            if not last_claim or last_claim.claim_date != date.today():
                try:
                    await bot.send_message(
                        user.telegram_id,
                        "🎁 Не забудь забрать двойной бонус дня! Он уже ждёт тебя в меню.",
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
                    print(f"Неизвестная ошибка при отправке пользователю {user.telegram_id}: {e}")
                    continue
