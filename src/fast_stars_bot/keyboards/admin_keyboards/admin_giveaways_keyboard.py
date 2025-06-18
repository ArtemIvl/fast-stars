from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.models.giveaway import Giveaway


def manage_giveaways_keyboard(giveaways: list[Giveaway]) -> InlineKeyboardMarkup:
    if not giveaways:
        pass
    else:
        inline_keyboard = [
            [
                InlineKeyboardButton(
                    text=f"{i+1}. {giveaway.name}",
                    callback_data=f"giveaway_{giveaway.id}",
                )
            ]
            for i, giveaway in enumerate(giveaways)
        ]
        inline_keyboard.extend(
            [
                [
                    InlineKeyboardButton(
                        text="Добавить розыгрыш", callback_data="add_giveaway"
                    )
                ],
            ]
        )
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def giveaway_info_keyboard(giveaway: Giveaway) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Удалить розыгрыш", callback_data=f"del_giveaway_{giveaway.id}"
            )
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="manage_giveaways")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def back_to_giveaways_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="manage_giveaways")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
