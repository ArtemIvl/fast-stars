from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.promo_code import PromoCode, PromoActivation
from db.models.user import User
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

async def is_promo_code_unique(session: AsyncSession, code: str) -> bool:
    result = await session.execute(
        select(PromoCode).filter(PromoCode.code == code)
    )
    return result.scalars().first() is None

async def add_promo_code(session: AsyncSession, code: str, max_activations: int, reward: Decimal) -> None:
    promo_code = PromoCode(code=code, max_activations=max_activations, activations_left = max_activations, reward=reward)
    session.add(promo_code)
    await session.commit()

async def activate_promo(session: AsyncSession, user: User, code: str) -> tuple[bool, str | None, Decimal | None]:
    try:
        promo = await session.scalar(
            select(PromoCode)
            .where(PromoCode.code == code)
            .with_for_update()
        )

        if not promo or promo.activations_left <= 0:
            return False, "Промокод недействителен или уже использован.", None

        already_activated = await session.scalar(
            select(PromoActivation).filter_by(user_id=user.id, promo_code_id=promo.id)
        )
        if already_activated:
            return False, "Вы уже активировали этот промокод.", None

        promo.activations_left -= 1
        user.stars += promo.reward

        session.add(PromoActivation(user_id=user.id, promo_code_id=promo.id))
        await session.commit()

        return True, None, promo.reward

    except IntegrityError:
        await session.rollback()
        return False, "❌ Ошибка при активации промокода. Попробуйте позже.", None

async def get_promo_code_with_activations(session: AsyncSession, code: str) -> PromoCode | None:
    result = await session.execute(
        select(PromoCode)
        .options(selectinload(PromoCode.activations).selectinload(PromoActivation.user))
        .where(PromoCode.code == code)
    )
    return result.scalars().first()