from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def menu_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text="💼 Мой профиль 💼", callback_data="profile"),
        ],
        [
            InlineKeyboardButton(text="🧩 Задания 🧩", callback_data="tasks"),
        ],
        [
            InlineKeyboardButton(
                text="🫂 Пригласить друга", callback_data="invite_friend"
            ),
            InlineKeyboardButton(text="🏆 Топ-10", callback_data="top_10"),
        ],
        [
            InlineKeyboardButton(text="🎁 Бонус дня", callback_data="daily_bonus"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
        ],
        [
            InlineKeyboardButton(text="🏀 Basketball Game", callback_data="basketball_game"),
            InlineKeyboardButton(text="🎲 Cube Game", callback_data="cube_game"),
        ],
        [
            InlineKeyboardButton(text="🎮X2 Game🎮", callback_data="x2_game")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def menu_button_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text="⭐️ Меню")]]

    return ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, is_persistent=True
    )
