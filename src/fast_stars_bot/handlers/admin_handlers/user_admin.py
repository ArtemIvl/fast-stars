from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from keyboards.admin_keyboards import manage_users_keyboard, back_to_users_keyboard, back_to_withdrawal_keyboard, banned_users_keyboard, user_referrals_keyboard
from utils.user_requests import (add_admin, ban_user, get_user_by_telegram_id,
                                 remove_admin, unban_user, get_user_by_id, get_user_bonus_claim_percent, get_user_task_completion_percent, get_banned_users_page, get_banned_users_count)
from utils.vip_requests import is_user_vip
from utils.withdrawal_requests import get_completed_user_withdrawals
from utils.referral_requests import get_referral_stats, get_referrals, get_who_referred, get_referrals_page, get_referral_count
from db.models.withdrawal import WithdrawalStatus
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from decimal import Decimal

user_admin_router = Router()


class AdminActions(StatesGroup):
    view_user = State()
    ban_user = State()
    unban_user = State()
    add_admin = State()
    remove_admin = State()

async def generate_detailed_user_text(session: AsyncSession, user: User, withdrawal_id: int | None = None) -> tuple[str, types.InlineKeyboardMarkup]:
    is_vip = await is_user_vip(session, user.id)
    withdrawals = await get_completed_user_withdrawals(session, user.id)
    referral_stats = await get_referral_stats(session, user.id)
    user_bonus_claim_percent = await get_user_bonus_claim_percent(session, user.id)
    user_task_completion_percent = await get_user_task_completion_percent(session, user.id)
    referrals = await get_referrals(session, user.id)
    referrer = await get_who_referred(session, user.id)

    text = (
        f"<b>Пользователь:</b>\n\n"
        f"ID: {user.telegram_id}\n"
        f"Username: @{user.username}\n"
        f"Админ? {'Да' if user.is_admin else 'Нет'}\n"
        f"Заблокирован? {'Да' if user.is_banned else 'Нет'}\n"
        f"Дата регистрации: {user.reg_date}\n"
        f"Баланс: {user.stars:.2f}⭐\n"
        f"VIP? {'Да' if is_vip else 'Нет'}\n"
        f"Бонус дня: {user_bonus_claim_percent}%\n"
        f"Выполнение заданий: {user_task_completion_percent}%\n\n"
        f"<b>Рефералы:</b>\n"
    )

    if referrals:
        last_referrals = sorted(referrals, key=lambda x: x.reg_date, reverse=True)[:10]
        for idx, ref in enumerate(last_referrals, start=1):
            username = f"@{ref.username}" if ref.username else f"ID:{ref.telegram_id}"
            reg_date = f"{ref.reg_date}"
            text += f"{idx}. {username} - {reg_date}\n"

        text += (
            f"\n👥 Всего приглашено: {referral_stats['referral_count']}\n"
            f"↪️ Ими приглашено: {referral_stats['nested_referrals']}\n"
            f"📈 Сбор бонуса дня: {referral_stats['bonus_percent']}%\n"
            f"✅ Выполнение заданий: {referral_stats['task_percent']}%\n"
            f"🚫 Забанено: {referral_stats['banned_count']}\n\n"
            f"<b>Обработанные выводы:</b>\n"
        )
    else:
        text += (
            f"У пользователя нет рефералов.\n\n"
            f"<b>Обработанные выводы:</b>\n"
        )

    if withdrawals:
        approved = [w for w in withdrawals if w.status == WithdrawalStatus.APPROVED]
        rejected = [w for w in withdrawals if w.status == WithdrawalStatus.REJECTED]
        total_withdrawn = sum(w.stars for w in approved) if approved else Decimal("0.00")

        text += (
            f"Заявок одобрено: {len(approved)}\n"
            f"Заявок отклонено: {len(rejected)}\n"
            f"Всего выведено: {total_withdrawn:.2f}⭐\n\n"
        )
    else:
        text += "У пользователя ещё нет обработаных выводов.\n\n"

    if referrer:
        text += f"Пользователь был приглашён @{referrer.username} (ID: {referrer.telegram_id})"
    else:
        text += "Пользователь не был приглашён."

    if withdrawal_id:
        keyboard = back_to_withdrawal_keyboard(withdrawal_id)
    else:
        keyboard = back_to_users_keyboard()

    return text, keyboard

