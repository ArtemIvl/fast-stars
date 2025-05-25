from aiogram import F, Router, types
from db.session import SessionLocal
from utils.user_requests import get_user_by_id, get_user_task_completion_percent, get_user_bonus_claim_percent
from db.models.withdrawal import WithdrawalStatus
from utils.withdrawal_requests import get_all_pending_withdrawals, get_withdrawal_by_id, update_withdrawal_status, get_completed_user_withdrawals
from utils.referral_requests import get_referral_stats, get_referrals, get_who_referred
from utils.vip_requests import is_user_vip
from keyboards.admin_keyboards import withdraw_info_keyboard, pending_withdraw_keyboard, back_to_withdrawal_keyboard
from aiogram.exceptions import TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from db.models.withdrawal import Withdrawal
from decimal import Decimal

withdraw_admin_router = Router()

status_map = {
    WithdrawalStatus.PENDING: "⏳ В ожидании",
    WithdrawalStatus.APPROVED: "✅ Одобрено",
    WithdrawalStatus.REJECTED: "❌ Отклонено"
}

async def generate_detailed_withdraw_text(
    session: AsyncSession,
    withdrawal: Withdrawal,
    user: User
) -> str:
    is_vip = await is_user_vip(session, user.id)
    withdrawals = await get_completed_user_withdrawals(session, user.id)
    referral_stats = await get_referral_stats(session, user.id)
    user_bonus_claim_percent = await get_user_bonus_claim_percent(session, user.id)
    user_task_completion_percent = await get_user_task_completion_percent(session, user.id)
    referrals = await get_referrals(session, user.id)
    referrer = await get_who_referred(session, user.id)

    status_text = status_map.get(withdrawal.status, "Неизвестно")
    text = (
        f"<b>Информация о выводе:</b>\n\n"
        f"Заявка {withdrawal.id} от @{user.username} ({user.telegram_id}) {user.reg_date} на {withdrawal.stars}⭐\n"
        f"VIP? {'Да' if is_vip else 'Нет'}\n"
        f"Баланс: {user.stars:.2f}⭐\n"
        f"Бонус дня: {user_bonus_claim_percent}%\n"
        f"Выполнение заданий: {user_task_completion_percent}%\n"
    )

    if withdrawal.ton_address:
        text += f"TON Address: <code>{withdrawal.ton_address}</code>\n"

    text += f"\n<b>Рефералы:</b>\n"

    if referrals:
        sorted_referrals = sorted(referrals, key=lambda x: x.reg_date, reverse=True)[:10]
        for idx, user in enumerate(sorted_referrals, start=1):
            username = f"@{user.username}" if user.username else f"ID:{user.telegram_id}"
            reg_date = f"{user.reg_date}"
            text += f"{idx}. {username} - {reg_date}\n"
        text += (
            f"\n👥 Всего приглашено: {referral_stats['referral_count']}\n"
            f"↪️ Ими приглашено: {referral_stats['nested_referrals']}\n"
            f"📈 Сбор бонуса дня: {referral_stats['bonus_percent']}%\n"
            f"✅ Выполнение заданий: {referral_stats['task_percent']}%\n"
            f"🚫 Забанено: {referral_stats['banned_count']}\n\n"
            f"<b>Обработанные выводы:</b>\n\n"
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

    text += f"\n\nСтатус: {status_text}"

    return text

@withdraw_admin_router.callback_query(F.data == "manage_withdrawals")
async def manage_withdrawals_callback(callback: types.CallbackQuery) -> None:
    async with SessionLocal() as session:
        withdrawals = await get_all_pending_withdrawals(session)
        await callback.message.edit_text(
            "Список выводов:", reply_markup=pending_withdraw_keyboard(withdrawals, page=1)
        )

@withdraw_admin_router.callback_query(F.data.startswith("withdraw_page_"))
async def handle_withdraw_page(callback: types.CallbackQuery) -> None:
    page = int(callback.data.split("_")[-1])
    async with SessionLocal() as session:
        withdrawals = await get_all_pending_withdrawals(session)
        await callback.message.edit_text(
            "Список выводов:",
            reply_markup=pending_withdraw_keyboard(withdrawals, page=page)
        )
        await callback.answer()

@withdraw_admin_router.callback_query(F.data.startswith("withdraw_info_"))
async def withdraw_info_callback(callback: types.CallbackQuery) -> None:
    withdrawal_id = int(callback.data.split("_")[2])
    async with SessionLocal() as session:
        withdrawal = await get_withdrawal_by_id(session, withdrawal_id)
        user = await get_user_by_id(session, withdrawal.user_id)
        text = await generate_detailed_withdraw_text(session, withdrawal, user)

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=withdraw_info_keyboard(withdrawal.id, user.id),
        )

