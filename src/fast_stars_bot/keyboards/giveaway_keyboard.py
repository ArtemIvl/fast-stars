from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.models.giveaway import Giveaway


def giveaways_keyboard(giveaways: list[Giveaway]) -> InlineKeyboardMarkup:
    if not giveaways:
        pass
    else:
        inline_keyboard = [
            [
                InlineKeyboardButton(
                    text=f"{i+1}. {giveaway.name}",
                    callback_data=f"view_giveaway_{giveaway.id}",
                )
            ]
            for i, giveaway in enumerate(giveaways)
        ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def giveaway_tickets_keyboard(giveaway: Giveaway) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="1 🎟", callback_data=f"buy_tickets_{giveaway.id}_1"
            )
        ],
        [
            InlineKeyboardButton(
                text="2 🎟", callback_data=f"buy_tickets_{giveaway.id}_2"
            )
        ],
        [
            InlineKeyboardButton(
                text="5 🎟", callback_data=f"buy_tickets_{giveaway.id}_5"
            )
        ],
        [
            InlineKeyboardButton(
                text="10 🎟", callback_data=f"buy_tickets_{giveaway.id}_10"
            )
        ],
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="giveaways")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
