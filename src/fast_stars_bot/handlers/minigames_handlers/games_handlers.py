from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from keyboards.games_keyboard import games_keyboard

router = Router()


def register_games_handlers(dp) -> None:
    dp.include_router(router)


@router.callback_query(F.data == "games")
async def games_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    text = (
        "<b>🎮 Добро пожаловать в игры FastStars!</b>\n"
        "<blockquote>🏆 Проверь свою удачу и заработай больше звёзд⭐</blockquote>\n"
        "Выбирай игру, которая тебе больше по душе, и начинай прямо сейчас!👇🏻"
    )
    await callback.message.edit_text(
        text=text, parse_mode="HTML", reply_markup=games_keyboard()
    )
