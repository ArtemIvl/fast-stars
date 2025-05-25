from decimal import Decimal
from aiogram.exceptions import TelegramBadRequest
from aiogram import Bot
from db.models.channel import Channel
from db.models.subscription_log import SubscriptionLog
from db.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def resolve_chat_id(bot: Bot, channel: Channel) -> int | str | None:
    url_part = channel.link.strip().rstrip("/").split("/")[-1]

    if not url_part.startswith("+"):
        return "@" + url_part  # публичный канал
    try:
        chat = await bot.get_chat(channel.username)
        return chat.id  # приватный канал
    except Exception as e:
        print(f"Error resolving chat ID for {channel.username}: {e}")
        return None



async def is_user_subscribed_to_all(
    bot: Bot, telegram_id: int, channels: list[Channel]
) -> bool:
    for channel in channels:
        try:
            chat_id = await resolve_chat_id(bot, channel)
            if chat_id is None:
                continue  # если не можем получить чат, просто пропускаем

            member = await bot.get_chat_member(chat_id=chat_id, user_id=telegram_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except TelegramBadRequest as e:
            print(f"Can't check subscription for {channel.id}: {e}")
            continue
    return True


async def reward_user_for_subscription(
    session: AsyncSession, bot: Bot, user: User, channels: list[Channel]
) -> None:
    for channel in channels:
        rewarded = await session.execute(
            select(SubscriptionLog).filter(
                SubscriptionLog.user_id == user.id,
                SubscriptionLog.channel_id == channel.id,
            )
        )
        if rewarded.scalars().first():
            continue

        try:
            chat_id = await resolve_chat_id(bot, channel)
            if chat_id is None:
                session.add(SubscriptionLog(user_id=user.id, channel_id=channel.id))
                user.stars += Decimal("1")
                continue

            member = await bot.get_chat_member(
                chat_id=chat_id, user_id=user.telegram_id
            )
            if member.status in ["member", "administrator", "creator"]:
                subscription_log = SubscriptionLog(
                    user_id=user.id, channel_id=channel.id
                )
                session.add(subscription_log)
                user.stars += Decimal("1")
        except Exception as e:
            print(
                f"Error checking channel {channel.username} for user {user.telegram_id}: {e}"
            )

    await session.commit()