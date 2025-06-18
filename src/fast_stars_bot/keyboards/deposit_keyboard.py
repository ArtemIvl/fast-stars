from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def deposit_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="50 ⭐️ -- 0.4 TON",
                callback_data="deposit_50",
            )
        ],
        [
            InlineKeyboardButton(
                text="100 ⭐️ -- 0.75 TON",
                callback_data="deposit_100",
            )
        ],
        [
            InlineKeyboardButton(
                text="555 ⭐️ -- 4 TON",
                callback_data="deposit_555",
            )
        ],
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def confirm_payment_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="confirm_deposit")]
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
