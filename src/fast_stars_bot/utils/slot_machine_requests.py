from decimal import Decimal
from sqlalchemy import select, func

from db.models.slot_machine_log import SlotMachineLog
from db.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


async def log_slot_machine_spin(
    session: AsyncSession, user: User, win_amount: Decimal
) -> None:
    log = SlotMachineLog(user_id=user.id, win_amount=win_amount)
    session.add(log)
    if win_amount > 0:
        user.stars += win_amount
    await session.commit()

async def get_total_slot_spins(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(SlotMachineLog))
    return result.scalar_one()

async def get_total_slot_winnings(session: AsyncSession) -> Decimal:
    result = await session.execute(select(func.sum(SlotMachineLog.win_amount)))
    total = result.scalar()
    return total if total is not None else Decimal(0)

