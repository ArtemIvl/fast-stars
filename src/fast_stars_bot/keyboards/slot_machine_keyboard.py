from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def slot_machine_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="Купить 1 спин 🎰", callback_data="slot_machine_1")],
        [
            InlineKeyboardButton(
                text="Купить 5 спинов 🎰", callback_data="slot_machine_5"
            )
        ],
        [
            InlineKeyboardButton(
                text="Купить 10 спинов 🎰", callback_data="slot_machine_10"
            )
        ],
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="games")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def back_to_slot_machine_keyboard(spin) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Крутануть ещё раз!", callback_data=f"slot_machine_{spin}"
            )
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="slot_machine")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
