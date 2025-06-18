from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def x2game_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Чётное",
                callback_data="choice_even",
            )
        ],
        [
            InlineKeyboardButton(
                text="Нечётное",
                callback_data="choice_odd",
            )
        ],
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="x2_game")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def play_x2game_again() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Сыграть ещё раз",
                callback_data="x2_game",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)