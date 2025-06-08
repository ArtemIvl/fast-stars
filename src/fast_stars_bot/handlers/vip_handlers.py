from aiogram import F, Router, types
from db.session import SessionLocal
from keyboards.vip_keyboard import (vip_confirmation_keyboard,
                                    vip_info_keyboard, vip_keyboard)
from utils.user_requests import get_user_by_telegram_id
from utils.vip_requests import (get_active_vip_subscription, grant_vip,
                                is_user_vip)

router = Router()


def register_vip_handlers(dp) -> None:
    dp.include_router(router)


@router.callback_query(F.data == "vip_package")
async def vip_info_callback(callback: types.CallbackQuery) -> None:
    telegram_id = callback.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        is_vip = await is_user_vip(session, user.id)

        if is_vip:
            active_vip = await get_active_vip_subscription(session, user.id)

            if active_vip:
                await callback.message.edit_text(
                    f"💎 У вас уже есть VIP-подписка!\n\n"
                    f"Дата начала подписки: {active_vip.start_date}\n"
                    f"Дата окончания подписки: {active_vip.end_date}\n\n"
                    f"Наслаждайтесь двойным бонусом дня, напоминаниями, уведомлениями о новых заданиях и приоритетным выводом средств!💎\n\n"
                    f"Спасибо, что вы с нами!",
                    reply_markup=vip_info_keyboard(),
                )
                return
        else:
            await callback.message.edit_text(
                "💎 <b>VIP-пакет — эксклюзивная подписка для самых активных!</b>\n"
                "Цена: <b>99,9 ⭐ на 30 дней</b>.\n\n"
                "<b>Преимущества VIP-пакета:</b>\n"
                " 1. ✨ X2 к бонусу дня — твоя ежедневная награда автоматически удваивается!\n"
                " 2. ⏰ Ежедневные напоминания — бот будет лично напоминать тебе собрать бонус дня.\n"
                " 3. 📢 Уведомления о новых заданиях — как только появляется новое задание, ты сразу получаешь личное сообщение.\n"
                "  🔹 Задания часто доступны всего на 20–60 минут — с VIP ты узнаешь о них первым!\n"
                " 4. 💰 Выплаты без очереди — приоритетная обработка заявок на вывод для всех VIP-пользователей.\n\n"
                "✅ <b>VIP-пакет = больше звёзд, больше заданий, быстрее выплаты!</b>\n"
                "Активируй прямо сейчас и получи максимум от бота!",
                parse_mode="HTML",
                reply_markup=vip_keyboard(),
            )


@router.callback_query(F.data == "buy_vip")
async def buy_vip_callback(callback: types.CallbackQuery) -> None:
    telegram_id = callback.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user.stars < 99.9:
            await callback.answer(
                "Недостаточно звезд для покупки VIP-пакета! ⭐️\n"
                "Для начала пополните баланс.",
                show_alert=True,
            )
            return

        is_vip = await is_user_vip(session, user.id)
        if is_vip:
            await callback.answer(
                "У вас уже есть VIP-подписка! 💎\n"
                "Вы сможете продлить её, как только ваша текущая подписка истечет.",
                show_alert=True,
            )
            return

        # Запрашиваем подтверждение перед покупкой VIP
        await callback.message.edit_text(
            "❓ Вы уверены, что хотите купить VIP статус за 99.9 ⭐️?\n"
            "После активации вы получите все привилегии VIP-пользователя.",
            reply_markup=vip_confirmation_keyboard(),
        )


@router.callback_query(F.data == "confirm_vip_purchase")
async def confirm_vip_purchase_callback(callback: types.CallbackQuery) -> None:
    telegram_id = callback.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        await grant_vip(session, user)

        await callback.message.answer(
            "✅ Поздравляем! Вы успешно приобрели VIP статус!\n"
            "Теперь вы можете наслаждаться всеми привилегиями VIP-пользователя!\n\n",
            reply_markup=vip_info_keyboard(),
        )
