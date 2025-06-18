from decimal import Decimal

from db.models.withdrawal import Withdrawal, WithdrawalStatus
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.user_requests import get_user_by_id


async def create_withdrawal_request(
    session: AsyncSession, user_id: int, stars: Decimal, ton_address: str | None = None
) -> int:
    user = await get_user_by_id(session, user_id)
    if user.stars < stars:
        raise ValueError("Insufficient stars for withdrawal.")
    user.stars -= stars
    withdrawal_request = Withdrawal(
        user_id=user_id, stars=stars, ton_address=ton_address
    )
    session.add_all([user, withdrawal_request])
    await session.commit()
    return withdrawal_request.id


async def get_withdrawal_by_id(
    session: AsyncSession, withdrawal_id: int
) -> Withdrawal | None:
    withdrawal = await session.execute(
        select(Withdrawal).where(Withdrawal.id == withdrawal_id)
    )
    if withdrawal:
        return withdrawal.scalars().first()
    else:
        return None


async def get_all_pending_withdrawals(session: AsyncSession) -> list[Withdrawal]:
    result = await session.execute(
        select(Withdrawal).where(Withdrawal.status == WithdrawalStatus.PENDING)
    )
    return result.scalars().all()


async def get_completed_user_withdrawals(
    session: AsyncSession, user_id: int
) -> list[Withdrawal] | None:
    result = await session.execute(
        select(Withdrawal).where(
            Withdrawal.user_id == user_id, Withdrawal.status != WithdrawalStatus.PENDING
        )
    )
    if result is None:
        return None
    else:
        return result.scalars().all()


async def update_withdrawal_status(
    session: AsyncSession, withdrawal_id: int, status: WithdrawalStatus
) -> None:
    withdrawal = await session.get(Withdrawal, withdrawal_id)
    if withdrawal:
        withdrawal.status = status
        await session.commit()
    else:
        raise ValueError(f"Withdrawal with id {withdrawal_id} not found.")


async def get_total_withdrawn_stars(session: AsyncSession) -> Decimal:
    query = select(func.coalesce(func.sum(Withdrawal.stars), 0)).where(
        Withdrawal.status == WithdrawalStatus.APPROVED
    )
    result = await session.execute(query)
    total_stars = result.scalar()
    return Decimal(total_stars)
