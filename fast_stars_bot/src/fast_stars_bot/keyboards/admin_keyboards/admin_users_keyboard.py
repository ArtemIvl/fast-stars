from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def manage_users_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Посмотреть пользователя", callback_data="view_user"
            )
        ],
        [
            InlineKeyboardButton(
                text="Заблокировать пользователя", callback_data="ban_user"
            )
        ],
        [
            InlineKeyboardButton(
                text="Разблокировать пользователя", callback_data="unban_user"
            )
        ],
        [
            InlineKeyboardButton(
                text="Добавить администратора", callback_data="add_admin"
            )
        ],
        [
            InlineKeyboardButton(
                text="Удалить администратора", callback_data="remove_admin"
            )
        ],
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def back_to_users_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="manage_users"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
