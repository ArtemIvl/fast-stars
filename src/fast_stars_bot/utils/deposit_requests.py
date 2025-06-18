from decimal import Decimal

from db.models.deposit import Deposit, DepositStatus
from db.models.user import User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_deposit(
    session: AsyncSession, user_id: int, stars: Decimal, ton: Decimal, comment: str
) -> None:
    deposit = Deposit(
        user_id=user_id,
        stars=stars,
        ton=ton,
        comment=comment,
        status=DepositStatus.PENDING,
    )
    session.add(deposit)
    await session.commit()


async def get_latest_pending_deposit(
    session: AsyncSession, user_id: int
) -> Deposit | None:
    result = await session.execute(
        select(Deposit)
        .where(Deposit.user_id == user_id, Deposit.status == DepositStatus.PENDING)
        .order_by(Deposit.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def confirm_deposit(
    session: AsyncSession, user_id: int, comment: str
) -> Deposit | None:
    result = await session.execute(
        select(Deposit).where(
            Deposit.user_id == user_id,
            Deposit.comment == comment,
            Deposit.status == DepositStatus.PENDING,
        )
    )
    deposit = result.scalar_one_or_none()
    if deposit:
        deposit.status = DepositStatus.CONFIRMED

        user = await session.get(User, user_id)
        user.stars += deposit.stars

        await session.commit()
    return deposit


async def get_total_amount_deposited(session: AsyncSession) -> tuple[Decimal, Decimal]:
    result = await session.execute(
        select(
            func.coalesce(func.sum(Deposit.stars), 0),
            func.coalesce(func.sum(Deposit.ton), 0),
        ).where(Deposit.status == DepositStatus.CONFIRMED)
    )
    total_stars, total_ton = result.one()
    return total_stars, total_ton
