from aiogram import F, Router, types
from db.session import SessionLocal
from utils.user_requests import get_user_by_telegram_id
from utils.referral_requests import get_referral_count, get_referral_stats
from keyboards.channels_keyboard import back_to_menu_keyboard


router = Router()

def register_invite_friend_handlers(dp) -> None:
    dp.include_router(router)

@router.callback_query(F.data == "invite_friend")
async def invite_friend_callback(callback: types.CallbackQuery) -> None:
    telegram_id = callback.from_user.id
    bot_username = (await callback.bot.me()).username

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        referral_link = f"https://t.me/{bot_username}?start={telegram_id}"

        referral_count = await get_referral_count(session, user.id)
        stats = await get_referral_stats(session, user.id)

        text = (
            f"Приглашайте друзей и получайте 4.0 ⭐️ STARS за каждого друга! ⭐️\n\n"
            f"Ваша ссылка:👉🏻 <code>{referral_link}</code>\n\n"
        )

        if not referral_count:
            text += "У вас нет рефералов.\n\n"
        else:
            text += (
                f"👥 Всего приглашено: {referral_count}\n\n"
                f"↪️ Ими приглашено: {stats['nested_referrals']}\n"
                f"📈 Сбор бонуса дня: {stats['bonus_percent']}%\n"
                f"✅ Выполнение заданий: {stats['task_percent']}%\n"
                f"🚫 Забанено: {stats['banned_count']}\n\n"
            )

        text += (
            "✅ Норма активности рефералов:\n"
            "❌ Не менее 10% по каждому показателю.\n\n"
            "❗️Минимальная активность для вывода ⭐️ за рефералов — 10% по каждому показателю.❗️"
        )

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_menu_keyboard())