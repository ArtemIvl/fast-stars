from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def manage_games_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Поменять Шанс X2Game", callback_data="change_x2game"
            )
        ],
        [
            InlineKeyboardButton(
                text="Поменять награду в Баскетболе", callback_data="change_basketball"
            )
        ],
        [
            InlineKeyboardButton(
                text="Поменять комиссию в кубиках", callback_data="change_cube"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад", callback_data="back_admin"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def back_to_games_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Назад", callback_data="manage_games"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)