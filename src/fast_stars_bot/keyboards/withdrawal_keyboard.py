from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def withdrawal_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Вывести звёзды ⭐️", callback_data="withdraw_stars"
            )
        ],
        [InlineKeyboardButton(text="Обменять ⭐️ на TON", callback_data="withdraw_ton")],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="profile"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def back_to_withdrawal_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="withdraw")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