async def generate_user_referrals_text(session: AsyncSession, user: User, withdrawal_id: int, page: int = 1, per_page: int = 10) -> tuple[str, types.InlineKeyboardMarkup]:
    referrals = await get_referrals_page(session, user.id, page, per_page)
    referral_stats = await get_referral_stats(session, user.id)
    total_referrals = await get_referral_count(session, user.id)
    total_pages = (total_referrals + per_page - 1) // per_page 

    text = f"<b>Рефералы пользователя @{user.username} (страница {page} из {total_pages}):</b>\n\n"

    if referrals:
        for idx, ref in enumerate(referrals, start=(page - 1) * per_page + 1):
            username = f"@{ref.username}" if ref.username else f"ID:{ref.telegram_id}"
            reg_date = f"{ref.reg_date}"
            text += f"{idx}. {username} - {reg_date}\n"

        text += (
            f"\n👥 Всего приглашено: {referral_stats['referral_count']}\n"
            f"↪️ Ими приглашено: {referral_stats['nested_referrals']}\n"
            f"📈 Сбор бонуса дня: {referral_stats['bonus_percent']}%\n"
            f"✅ Выполнение заданий: {referral_stats['task_percent']}%\n"
            f"🚫 Забанено: {referral_stats['banned_count']}\n"
        )
    else:
        text += "У пользователя нет рефералов."

    kb = user_referrals_keyboard(user.id, withdrawal_id, page, total_pages)
    return text, kb

@user_admin_router.callback_query(F.data.startswith("referrals_page_"))
async def referrals_page_handler(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    _, _, user_id_str, withdrawal_id_str, page_str = parts
    user_id = int(user_id_str)
    withdrawal_id = int(withdrawal_id_str)
    page = int(page_str)

    async with SessionLocal() as session:
        user = await get_user_by_id(session, user_id)
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        text, kb = await generate_user_referrals_text(session, user, withdrawal_id, page=page)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await callback.answer()


@user_admin_router.callback_query(F.data.startswith("view_user_refs_"))
async def view_detailed_user_info(callback: types.CallbackQuery) -> None:
    user_id = int(callback.data.split("_")[3])
    withdrawal_id = int(callback.data.split("_")[4])
    async with SessionLocal() as session:
        user = await get_user_by_id(session, user_id)
        if user:
            text, keyboard = await generate_user_referrals_text(session, user, withdrawal_id)
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await callback.message.answer("Пользователь не найден.", reply_markup=back_to_users_keyboard())


@user_admin_router.callback_query(F.data == "manage_users")
async def manage_users_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Управление пользователями:", reply_markup=manage_users_keyboard()
    )


