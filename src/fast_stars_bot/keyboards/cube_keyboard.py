from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.session import SessionLocal
from utils.cube_requests import get_waiting_count, get_active_count
from decimal import Decimal


async def cube_keyboard() -> InlineKeyboardMarkup:
    rows = []
    async with SessionLocal() as session:
        for bet in (Decimal("1"), Decimal("5"), Decimal("10")):
            wait = await get_waiting_count(session, bet)
            act  = await get_active_count(session, bet)

            text = f"Ставка {bet} ⭐ | ⏳{wait} | 🎮{act}"
            rows.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"cube_bet_{bet}"
                )
            ])

    rows.append([
        InlineKeyboardButton(text="🔄 Обновить", callback_data="cube_refresh")
    ])
    rows.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="games")
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_cube_keyboard(game_id: int) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="🔙 Выйти", callback_data=f"cancel_game_{game_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def throw_cube_keyboard(game_id: int, player_number: int) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Бросить кубик 🎲",
                callback_data=f"throw_cube_{game_id}_{player_number}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def back_to_cube_menu_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="🔙 Вернуться к столам",
                callback_data="cube_game"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def end_game_keyboard(bet: Decimal) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="🔁 Сыграть ещё",
                callback_data=f"cube_bet_{bet}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Выйти",
                callback_data="cube_game"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)