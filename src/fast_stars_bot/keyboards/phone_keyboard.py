from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text="Пройти проверку🤝", request_contact=True)]]

    return ReplyKeyboardMarkup(
        keyboard=keyboard, one_time_keyboard=True, resize_keyboard=True
    )
