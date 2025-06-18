from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def channels_keyboard(channels: list) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text=f"🔗 Канал {i+1}", url=ch.link)]
        for i, ch in enumerate(channels)
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_subs")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back")]]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
