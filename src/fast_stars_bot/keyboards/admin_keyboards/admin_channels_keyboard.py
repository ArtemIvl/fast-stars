from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.models.channel import Channel


def manage_channels_keyboard(channels: list[Channel]) -> InlineKeyboardMarkup:
    if not channels:
        inline_keyboard = [
            [InlineKeyboardButton(text="Добавить канал", callback_data="add_channel")]
        ]
    else:
        inline_keyboard = [
            [
                InlineKeyboardButton(
                    text=f"🔗 Канал {ch.name}", callback_data=f"channel_{ch.id}"
                )
            ]
            for i, ch in enumerate(channels)
        ]
        inline_keyboard.extend(
            [
                [
                    InlineKeyboardButton(
                        text="Добавить канал", callback_data="add_channel"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Удалить канал", callback_data="remove_channel"
                    )
                ],
            ]
        )
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def channel_info_keyboard(channel: Channel) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Удалить канал", callback_data=f"del_channel_{channel.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="manage_channels"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def back_to_channels_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="manage_channels"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def delete_channels_keyboard(channels: list[Channel]) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"🔗 Канал {ch.name}", callback_data=f"del_channel_{ch.id}"
            )
        ]
        for ch in channels
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="manage_channels")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
