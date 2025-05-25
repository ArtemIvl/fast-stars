from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def audience_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Отправить всем", callback_data="audience_all"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отправить только VIP", callback_data="audience_vip"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад", callback_data="back_admin"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def time_choice_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Сейчас", callback_data="send_now"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
