from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from keyboards.admin_keyboards import manage_users_keyboard, back_to_users_keyboard, back_to_withdrawal_keyboard
from utils.user_requests import (add_admin, ban_user, get_user_by_telegram_id,
                                 remove_admin, unban_user, get_user_by_id, get_user_bonus_claim_percent, get_user_task_completion_percent)
from utils.vip_requests import is_user_vip
from utils.withdrawal_requests import get_completed_user_withdrawals
from utils.referral_requests import get_referral_stats, get_referrals, get_who_referred
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

async def generate_user_referrals_text(session: AsyncSession, user: User, withdrawal_id: int) -> tuple[str, types.InlineKeyboardMarkup]:
    referrals = await get_referrals(session, user.id)
    referral_stats = await get_referral_stats(session, user.id)

    text = f"<b>Рефералы пользователя @{user.username}:</b>\n\n"

    if referrals:
        sorted_refs = sorted(referrals, key=lambda x: x.reg_date, reverse=True)
        for idx, ref in enumerate(sorted_refs, start=1):
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

    return text, back_to_withdrawal_keyboard(withdrawal_id)

@user_admin_router.callback_query(F.data == "manage_users")
async def manage_users_callback(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        "Управление пользователями:", reply_markup=manage_users_keyboard()
    )


@user_admin_router.callback_query(F.data == "view_user")
async def view_user_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.view_user)
    await callback.message.answer(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите посмотреть:"
    )


@user_admin_router.message(AdminActions.view_user, F.text.regexp(r"^\d+$"))
async def view_user_by_id(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    telegram_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user:
            text, keyboard = await generate_detailed_user_text(session, user)
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.answer("User not found.", reply_markup=back_to_users_keyboard())

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


@user_admin_router.callback_query(F.data == "ban_user")
async def ban_user_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.ban_user)
    await callback.message.answer(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите забанить:"
    )


@user_admin_router.message(AdminActions.ban_user, F.text.regexp(r"^\d+$"))
async def ban_user_by_id(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if user.is_banned:
                await message.answer("User is already banned.", reply_markup=back_to_users_keyboard())
                return
            await ban_user(session, user)
            await message.answer(f"User with ID {user_id} has been blocked.", reply_markup=back_to_users_keyboard())
        else:
            await message.answer("User not found.", reply_markup=back_to_users_keyboard())


@user_admin_router.callback_query(F.data == "unban_user")
async def unban_user_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.unban_user)
    await callback.message.answer(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите разбанить:"
    )


@user_admin_router.message(AdminActions.unban_user, F.text.regexp(r"^\d+$"))
async def unban_user_by_id(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if not user.is_banned:
                await message.answer("User is not banned.", reply_markup=back_to_users_keyboard())
                return
            await unban_user(session, user)
            await message.answer(f"User with ID {user_id} has been unblocked.", reply_markup=back_to_users_keyboard())
        else:
            await message.answer("User not found.", reply_markup=back_to_users_keyboard())


@user_admin_router.callback_query(F.data == "add_admin")
async def add_admin_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.add_admin)
    await callback.message.answer(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите сделать админом:"
    )


@user_admin_router.message(AdminActions.add_admin, F.text.regexp(r"^\d+$"))
async def make_user_admin(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if user.is_admin:
                await message.answer("User is already an admin.", reply_markup=back_to_users_keyboard())
                return
            await add_admin(session, user)
            await message.answer(
                f"User with ID {user_id} has been granted admin rights.", reply_markup=back_to_users_keyboard()
            )
        else:
            await message.answer("User not found.", reply_markup=back_to_users_keyboard())


@user_admin_router.callback_query(F.data == "remove_admin")
async def remove_admin_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    await state.set_state(AdminActions.remove_admin)
    await callback.message.answer(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите удалить из админов:"
    )


@user_admin_router.message(AdminActions.remove_admin, F.text.regexp(r"^\d+$"))
async def remove_user_admin(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if not user.is_admin:
                await message.answer("User is not an admin.", reply_markup=back_to_users_keyboard())
                return
            await remove_admin(session, user)
            await message.answer(
                f"Admin rights for user with ID {user_id} have been revoked.", reply_markup=back_to_users_keyboard()
            )
        else:
            await message.answer("User not found.", reply_markup=back_to_users_keyboard())