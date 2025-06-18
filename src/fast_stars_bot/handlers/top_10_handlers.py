from aiogram import F, Router, types
from db.session import SessionLocal
from keyboards.channels_keyboard import back_to_menu_keyboard
from utils.user_requests import get_top_10_users

router = Router()


def register_top_10_handlers(dp) -> None:
    dp.include_router(router)


@router.callback_query(F.data == "top_10")
async def top_10_callback(callback: types.CallbackQuery) -> None:
    async with SessionLocal() as session:
        top_users = await get_top_10_users(session)

    medals = ["🥇", "🥈", "🥉"]
    lines = ["<b>Топ-10 пользователей по звёздному балансу ⭐️</b>\n"]

    for idx, user in enumerate(top_users, start=1):
        username = f"@{user.username}" if user.username else f"ID:{user.telegram_id}"
        prefix = medals[idx - 1] if idx <= 3 else f"{idx})"
        lines.append(f"{prefix} {username} — {user.stars:.2f}⭐️")

    text = "\n".join(lines)

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=back_to_menu_keyboard()
    )
