from aiogram import F, Router, types
from db.session import SessionLocal
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from decimal import Decimal
from keyboards.x2game_keyboard import x2game_keyboard, play_x2game_again
from keyboards.channels_keyboard import back_to_menu_keyboard
from utils.user_requests import get_user_by_telegram_id
from utils.x2game_requests import save_x2game_results
import random
from utils.game_settings_requests import get_game_setting

router = Router()

class X2GameState(StatesGroup):
    waiting_for_bet = State()
    waiting_for_choice = State()

def register_x2game_handlers(dp) -> None:
    dp.include_router(router)


@router.callback_query(F.data == "x2_game")
async def x2_game_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    telegram_id = callback.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
    await state.set_state(X2GameState.waiting_for_bet)
    await callback.message.edit_text(
        "🕹️ Добро пожаловать в игру, где удача решает всё!\n\n"
        "🔹 Как играть?\n\n"
        "1. Сделайте ставку — например, 0.5 ⭐️\n"
        "2. Выберите результат: чётное или нечётное число.\n"
        "3. Угадали? Ваш выигрыш — ×2 от ставки!\n"
        "4. Ошиблись? Ставка сгорает.\n\n"
        "🕹️ Испытайте свою удачу🪄\n\n"
        f"💰 Ваш баланс: {user.stars} ⭐️\n"
        "Введите количество звёздочек, на которое хотите сыграть: 👇🏻",
        reply_markup=back_to_menu_keyboard(),
    )

@router.message(X2GameState.waiting_for_bet, F.text.regexp(r"^\d+(\.\d+)?$"))
async def x2_game_bet_handler(message: types.Message, state: FSMContext) -> None:
    telegram_id = message.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)

        try:
            bet = Decimal(message.text)
        except Exception:
            return await message.answer("❌ Неверный формат ставки.")

        if bet <= 0:
            return await message.answer("❌ Ставка должна быть больше нуля.")
        if user.stars < bet:
            return await message.answer("❌ Недостаточно звёздочек для этой ставки.")

    await state.update_data(bet=bet)
    await state.set_state(X2GameState.waiting_for_choice)
    await message.answer(
        f"Какое число выпадет?",
        reply_markup=x2game_keyboard()
    )

@router.callback_query(X2GameState.waiting_for_choice, F.data.startswith("choice_"))
async def x2_game_result_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    telegram_id = callback.from_user.id
    user_choice = callback.data.split("_")[-1]

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)

        data = await state.get_data()
        bet = data.get("bet")
        if not bet:
            return await callback.message.answer("❌ Произошла ошибка. Начните заново.")
        
        win_chance = await get_game_setting(session, "x2_win_chance")
        if win_chance is None:
            win_chance = 30

        win_chance = float(win_chance)
        rand = random.uniform(0, 100)
        win = rand <= win_chance

        even_numbers = [2, 4, 6, 8, 10]
        odd_numbers = [1, 3, 5, 7, 9]

        if user_choice == "even":
            number = random.choice(even_numbers) if win else random.choice(odd_numbers)
        elif user_choice == "odd":
            number = random.choice(odd_numbers) if win else random.choice(even_numbers)

        await save_x2game_results(session, user, bet, win)

        if win:
            await callback.message.edit_text(f"Поздравляем, вы выиграли {bet * 2:.2f} ⭐️\nВыпало число {number}.", reply_markup=play_x2game_again())
        else:
            await callback.message.edit_text(f"К сожалению, вы проиграли :(\nВыпало число {number}.", reply_markup=play_x2game_again())

    await state.clear()