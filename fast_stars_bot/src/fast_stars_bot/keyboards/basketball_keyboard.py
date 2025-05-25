from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def basketball_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Бросить за 1 ⭐", callback_data="basketball_bet_1"
            )
        ],
        [
            InlineKeyboardButton(
                text="Бросить за 2 ⭐", callback_data="basketball_bet_2"
            )
        ],
        [
            InlineKeyboardButton(
                text="Бросить за 5 ⭐", callback_data="basketball_bet_5"
            )
        ],
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def back_to_basketball_keyboard(bet) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="Бросить ещё раз!", callback_data=f"basketball_bet_{bet}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="basketball_game")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
