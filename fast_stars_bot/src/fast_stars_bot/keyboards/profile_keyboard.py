from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def profile_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text="🏆 VIP-пакет 🏆", callback_data="vip_package")
        ],
        [
            InlineKeyboardButton(text="📲 Промокод", callback_data="promo_code"),
            InlineKeyboardButton(text="📤 Вывод", callback_data="withdraw"),
        ],
        [
            InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="deposit")
        ],
        [
            InlineKeyboardButton(text="📤 Чат выплат", url="https://t.me/+eNoPiyYDVYszZDZi")
        ],
        [
            InlineKeyboardButton(text="👥 Наш Канал", url="https://t.me/+VtYfvlpxmQJkNGMy"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def back_to_profile_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
