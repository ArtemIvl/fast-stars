import asyncio

from aiogram import F, Router, types
from db.session import SessionLocal
from utils.daily_bonus_requests import claim_daily_bonus
from utils.user_requests import get_user_by_telegram_id

router = Router()


def register_daily_bonus_handlers(dp) -> None:
    dp.include_router(router)


@router.callback_query(F.data == "daily_bonus")
async def daily_bonus_callback(callback: types.CallbackQuery) -> None:
    async with SessionLocal() as session:
        telegram_id = callback.from_user.id
        user = await get_user_by_telegram_id(session, telegram_id)

        try:
            bonus = await claim_daily_bonus(session, user)
            await callback.answer(
                f"Вы получили {bonus}⭐️ за ежедневный бонус! 🎉\n\n"
                f"Баланс: {user.stars:.2f}⭐️",
                show_alert=True,
            )
        except ValueError:
            await callback.answer(
                "Вы уже получили бонус сегодня! Попробуйте завтра. ⏳", show_alert=True
            )

        message = await callback.message.answer(
            "Ежедневный бонус 🎁\n\n"
            "Каждый день ваш бонус увеличивается!\n\n"
            "• Сегодня: 0.1 ⭐️\n"
            "• Завтра: 0.2 ⭐️\n"
            "• Послезавтра: 0.3 ⭐️ и так далее.\n\n"
            "📅 За 15 дней можно собрать 12 ⭐️! Не пропускайте, чтобы получить максимум!"
        )

        await asyncio.sleep(10)
        await message.delete()
