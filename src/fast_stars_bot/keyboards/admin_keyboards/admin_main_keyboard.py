from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Управление каналами", callback_data="manage_channels"
            )
        ],
        [
            InlineKeyboardButton(
                text="Управление заданиями", callback_data="manage_tasks"
            )
        ],
        [
            InlineKeyboardButton(
                text="Управление пользователями", callback_data="manage_users"
            )
        ],
        [
            InlineKeyboardButton(
                text="Управление промокодами", callback_data="manage_promocodes"
            )
        ],
        [
            InlineKeyboardButton(
                text="Управление играми", callback_data="manage_games"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отправить сообщение", callback_data="send_message"
            )
        ],
        [
            InlineKeyboardButton(
                text="Управление выводами", callback_data="manage_withdrawals"
            )
        ],
        [
            InlineKeyboardButton(
                text="Управление розыгрышами", callback_data="manage_giveaways"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def admin_back_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Назад", callback_data="back_admin"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)