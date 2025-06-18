from decimal import Decimal, InvalidOperation

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from keyboards.admin_keyboards import back_to_games_keyboard, manage_games_keyboard
from utils.basketball_requests import get_basketball_stats
from utils.cube_requests import get_cube_game_stats
from utils.daily_bonus_requests import bonus_claims_today, total_bonus_amount_claimed
from utils.deposit_requests import get_total_amount_deposited
from utils.game_settings_requests import get_game_setting, update_game_setting
from utils.slot_machine_requests import get_total_slot_spins, get_total_slot_winnings
from utils.vip_requests import get_all_vip_users
from utils.x2game_requests import get_or_create_stats


class AdminGameSettingsState(StatesGroup):
    waiting_for_value = State()


games_admin_router = Router()


@games_admin_router.callback_query(F.data == "manage_games")
async def manage_games_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    await state.clear()
    async with SessionLocal() as session:
        x2game_stats = await get_or_create_stats(session)
        total_bonus = await total_bonus_amount_claimed(session)
        bonus_today = await bonus_claims_today(session)
        x2_win_chance = await get_game_setting(session, "x2_win_chance")
        basketball_multiplier = await get_game_setting(session, "basketball_multiplier")
        cube_commission = await get_game_setting(session, "cube_commission")
        cube_game_stats = await get_cube_game_stats(session, cube_commission)
        basketball_stats = await get_basketball_stats(session, basketball_multiplier)
        total_vip_users = len(await get_all_vip_users(session))
        total_stars_deposited, total_ton_deposited = await get_total_amount_deposited(
            session
        )
        total_spins = await get_total_slot_spins(session)
        total_slot_winnings = await get_total_slot_winnings(session)

        text = (
            "<b>🎮 Статистика игр</b>\n\n"
            "🎲 <b>X2Game</b>:\n"
            f"• Выиграно: <code>{x2game_stats.won:.2f}⭐</code>\n"
            f"• Потеряно: <code>{x2game_stats.lost:.2f}⭐</code>\n"
            f"• Шанс: <b>{x2_win_chance}%</b>\n\n"
            "🏀 <b>Баскетбол</b>:\n"
            f"• Всего игр: <code>{basketball_stats[0]}</code>\n"
            f"• Выиграно: <code>{basketball_stats[1]:.2f}⭐</code>\n"
            f"• Потеряно: <code>{basketball_stats[2]:.2f}⭐</code>\n"
            f"• Множитель выигрыша: <b>X{basketball_multiplier}</b>\n\n"
            "🎲 <b>Кубики</b>:\n"
            f"• Всего игр: <code>{cube_game_stats[0]}</code>\n"
            f"• Выиграно: <code>{cube_game_stats[1]:.2f}⭐</code>\n"
            f"• Потеряно: <code>{cube_game_stats[2]:.2f}⭐</code>\n"
            f"• Комиссия бота: <code>{cube_game_stats[3]:.2f}⭐</code>\n"
            f"• Текущая комиссия: <b>{cube_commission}%</b>\n\n"
            "🎰 <b>Слот машина</b>:\n"
            f"• Всего спинов: <code>{total_spins}</code>\n"
            f"• Выиграно: <code>{total_slot_winnings}⭐</code>\n\n"
            f"Онлайн за сегодня: <code>{bonus_today}</code>\n"
            f"Всего бонусов получено: <code>{total_bonus:.2f}⭐</code>\n"
            f"Всего активных VIP: <code>{total_vip_users}</code>\n"
            f"Всего задоначено TON: <code>{total_ton_deposited:.3f} TON</code>\n"
            f"Всего получено за донат: <code>{total_stars_deposited}⭐</code>\n\n"
        )

        await callback.message.edit_text(
            text, parse_mode="HTML", reply_markup=manage_games_keyboard()
        )


@games_admin_router.callback_query(
    F.data.in_({"change_x2game", "change_basketball", "change_cube"})
)
async def start_setting_change(callback: types.CallbackQuery, state: FSMContext):
    setting_map = {
        "change_x2game": "x2_win_chance",
        "change_basketball": "basketball_multiplier",
        "change_cube": "cube_commission",
    }
    key = setting_map[callback.data]
    await state.set_state(AdminGameSettingsState.waiting_for_value)
    await state.update_data(setting_key=key)

    field_names = {
        "x2_win_chance": "шанс победы в X2Game (%)",
        "basketball_multiplier": "множитель победы в баскетболе (например, 1.5)",
        "cube_commission": "комиссию в кубиках (%)",
    }
    sent = await callback.message.edit_text(
        f"Введите новое значение для: <b>{field_names[key]}</b>",
        parse_mode="HTML",
        reply_markup=back_to_games_keyboard(),
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@games_admin_router.message(AdminGameSettingsState.waiting_for_value)
async def set_setting_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    try:
        value = Decimal(message.text.replace(",", "."))
        if value <= 0 or value > 100:
            sent = await message.answer(
                "Число должно быть больше 0 и не больше 100. Попробуйте снова.",
                reply_markup=back_to_games_keyboard(),
            )
            await state.update_data(last_bot_message_id=sent.message_id)
            return
    except InvalidOperation:
        sent = await message.answer(
            "Введите корректное число.", reply_markup=back_to_games_keyboard()
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        return

    key = data.get("setting_key")

    async with SessionLocal() as session:
        await update_game_setting(session, key, value)

    await message.answer(
        "✅ Настройка успешно обновлена.", reply_markup=back_to_games_keyboard()
    )
    await state.clear()
