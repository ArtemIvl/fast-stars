from decimal import Decimal

from db.models.game_settings import GameSetting
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_game_setting(session: AsyncSession, key: str) -> Decimal:
    result = await session.execute(
        select(GameSetting.value).where(GameSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    if setting is None:
        raise ValueError(f"Setting '{key}' not found")
    return Decimal(setting)


async def update_game_setting(
    session: AsyncSession, key: str, new_value: Decimal
) -> None:
    result = await session.execute(select(GameSetting).where(GameSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = new_value
    else:
        raise ValueError(f"Setting '{key}' not found")
    await session.commit()
