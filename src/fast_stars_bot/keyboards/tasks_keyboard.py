from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.models.task import Task


def tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    inline_keyboard = []
    for task in tasks:
        # if task.requires_subscription:
        button = InlineKeyboardButton(
            text=f"{task.title} + {task.reward}⭐", url=task.url
        )
        # else:
        #     button = InlineKeyboardButton(
        #         text=f"{task.title} + {task.reward}⭐",
        #         callback_data=f"clicked_task_{task.id}",
        #     )
        inline_keyboard.append([button])

    inline_keyboard.append(
        [InlineKeyboardButton(text="✅ Проверить задания", callback_data="check_tasks")]
    )
    inline_keyboard.append(
        [
            InlineKeyboardButton(
                text="Добавить своё задание", url="https://t.me/derektor_tut1"
            )
        ]
    )
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# def no_required_subscription_task(task: Task) -> InlineKeyboardMarkup:
#     inline_keyboard = [
#         [
#             InlineKeyboardButton(
#                 text=f"Перейти к заданию",
#                 url=task.url,
#             )
#         ],
#         [
#             InlineKeyboardButton(text="🔙 К заданиям", callback_data="tasks")
#         ]
#     ]
#     return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def no_tasks_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Добавить своё задание", url="https://t.me/derektor_tut1"
            )
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
