from datetime import datetime
from decimal import Decimal

from db.models.giveaway import Giveaway, GiveawayTicket
from pytz import timezone
from sqlalchemy import asc, case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

kyiv_tz = timezone("Europe/Kyiv")


async def get_active_bot_giveaway(session: AsyncSession) -> Giveaway | None:
    now = datetime.now(kyiv_tz)
    result = await session.execute(
        select(Giveaway).where(
            Giveaway.is_finished == False,
            Giveaway.channel_link == None,
            Giveaway.start_time <= now,
        )
    )
    return result.scalars().first()


async def get_all_active_giveaways(session: AsyncSession) -> list[Giveaway] | None:
    now = datetime.now(kyiv_tz)
    result = await session.execute(
        select(Giveaway)
        .where(
            Giveaway.start_time <= now,
            Giveaway.is_finished == False,
            Giveaway.end_time >= now,
        )
        .order_by(
            case(
                (Giveaway.username == None, 0),
                (Giveaway.channel_link == None, 0),
                else_=1,
            ),
            asc(Giveaway.id),
        )
    )
    giveaways = result.scalars().all()
    return giveaways


async def get_all_giveaways(session: AsyncSession) -> list[Giveaway]:
    result = await session.execute(
        select(Giveaway).order_by(
            case(
                (Giveaway.username == None, 0),
                (Giveaway.channel_link == None, 0),
                else_=1,
            ),
            asc(Giveaway.id),
        )
    )
    giveaways = result.scalars().all()
    return giveaways


async def get_tickets_for_giveaway(
    session: AsyncSession, giveaway_id: int
) -> list[GiveawayTicket] | None:
    result = await session.execute(
        select(GiveawayTicket).where(GiveawayTicket.giveaway_id == giveaway_id)
    )
    if result:
        return result.scalars().all()
    else:
        return None


async def buy_tickets_for_giveaway(
    session: AsyncSession, giveaway_id: int, user_id: int, amount: int
) -> None:
    for t in range(amount):
        session.add(GiveawayTicket(user_id=user_id, giveaway_id=giveaway_id))
    await session.commit()


async def get_tickets_per_user(
    session: AsyncSession, giveaway_id: int, user_id: int
) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(GiveawayTicket)
        .where(
            GiveawayTicket.giveaway_id == giveaway_id, GiveawayTicket.user_id == user_id
        )
    )
    return result.scalar_one()


async def get_giveaway_by_id(
    session: AsyncSession, giveaway_id: int
) -> Giveaway | None:
    giveaway = await session.get(Giveaway, giveaway_id)
    return giveaway


async def create_giveaway(
    session: AsyncSession,
    name: str,
    start_time: datetime,
    end_time: datetime,
    prize_pool: Decimal,
    channel_link: str,
    channel_username: str,
    num_of_winners: int,
) -> Giveaway:
    giveaway = Giveaway(
        name=name,
        start_time=start_time,
        end_time=end_time,
        is_finished=False,
        prize_pool=prize_pool,
        channel_link=channel_link,
        username=channel_username,
        num_of_winners=num_of_winners,
    )
    session.add(giveaway)
    await session.commit()
    return giveaway


async def delete_giveaway(session: AsyncSession, giveaway_id: int) -> None:
    giveaway = await session.get(Giveaway, giveaway_id)
    if giveaway:
        await session.execute(
            delete(GiveawayTicket).where(GiveawayTicket.giveaway_id == giveaway_id)
        )
        await session.execute(delete(Giveaway).where(Giveaway.id == giveaway_id))
        await session.commit()


async def mark_giveaway_finished(session: AsyncSession, giveaway_id: int) -> None:
    giveaway = await get_giveaway_by_id(session, giveaway_id)
    giveaway.is_finished = True
    await session.commit()