@withdraw_admin_router.callback_query(F.data.startswith("confirm_withdrawal_"))
async def confirm_withdrawal_callback(callback: types.CallbackQuery) -> None:
    withdrawal_id = int(callback.data.split("_")[2])
    async with SessionLocal() as session:
        await update_withdrawal_status(session, withdrawal_id, WithdrawalStatus.APPROVED)
        withdrawal = await get_withdrawal_by_id(session, withdrawal_id)
        user = await get_user_by_id(session, withdrawal.user_id)

        try:
            await callback.bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    "✅ <b>Ваша заявка на вывод одобрена!🫡</b>\n\n"
                    "💫 Скоро ваши звёзды поступят на ваш Telegram-аккаунт.\n\n"
                    "Когда получите звёзды, пожалуйста, поделитесь скриншотом с друзьями. "
                    "Расскажите им, что наш бот платит! 🚀🫂"
                ),
                parse_mode="HTML"
            )
        except TelegramForbiddenError:
            pass

        try:
            await callback.bot.send_message(
                chat_id=-1002436472086,
                text=f"@{user.username} вывел(-а) {withdrawal.stars} ⭐️"
            )
        except Exception as e:
            print(f"Ошибка отправки в канал: {e}")

        await callback.answer("Вывод подтвержден!", show_alert=True)
    withdrawals = await get_all_pending_withdrawals(session)
    updated_text = await generate_detailed_withdraw_text(session, withdrawal, user)
    await callback.message.edit_text(updated_text, parse_mode="HTML", reply_markup=None)
    await callback.message.answer(
        "Список выводов:", reply_markup=pending_withdraw_keyboard(withdrawals, page=1)
    )

@withdraw_admin_router.callback_query(F.data.startswith("reject_withdrawal_"))
async def decline_withdrawal_callback(callback: types.CallbackQuery) -> None:
    withdrawal_id = int(callback.data.split("_")[2])
    async with SessionLocal() as session:
        await update_withdrawal_status(session, withdrawal_id, WithdrawalStatus.REJECTED)
        withdrawal = await get_withdrawal_by_id(session, withdrawal_id)
        user = await get_user_by_id(session, withdrawal.user_id)

        try:
            await callback.bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    "❌ <b>Ваша заявка на вывод была отменена из-за нарушения правил нашего проекта.</b>\n\n"
                    "🔸 <b>Наш проект не выплачивает за:</b>\n"
                    "— накрутку рефералов,\n"
                    "— неактивных пользователей,\n"
                    "— ботов и фейковые аккаунты,\n"
                    "— вторые и третьи аккаунты одного человека.\n\n"
                    "👤 В нашем боте разрешено фармить только с одного аккаунта. Один человек — один аккаунт.\n\n"
                    "📊 Также активность ваших рефералов должна быть в норме!\n\n"
                    "📌 Зайдите в наше сообщество, ознакомьтесь с постами и внимательно прочитайте правила проекта, "
                    "чтобы избежать подобных ситуаций в будущем👇🏻\n\n"
                    "https://t.me/STARS_FAST_go"
                ),
                disable_web_page_preview=True,
                parse_mode="HTML"
            )
        except TelegramForbiddenError:
            pass

        await callback.answer("Вывод отклонен!", show_alert=True)
        withdrawals = await get_all_pending_withdrawals(session)
    updated_text = await generate_detailed_withdraw_text(session, withdrawal, user)
    await callback.message.edit_text(updated_text, parse_mode="HTML", reply_markup=None)
    await callback.message.answer(
        "Список выводов:", reply_markup=pending_withdraw_keyboard(withdrawals, page=1)
    )

@withdraw_admin_router.callback_query(F.data.startswith("all_withdrawals_"))
async def user_withdrawals_callback(callback: types.CallbackQuery) -> None:
    user_id = int(callback.data.split("_")[2])
    withdrawal_id = int(callback.data.split("_")[3])

    async with SessionLocal() as session:
        withdrawals = await get_completed_user_withdrawals(session, user_id)
        if not withdrawals:
            await callback.message.edit_text("У этого пользователя нет завершенных выводов.", reply_markup=back_to_withdrawal_keyboard(withdrawal_id))
            return
        
        text = "Завершенные выводы пользователя:\n\n"
        for withdrawal in withdrawals:
            status_text = status_map.get(withdrawal.status, "Неизвестно")
            text += (
                f"ID: {withdrawal.id}\n"
                f"Статус: {status_text}\n"
                f"Сумма: {withdrawal.stars}⭐\n"
            )

            if withdrawal.ton_address:
                text += f"Вывод в TON? Да\n"
            else:
                text += f"Вывод в TON? Нет\n"
            text+= f"Заявка создална: {withdrawal.created_at}\n\n"
        
    await callback.message.edit_text(
        text,
        reply_markup=back_to_withdrawal_keyboard(withdrawal_id),
    )