@user_admin_router.callback_query(F.data == "view_user")
async def view_user_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.view_user)
    sent = await callback.message.edit_text(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите посмотреть:",
        reply_markup=back_to_users_keyboard()
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.view_user, F.text.regexp(r"^\d+$"))
async def view_user_by_id(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    telegram_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user:
            text, keyboard = await generate_detailed_user_text(session, user)
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
            await state.clear()
        else:
            sent = await message.answer("Пользователь не найден. Попробуйте ещё раз:", reply_markup=back_to_users_keyboard())
            await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.callback_query(F.data == "ban_user")
async def ban_user_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.ban_user)
    sent = await callback.message.edit_text(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите забанить:",
        reply_markup=back_to_users_keyboard()
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.ban_user, F.text.regexp(r"^\d+$"))
async def ban_user_by_id(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if user.is_banned:
                await message.answer("Пользователь уже забанен.", reply_markup=back_to_users_keyboard())
                await state.clear()
                return
            await ban_user(session, user)
            await message.answer(f"Пользователь с ID {user_id} заблокирован.", reply_markup=back_to_users_keyboard())
            await state.clear()
        else:
            sent = await message.answer("Пользоатель не найден. Попробуйте ещё раз:", reply_markup=back_to_users_keyboard())
            await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.callback_query(F.data == "unban_user")
async def unban_user_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.unban_user)
    sent = await callback.message.edit_text(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите разбанить:",
        reply_markup=back_to_users_keyboard()
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.unban_user, F.text.regexp(r"^\d+$"))
async def unban_user_by_id(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if not user.is_banned:
                await message.answer("Пользователь не заблокирован.", reply_markup=back_to_users_keyboard())
                await state.clear()
                return
            await unban_user(session, user)
            await message.answer(f"Пользователь с ID {user_id} успешно разблокирован.", reply_markup=back_to_users_keyboard())
            await state.clear()
        else:
            sent = await message.answer("Пользователь не найден. Попробуйте ещё раз:", reply_markup=back_to_users_keyboard())
            await state.update_data(last_bot_message_id=sent.message_id)



@user_admin_router.callback_query(F.data == "add_admin")
async def add_admin_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.add_admin)
    sent = await callback.message.edit_text(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите сделать админом:",
        reply_markup=back_to_users_keyboard()
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.add_admin, F.text.regexp(r"^\d+$"))
async def make_user_admin(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if user.is_admin:
                await message.answer("Пользователь уже администратор.", reply_markup=back_to_users_keyboard())
                await state.clear()
                return
            await add_admin(session, user)
            await message.answer(f"Пользователь с ID {user_id} получил права администратора.", reply_markup=back_to_users_keyboard())
            await state.clear()
        else:
            sent = await message.answer("Пользователь не найден. Попробуйте ещё раз:", reply_markup=back_to_users_keyboard())
            await state.update_data(last_bot_message_id=sent.message_id)



@user_admin_router.callback_query(F.data == "remove_admin")
async def remove_admin_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.remove_admin)
    sent = await callback.message.edit_text(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите удалить из админов:",
        reply_markup=back_to_users_keyboard()
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.remove_admin, F.text.regexp(r"^\d+$"))
async def remove_user_admin(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if not user.is_admin:
                await message.answer("Пользователь не администратор.", reply_markup=back_to_users_keyboard())
                await state.clear()
                return
            await remove_admin(session, user)
            await message.answer(f"Пользователь с ID {user_id} был лишен прав администратора.", reply_markup=back_to_users_keyboard())
            await state.clear()
        else:
            sent = await message.answer("Пользователь не найден. Попробуйте ещё раз:", reply_markup=back_to_users_keyboard())
            await state.update_data(last_bot_message_id=sent.message_id)



def generate_banned_users_text(banned_users: list[User], page: int, pages: int, total: int, per_page: int = 10) -> tuple[str, types.InlineKeyboardMarkup | None]:
    text = "<b>🚫 Заблокированные пользователи:</b>\n\n"
    if total == 0:
        text += "Нет забаненных пользователей."
    else:
        start = (page - 1) * per_page
        for i, user in enumerate(banned_users, start + 1):
            username = f"@{user.username}" if user.username else "None"
            text += f"{i}. {username} | ID: <code>{user.telegram_id}</code>\n"

    kb = banned_users_keyboard(page, pages)
    return text, kb

@user_admin_router.callback_query(F.data == "view_banned_users")
async def view_banned_callback(callback: types.CallbackQuery) -> None:
    page = 1
    per_page = 10
    async with SessionLocal() as session:
        total = await get_banned_users_count(session)
        pages = (total + per_page - 1) // per_page
        banned_users = await get_banned_users_page(session, page, per_page)
        text, kb = generate_banned_users_text(banned_users, page, pages, total, per_page)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@user_admin_router.callback_query(F.data.startswith("banned_page_"))
async def handle_banned_page(callback: types.CallbackQuery) -> None:
    per_page = 10
    page = int(callback.data.split("_")[-1])
    async with SessionLocal() as session:
        total = await get_banned_users_count(session)
        pages = (total + per_page - 1) // per_page
        banned_users = await get_banned_users_page(session, page, per_page)
        text, kb = generate_banned_users_text(banned_users, page, pages, total, per_page)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()