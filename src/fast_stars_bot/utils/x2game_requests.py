from db.models.x2game import X2Game
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User

async def get_or_create_stats(session: AsyncSession) -> X2Game:
    result = await session.execute(select(X2Game).limit(1))
    stats = result.scalar_one_or_none()
    if not stats:
        stats = X2Game(lost=Decimal(0), won=Decimal(0))
        session.add(stats)
        await session.commit()
    return stats

async def save_x2game_results(session: AsyncSession, user: User, bet: Decimal, result: bool) -> None:
    stats = await get_or_create_stats(session)
    if result:
        stats.won += bet
        user.stars += bet
    else:
        stats.lost += bet
        user.stars -= bet
    await session.commit()