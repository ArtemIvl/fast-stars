from db.models.channel import Channel
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.subscription_log import SubscriptionLog


async def get_all_channels(session: AsyncSession) -> list[Channel]:
    result = await session.execute(select(Channel))
    channels = result.scalars().all()
    return channels


async def get_channel_by_id(session: AsyncSession, channel_id: int) -> Channel | None:
    channel = await session.get(Channel, channel_id)
    return channel


async def add_channel(
    session: AsyncSession, name: str, username: str, link: str
) -> None:
    new_channel = Channel(name=name, username=username, link=link)
    session.add(new_channel)
    await session.commit()


async def delete_channel(session: AsyncSession, channel_id: int) -> None:
    channel = await session.get(Channel, channel_id)
    if channel:
        await session.execute(delete(SubscriptionLog).where(SubscriptionLog.channel_id == channel_id))
        await session.execute(delete(Channel).where(Channel.id == channel_id))
        await session.delete(channel)
        await session.commit()

async def get_channel_completion_count(session: AsyncSession, channel_id: int) -> int:
    result = await session.execute(
        select(func.count()).select_from(SubscriptionLog).where(SubscriptionLog.channel_id == channel_id)
    )
    return result.scalar_one()
