from datetime import date, timedelta
from decimal import Decimal

from db.models.user import User
from db.models.vip_subscription import VipSubscription
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def is_user_vip(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(
        select(VipSubscription).where(
            VipSubscription.user_id == user_id, VipSubscription.end_date >= date.today()
        )
    )
    return result.scalars().first() is not None


async def get_active_vip_subscription(
    session: AsyncSession, user_id: int
) -> VipSubscription | None:
    result = await session.execute(
        select(VipSubscription).where(
            VipSubscription.user_id == user_id,
            VipSubscription.start_date <= date.today(),
            VipSubscription.end_date >= date.today(),
        )
    )
    return result.scalars().first()


async def grant_vip(session: AsyncSession, user: User) -> bool:
    if user.stars < Decimal("99.9"):
        return False

    already_vip = await is_user_vip(session, user.id)
    if already_vip:
        return False

    user.stars -= Decimal("99.9")
    vip_subscription = VipSubscription(
        user_id=user.id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
    )
    session.add(vip_subscription)
    await session.commit()
    return True


async def get_all_vip_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User)
        .join(VipSubscription)
        .where(VipSubscription.end_date >= date.today())
    )
    return result.scalars().all()
