from db.models.user import User
from sqlalchemy import desc, select, func
from db.models.daily_bonus_claim import DailyBonusClaim
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.task import TaskCompletion, Task
from datetime import date


def allowed_phone_number(phone: str) -> bool:
    return phone.startswith(
        tuple(["380", "48", "420", "7", "375", "39", "49", "31", "995"])
    )


async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> User | None:
    user = await session.execute(select(User).filter(User.telegram_id == telegram_id))
    if user:
        return user.scalars().first()
    
async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    user = await session.execute(select(User).filter(User.id == user_id))
    if user:
        return user.scalars().first()


async def add_user(
    session: AsyncSession, telegram_id: int, username: str, phone: str
) -> None:
    user = User(
        telegram_id=telegram_id,
        username=username,
        phone=phone,
    )
    session.add(user)
    await session.commit()


async def ban_user(session: AsyncSession, user: User) -> None:
    user.is_banned = True
    await session.commit()


async def unban_user(session: AsyncSession, user: User) -> None:
    user.is_banned = False
    await session.commit()


async def check_admin(session: AsyncSession, telegram_id: int) -> bool:
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        return user.is_admin
    else:
        return False


async def add_admin(session: AsyncSession, user: User) -> None:
    user.is_admin = True
    await session.commit()


async def remove_admin(session: AsyncSession, user: User) -> None:
    user.is_admin = False
    await session.commit()


async def get_top_10_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).order_by(desc(User.stars)).limit(10))
    return result.scalars().all()

async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return result.scalars().all()

async def get_all_admins(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).filter(User.is_admin == True))
    return result.scalars().all()

async def get_total_users(session: AsyncSession):
    query = select(func.count(User.id))
    result = await session.execute(query)
    total_users = result.scalar()
    return total_users

async def get_users_registered_today(session: AsyncSession):
    query = select(func.count(User.id)).where(User.reg_date == date.today())
    result = await session.execute(query)
    users_today = result.scalar()
    return users_today

async def get_user_bonus_claim_percent(session: AsyncSession, user_id: int) -> int:
    user_data = await session.execute(
        select(User.reg_date).where(User.id == user_id)
    )
    reg_date = user_data.scalar_one_or_none()
    if not reg_date:
        return 0

    days_since_reg = (date.today() - reg_date).days + 1 or 1

    claim_count_result = await session.execute(
        select(func.count()).where(DailyBonusClaim.user_id == user_id)
    )
    claim_count = claim_count_result.scalar_one()

    percent = min((claim_count / days_since_reg) * 100, 100)
    return round(percent)

async def get_user_task_completion_percent(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(select(func.count()).select_from(Task))
    total_tasks = result.scalar_one()
    if total_tasks == 0:
        return 0

    completed_result = await session.execute(
        select(func.count())
        .select_from(TaskCompletion)
        .where(TaskCompletion.user_id == user_id)
    )
    completed = completed_result.scalar_one()

    percent = min((completed / total_tasks) * 100, 100)
    return round(percent)