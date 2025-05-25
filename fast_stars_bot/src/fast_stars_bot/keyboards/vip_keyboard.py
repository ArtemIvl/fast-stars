from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def vip_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="💎 Купить VIP status", callback_data="buy_vip")]
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def vip_confirmation_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Подтвердить", callback_data="confirm_vip_purchase"
            )
        ]
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="vip_package")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def vip_info_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="profile")]]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
