from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.promo_code import PromoCode, PromoActivation
from db.models.user import User
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from utils.user_requests import ban_user, get_all_admins
from aiogram import Bot
import redis.asyncio as redis

# Redis config
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
LOCK_TTL = 5  # сек
VIP_CHAT_ID = -1002628175095
ACTIVATION_KEY = "promo_activated:{code}:{user_id}"

async def is_promo_code_unique(session: AsyncSession, code: str) -> bool:
    result = await session.execute(
        select(PromoCode).filter(PromoCode.code == code)
    )
    return result.scalars().first() is None

async def add_promo_code(session: AsyncSession, code: str, max_activations: int, is_vip: bool, reward: Decimal) -> None:
    promo_code = PromoCode(code=code, max_activations=max_activations, activations_left = max_activations, is_vip=is_vip, reward=reward)
    session.add(promo_code)
    await session.commit()

async def is_user_in_chat(bot: Bot, user_id: int, chat_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

async def activate_promo(session: AsyncSession, user: User, code: str, bot: Bot) -> tuple[bool, str | None, Decimal | None]:
    key = ACTIVATION_KEY.format(code=code, user_id=user.id)
    if await redis_client.get(key):
        return False, "Вы уже активировали этот промокод.", None

    # Лочим промокод, чтобы избежать гонки
    lock = redis_client.lock(f"promo_lock:{code}", timeout=LOCK_TTL)
    async with lock:
        promo = await session.scalar(select(PromoCode).where(PromoCode.code == code))
        if not promo or promo.activations_left <= 0:
            return False, "Промокод недействителен или уже использован.", None

        already = await session.scalar(
            select(PromoActivation).filter_by(user_id=user.id, promo_code_id=promo.id)
        )
        if already:
            await redis_client.set(key, "1", ex=86400)
            return False, "Вы уже активировали этот промокод.", None
        
        if promo.is_vip:
            is_vip = await is_user_in_chat(bot, user.telegram_id, VIP_CHAT_ID)
            if not is_vip:
                await ban_user(session, user)
                admins = await get_all_admins(session)
                await bot.send_message(
                    user.telegram_id,
                    text=f"🚫 Вы были забанены за попытку использовать VIP промокод без доступа.\n"
                    f"Чтобы вернуть доступ к боту, нажмите /start и следуйте инструкции."
                )
                for admin in admins:
                    await bot.send_message(
                        admin.telegram_id,
                        text=f"{user.username} был забанен за ввод вип промо.",
                    )
                return False, "Забанен за попытку использования VIP промо.", None

        # Активируем
        promo.activations_left -= 1
        user.stars += promo.reward
        session.add(PromoActivation(user_id=user.id, promo_code_id=promo.id))
        await session.commit()

        await redis_client.set(key, "1", ex=86400)
        return True, None, promo.reward
    
async def get_promo_code(session: AsyncSession, code: str) -> PromoCode | None:
    result = await session.execute(
        select(PromoCode)
        .where(PromoCode.code == code)
    )
    return result.scalars().first()

async def get_promo_activations_page(session: AsyncSession, promo_code_id: int, page: int = 1, per_page: int = 10) -> list [PromoActivation]:
    offset = (page - 1) * per_page
    result = await session.execute(
        select(PromoActivation)
        .options(selectinload(PromoActivation.user))
        .where(PromoActivation.promo_code_id == promo_code_id)
        .offset(offset)
        .limit(per_page)
    )
    return result.scalars().all()