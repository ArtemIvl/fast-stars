from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def games_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="🏀Basketball Game🏀", callback_data="basketball_game"
            ),
            InlineKeyboardButton(text="🎲Cube Game🎲", callback_data="cube_game"),
        ],
        [
            InlineKeyboardButton(text="🎮X2 Game🎮", callback_data="x2_game"),
            InlineKeyboardButton(text="🎰Slot Machine🎰", callback_data="slot_machine"),
        ],
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def back_to_all_games_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="games")]]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
