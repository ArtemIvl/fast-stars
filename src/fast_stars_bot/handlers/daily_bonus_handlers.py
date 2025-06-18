import asyncio

from aiogram import F, Router, types
from db.session import SessionLocal
from utils.daily_bonus_requests import claim_daily_bonus
from utils.user_requests import get_user_by_telegram_id

router = Router()


def register_daily_bonus_handlers(dp) -> None:
    dp.include_router(router)


async def delete_later(message: types.Message, delay: int = 10):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


@router.callback_query(F.data == "daily_bonus")
async def daily_bonus_callback(callback: types.CallbackQuery) -> None:
    telegram_id = callback.from_user.id

    async with SessionLocal() as session:
        try:
            user = await get_user_by_telegram_id(session, telegram_id)
            if not user:
                await callback.answer("Пользователь не найден.", show_alert=True)
                return
            
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
        except Exception as e:
            await callback.answer("Ошибка. Попробуйте позже.", show_alert=True)
            return

        message = await callback.message.answer(
            "Ежедневный бонус 🎁\n\n"
            "Каждый день ваш бонус увеличивается!\n\n"
            "• Сегодня: 0.1 ⭐️\n"
            "• Завтра: 0.2 ⭐️\n"
            "• Послезавтра: 0.3 ⭐️ и так далее.\n\n"
            "📅 За 15 дней можно собрать 12 ⭐️! Не пропускайте, чтобы получить максимум!"
        )

        asyncio.create_task(delete_later(message))