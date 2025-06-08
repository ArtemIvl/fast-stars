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
        [
            InlineKeyboardButton(
                text="Посмотреть всех заблокированных пользователей", callback_data="view_banned_users"
            )
        ]
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

def banned_users_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup | None:
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=f"banned_page_{page - 1}"
            )
        )
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="➡️", callback_data=f"banned_page_{page + 1}"
            )
        )
    back_button = InlineKeyboardButton(
        text="🔙 Назад", callback_data="manage_users"
    )
    return InlineKeyboardMarkup(inline_keyboard=[pagination_buttons, [back_button]])

def user_referrals_keyboard(user_id: int, withdrawal_id: int, page: int, total_pages: int) -> InlineKeyboardMarkup | None:
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=f"referrals_page_{user_id}_{withdrawal_id}_{page - 1}"
            )
        )
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="➡️", callback_data=f"referrals_page_{user_id}_{withdrawal_id}_{page + 1}"
            )
        )
    back_button = InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=f"withdraw_info_{withdrawal_id}"
    )
    return InlineKeyboardMarkup(inline_keyboard=[pagination_buttons, [back_button]])
