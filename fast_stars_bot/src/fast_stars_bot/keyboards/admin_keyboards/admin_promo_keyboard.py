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

def promo_pages_keyboard(promo_code: str, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    inline_keyboard = []
    if current_page > 1:
        inline_keyboard.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=f"promo_page_{promo_code}_{current_page - 1}"
            )
        )
    if current_page < total_pages:
        inline_keyboard.append(
            InlineKeyboardButton(
                text="➡️", callback_data=f"promo_page_{promo_code}_{current_page + 1}"
            )
        )
    if not inline_keyboard:
        return None
    
    return InlineKeyboardMarkup(inline_keyboard=[inline_keyboard])