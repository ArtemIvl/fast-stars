import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from random import choices

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from db.session import SessionLocal
from pytz import timezone
from utils.giveaway_requests import (
    create_giveaway,
    get_active_bot_giveaway,
    get_giveaway_by_id,
    get_tickets_for_giveaway,
    mark_giveaway_finished,
)
from utils.user_requests import add_stars_to_user, get_all_users, get_user_by_id

scheduler = AsyncIOScheduler()
kyiv_tz = timezone("Europe/Kyiv")


def setup_weekly_giveaway(bot: Bot) -> None:
    scheduler.add_job(
        finish_weekly_giveaway,
        CronTrigger(day_of_week="sun", hour=20, minute=00, timezone=kyiv_tz),
        kwargs={"bot": bot},
    )
    scheduler.start()


async def finish_weekly_giveaway(bot: Bot) -> None:
    async with SessionLocal() as session:
        giveaway = await get_active_bot_giveaway(session)
        if not giveaway:
            return

        await handle_giveaway_finish(bot, session, giveaway.id)
        await ensure_active_bot_giveaway_exists()


async def finish_scheduled_giveaway(giveaway_id: int, bot: Bot) -> None:
    async with SessionLocal() as session:
        await handle_giveaway_finish(bot, session, giveaway_id)


def schedule_giveaway_finish(giveaway_id: int, end_time: datetime, bot: Bot):
    scheduler.add_job(
        finish_scheduled_giveaway,
        DateTrigger(run_date=end_time),
        kwargs={"giveaway_id": giveaway_id, "bot": bot},
        id=f"finish_giveaway_{giveaway_id}",
        replace_existing=True,
    )
    print(f"✅ Scheduled giveaway {giveaway_id} for {end_time}")


def unschedule_giveaway_finish(giveaway_id: int):
    job_id = f"finish_giveaway_{giveaway_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


def schedule_giveaway_start_notification(
    giveaway_id: int, start_time: datetime, bot: Bot
):
    scheduler.add_job(
        notify_giveaway_start,
        DateTrigger(run_date=start_time),
        kwargs={"giveaway_id": giveaway_id, "bot": bot},
        id=f"start_notify_giveaway_{giveaway_id}",
        replace_existing=True,
    )


async def ensure_active_bot_giveaway_exists() -> None:
    async with SessionLocal() as session:
        active = await get_active_bot_giveaway(session)
        if not active:
            now = datetime.now(kyiv_tz)
            days_until_sunday = (6 - now.weekday()) % 7 or 7
            next_sunday = (now + timedelta(days=days_until_sunday)).replace(
                hour=20, minute=0, second=0, microsecond=0
            )
            name = "🏆 Розыгрыш от FAST Stars 🏆"
            await create_giveaway(
                session,
                name=name,
                start_time=now,
                end_time=next_sunday,
                prize_pool=Decimal(1000),
                channel_link=None,
                channel_username=None,
                num_of_winners=int(50),
            )


async def notify_giveaway_start(giveaway_id: int, bot: Bot) -> None:
    async with SessionLocal() as session:
        giveaway = await get_giveaway_by_id(session, giveaway_id)
        if not giveaway:
            return
        users = await get_all_users(session)

        text = (
            f"<b>🎉 Начался новый розыгрыш: {giveaway.name}!</b>\n\n"
            f"📌 Призовой фонд: <b>{giveaway.prize_pool}⭐</b>\n"
            f"🏆 Победителей: <b>{giveaway.num_of_winners}</b>\n"
            f"⏰ Итоги: <b>{giveaway.end_time.astimezone(kyiv_tz).strftime('%d.%m.%Y %H:%M')}</b>\n\n"
            f"🎟 Участвуй прямо сейчас — чем больше билетов, тем выше шансы на победу!"
        )

        for user in users:
            try:
                await bot.send_message(user.telegram_id, text, parse_mode="HTML")
            except Exception:
                continue


async def handle_giveaway_finish(bot: Bot, session, giveaway_id: int) -> None:
    giveaway = await get_giveaway_by_id(session, giveaway_id)
    tickets = await get_tickets_for_giveaway(session, giveaway_id)
    if not tickets:
        return

    pool = [t.user_id for t in tickets]
    winners = choices(pool, k=giveaway.num_of_winners)

    await mark_giveaway_finished(session, giveaway_id)

    user_rewards = {}
    prize_distribution = generate_prizes(giveaway.num_of_winners, giveaway.prize_pool)

    for i, user_id in enumerate(winners, start=1):
        reward = prize_distribution.get(i, 0)
        user_rewards.setdefault(user_id, 0)
        user_rewards[user_id] += reward

    for user_id, total_reward in user_rewards.items():
        await add_stars_to_user(session, user_id, Decimal(total_reward))

    result_text = (
        f"<b>🎉 Результаты розыгрыша {giveaway.name}!</b>\n"
        f"<i>Спасибо за участие. Вот список победителей:</i>\n\n"
    )
    for i, user_id in enumerate(winners[: giveaway.num_of_winners], 1):
        user = await get_user_by_id(session, user_id)
        result_text += (
            f"<b>{i}.</b> @{user.username or '—'} — {prize_distribution.get(i, 0)}⭐️\n"
        )
    result_text += "\nСледи за следующими розыгрышами — скоро новый!"

    users = await get_all_users(session)
    for user in users:
        try:
            await bot.send_message(user.telegram_id, result_text, parse_mode="HTML")
        except Exception:
            continue


def generate_prizes(num_winners: int, prize_pool: Decimal) -> dict:
    # Пропорции соответствуют 1000 prize_pool
    base_values = {
        1: 120,
        2: 90,
        3: 70,
        **{i: 40 for i in range(4, 11)},
        **{i: 20 for i in range(11, 21)},
        **{i: 8 for i in range(21, 51)},
    }

    # Урежем до нужного количества победителей
    base_values = {i: v for i, v in base_values.items() if i <= num_winners}
    total = sum(base_values.values())

    scaled = {
        i: round(prize_pool * Decimal(v / total), 2) for i, v in base_values.items()
    }
    return scaled
