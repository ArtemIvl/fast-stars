from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from db.models.referral import Referral
from db.models.task import TaskCompletion, Task
from datetime import date
from db.models.daily_bonus_claim import DailyBonusClaim

async def create_referral(session: AsyncSession, referral_id: int, referrer_id: int) -> None:
    referral = Referral(referral_id=referral_id, referrer_id=referrer_id)
    session.add(referral)
    await session.commit()

async def has_referral(session: AsyncSession, referral_id: int) -> bool:
    result = await session.execute(
        select(Referral).filter(Referral.referral_id == referral_id)
    )
    return result.scalars().first() is not None

async def reward_for_referral(session: AsyncSession, user: User) -> None:
    user.stars += 4
    await session.commit()

async def get_referral_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count()).select_from(Referral).where(Referral.referrer_id == user_id)
    )
    return result.scalar_one()

async def get_referrals(session: AsyncSession, referrer_id: int) -> list[User]:
    result = await session.execute(
        select(User).join(Referral, Referral.referral_id == User.id).where(Referral.referrer_id == referrer_id)
    )
    return result.scalars().all()

async def get_referrals_page(session: AsyncSession, referrer_id: int, page: int = 1, per_page: int = 10,) -> list[User]:
    offset = (page - 1) * per_page
    result = await session.execute(
        select(User)
        .join(Referral, Referral.referral_id == User.id)
        .where(Referral.referrer_id == referrer_id)
        .order_by(User.reg_date.desc())
        .offset(offset)
        .limit(per_page)
    )
    return result.scalars().all()

async def get_nested_referral_count(session: AsyncSession, referral_ids: list[int]) -> int:
    if not referral_ids:
        return 0
    result = await session.execute(
        select(func.count()).select_from(Referral).where(Referral.referrer_id.in_(referral_ids))
    )
    return result.scalar_one()

async def get_bonus_claim_percent(session: AsyncSession, referral_ids: list[int]) -> int:
    if not referral_ids:
        return 0
    
    total_percent = 0
    counted = 0
    
    for referral_id in referral_ids:
        user_data = await session.execute(
            select(User.reg_date).where(User.id == referral_id)
        )
        reg_date = user_data.scalar_one_or_none()
        if not reg_date:
            continue

        days_since_reg = (date.today() - reg_date).days + 1 or 1

        claim_count_result = await session.execute(
            select(func.count()).where(DailyBonusClaim.user_id == referral_id)
        )
        claim_count = claim_count_result.scalar_one()

        percent = min((claim_count / days_since_reg) * 100, 100)
        total_percent += percent
        counted += 1
    return round(total_percent / counted) if counted > 0 else 0
 

async def get_task_completion_percent(session: AsyncSession, referral_ids: list[int]) -> int:
    if not referral_ids:
        return 0
    
    result = await session.execute(select(func.count()).select_from(Task))
    total_tasks = result.scalar_one()
    if total_tasks == 0:
        return 0
    
    total_percent = 0
    counted = 0

    for referral_id in referral_ids:
        completed_result = await session.execute(
            select(func.count()).select_from(TaskCompletion).where(TaskCompletion.user_id == referral_id)
        )
        completed = completed_result.scalar_one()

        percent = min((completed / total_tasks) * 100, 100)
        total_percent += percent
        counted += 1
    return round(total_percent / counted) if counted > 0 else 0

def get_banned_referral_count(referrals: list[User]) -> int:
    return sum(1 for r in referrals if r.is_banned)

async def get_referral_stats(session: AsyncSession, referrer_id: int) -> dict:
    referrals = await get_referrals(session, referrer_id)
    referral_ids = [r.id for r in referrals]

    return {
        "referral_count": len(referrals),
        "nested_referrals": await get_nested_referral_count(session, referral_ids),
        "bonus_percent": await get_bonus_claim_percent(session, referral_ids),
        "task_percent": await get_task_completion_percent(session, referral_ids),
        "banned_count": get_banned_referral_count(referrals),
    }

async def get_who_referred(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(
        select(Referral).where(Referral.referral_id == user_id)
    )
    referral = result.scalars().first()
    if referral:
        return await session.get(User, referral.referrer_id)
    return None