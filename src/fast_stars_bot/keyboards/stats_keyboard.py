from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def stats_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="👮🏿‍♂️ Администратор", url="https://t.me/derektor_tut1"
            )
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
