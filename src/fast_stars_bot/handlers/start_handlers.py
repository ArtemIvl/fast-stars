from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
import asyncio
from db.session import SessionLocal
from keyboards.menu_keyboard import menu_keyboard, menu_button_keyboard
from keyboards.phone_keyboard import get_phone_keyboard
from utils.channel_requests import get_all_channels
from utils.subscription_requests import (is_user_subscribed_to_all,
                                         reward_user_for_subscription)
from utils.user_requests import (add_user, allowed_phone_number,
                                 get_user_by_telegram_id, unban_user)
from utils.referral_requests import (create_referral, has_referral, reward_for_referral)
from aiogram.exceptions import TelegramForbiddenError

router = Router()

def register_start_handlers(dp) -> None:
    dp.include_router(router)


async def send_verification_prompt(message: types.Message) -> None:
    try:
        await message.answer(
            "<b>Пройдите проверку на бота 👇🏻</b>\n\n"
            "Чтобы избежать массовой накрутки со стороны нечестных пользователей, мы вынуждены установить данную проверку. 🤝 \n\n"
            "<b>Спасибо за понимание! 🫂</b>",
            parse_mode="HTML",
            reply_markup=get_phone_keyboard(),
        )
    except TelegramForbiddenError:
        print(f"❌ Бот заблокирован пользователем {message.from_user.id}")

async def delete_message_after_delay(bot, chat_id, message_id, delay=30):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")


@router.message(F.text.startswith("/start"))
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    telegram_id = message.from_user.id
    username = message.from_user.username or "anonymous"
    referrer_id = None

    parts = message.text.split()
    if len(parts) > 1:
        try:
            referrer_id = int(parts[1])
        except ValueError:
            pass

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if not user:
            await state.set_data({
                    "telegram_id": telegram_id,
                    "username": username,
                    "referrer_id": referrer_id,
                })
            await send_verification_prompt(message)
        else:
            channels = await get_all_channels(session)
            await reward_user_for_subscription(session, message.bot, user, channels)

            await message.answer("Добро пожаловать!", reply_markup=menu_button_keyboard())
            await message.answer(
                    "<b>Чтобы получить больше ⭐️, выполняйте задания и приглашайте друзей!👥\n\n"
                    "‼️ За накрутку рефералов — БАН без выплат! ‼️\n\n"
                    f"Баланс: {user.stars:.2f}⭐️</b>",
                    parse_mode="HTML",
                    reply_markup=menu_keyboard(),
                )


@router.message(F.contact)
async def handle_contact(message: types.Message, state: FSMContext) -> None:
    if message.from_user.id != message.contact.user_id:
        await message.answer("Поделитесь *своим* номером телефона.", parse_mode="Markdown")
        return

    phone = message.contact.phone_number
    if not allowed_phone_number(phone):
        await message.answer("К сожалению, наш бот не доступен для вашего региона.")
        return

    data = await state.get_data()
    telegram_id = data.get("telegram_id", message.from_user.id)
    username = data.get("username", message.from_user.username)
    referrer_id = data.get("referrer_id")

    if not username:
        await message.answer("❗Чтобы пользоваться ботом, добавьте username в настройках Telegram и нажмите /start.")
        return

    async with SessionLocal() as session:
        await add_user(session, telegram_id, username, phone)
        user = await get_user_by_telegram_id(session, telegram_id)
        channels = await get_all_channels(session)
        await reward_user_for_subscription(session, message.bot, user, channels)

        if referrer_id and not await has_referral(session, user.id):
            referrer = await get_user_by_telegram_id(session, referrer_id)
            if referrer:
                await create_referral(session, user.id, referrer.id)
                await reward_for_referral(session, referrer)

                try:
                    sent = await message.bot.send_message(
                        chat_id=referrer.telegram_id,
                        text=f"🎉 У вас новый реферал — @{user.username or 'пользователь'}!\nВы получили 4.0 ⭐️"
                    )
                    asyncio.create_task(delete_message_after_delay(message.bot, referrer.telegram_id, sent.message_id))
                except Exception as e:
                    print(f"Не удалось отправить сообщение пригласившему: {e}")
        await message.answer("Добро пожаловать!", reply_markup=menu_button_keyboard())
        await message.answer(
                "<b>Чтобы получить больше ⭐️, выполняйте задания и приглашайте друзей!👥\n\n"
                "‼️ За накрутку рефералов — БАН без выплат! ‼️\n\n"
                f"Баланс: {user.stars:.2f}⭐️</b>",
                parse_mode="HTML",
                reply_markup=menu_keyboard(),
            )
        

@router.callback_query(F.data == "check_subs")
async def check_subs_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    telegram_id = callback.from_user.id
    username = callback.from_user.username or "anonymous"

    async with SessionLocal() as session:
        channels = await get_all_channels(session)
        if not await is_user_subscribed_to_all(callback.bot, telegram_id, channels):
            await callback.answer("❗Вы ещё не подписались на все каналы.", show_alert=True)
            return
        
        user = await get_user_by_telegram_id(session, telegram_id)

        if user:
            await reward_user_for_subscription(session, callback.bot, user, channels)
            await callback.message.edit_text(
                "<b>Чтобы получить больше ⭐️, выполняйте задания и приглашайте друзей!👥\n\n"
                "‼️ За накрутку рефералов — БАН без выплат! ‼️\n\n"
                f"Баланс: {user.stars:.2f}⭐️</b>",
                parse_mode="HTML",
                reply_markup=menu_keyboard(),
            )
        else:
            old_data = await state.get_data()
            await state.update_data({
                "telegram_id": telegram_id,
                "username": username,
                "referrer_id": old_data.get("referrer_id")
            })
            await callback.message.edit_text("✅ Спасибо за подписку!")
            await send_verification_prompt(callback.message)

@router.pre_checkout_query(lambda q: True)
async def pre_checkout_query_handler(pre_checkout_query: types.PreCheckoutQuery) -> None:
    await pre_checkout_query.bot.answer_pre_checkout_query(
        pre_checkout_query.id,
        ok=True,
    )
    
@router.message(F.successful_payment, F.successful_payment.invoice_payload.startswith("unban:"))
async def handle_unban_payment(message: types.Message):
    telegram_id = message.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user and user.is_banned:
            await unban_user(session, user)
            await message.answer("✅ Вы успешно разблокированы. Добро пожаловать обратно!")