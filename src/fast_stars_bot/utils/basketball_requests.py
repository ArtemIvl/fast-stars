from decimal import Decimal
from sqlalchemy import select, func

from db.models.basketball_log import BasketballLog
from db.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


async def log_basketball_game(
    session: AsyncSession, user: User, bet: Decimal, result: bool, multiplier: Decimal
) -> None:
    log = BasketballLog(user_id=user.id, bet=bet, result=result)
    session.add(log)
    if result:
        user.stars += bet * multiplier
    await session.commit()

async def get_basketball_stats(session: AsyncSession, multiplier: Decimal) -> tuple[int, Decimal, Decimal]:
    total_games = await session.scalar(
        select(func.count()).select_from(BasketballLog)
        )

    total_won_stars = await session.scalar(
        select(func.coalesce(func.sum(BasketballLog.bet * multiplier), Decimal("0")))
        .where(BasketballLog.result.is_(True))
    )

    total_lost_stars = await session.scalar(
        select(func.coalesce(func.sum(BasketballLog.bet), Decimal("0")))
        # .where(BasketballLog.result.is_(False))
    )

    return [total_games, total_won_stars, total_lost_stars]
