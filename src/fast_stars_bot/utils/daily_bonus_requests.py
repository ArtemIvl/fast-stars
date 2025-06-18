from datetime import date, timedelta
from decimal import Decimal

from db.models.daily_bonus_claim import DailyBonusClaim
from db.models.user import User
from sqlalchemy import desc, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.vip_requests import is_user_vip

MAX_BONUS_STREAK = 15


async def get_last_claim(session: AsyncSession, user_id: int) -> DailyBonusClaim | None:
    result = await session.execute(
        select(DailyBonusClaim)
        .where(DailyBonusClaim.user_id == user_id)
        .order_by(desc(DailyBonusClaim.claim_date))
        .limit(1)
    )
    return result.scalars().first()


def calculate_bonus_amount(
    last_claim: DailyBonusClaim | None, is_vip: bool
) -> tuple[Decimal, int]:
    today = date.today()

    if last_claim is None or last_claim.claim_date < today - timedelta(days=1):
        streak = 1
    elif last_claim.claim_date == today:
        raise ValueError("Бонус уже получен сегодня.")
    else:
        streak = last_claim.streak + 1
        if streak > MAX_BONUS_STREAK:
            streak = 1

    base_amount = Decimal("0.1") * streak
    bonus = base_amount * 2 if is_vip else base_amount
    return bonus.quantize(Decimal("0.01")), streak


async def claim_daily_bonus(session: AsyncSession, user: User) -> Decimal:
    last_claim = await get_last_claim(session, user.id)
    is_vip = await is_user_vip(session, user.id)
    bonus_amount, streak = calculate_bonus_amount(last_claim, is_vip)

    claim = DailyBonusClaim(
        user_id=user.id,
        claim_date=date.today(),
        bonus_amount=bonus_amount,
        streak=streak,
    )
    session.add(claim)
    user.stars += bonus_amount
    await session.commit()
    return bonus_amount


async def bonus_claims_today(session: AsyncSession) -> int:
    today = date.today()
    result = await session.execute(
        select(func.count(distinct(DailyBonusClaim.user_id))).where(
            DailyBonusClaim.claim_date == today
        )
    )
    return result.scalar_one()


async def total_bonus_amount_claimed(session: AsyncSession) -> Decimal:
    result = await session.execute(select(func.sum(DailyBonusClaim.bonus_amount)))
    return result.scalar_one() or Decimal("0.0")
