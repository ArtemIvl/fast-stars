from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def manage_promo_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Добавить промокод", callback_data="add_promo_code"
            )
        ],
        [
            InlineKeyboardButton(
                text="Посмотреть промокод", callback_data="view_promo_code"
            )
        ],
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def back_to_promo_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="manage_promocodes")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def promo_pages_keyboard(
    promo_code: str, current_page: int, total_pages: int
) -> InlineKeyboardMarkup:
    pagination_buttons = []
    if current_page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=f"promo_page_{promo_code}_{current_page - 1}"
            )
        )
    if current_page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="➡️", callback_data=f"promo_page_{promo_code}_{current_page + 1}"
            )
        )
    back_button = InlineKeyboardButton(
        text="🔙 Назад", callback_data="manage_promocodes"
    )
    return InlineKeyboardMarkup(inline_keyboard=[pagination_buttons, [back_button]])
