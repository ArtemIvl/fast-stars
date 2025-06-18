from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.models.task import Task


def manage_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    if not tasks:
        inline_keyboard = [
            [InlineKeyboardButton(text="Добавить задание", callback_data="add_task")]
        ]
    else:
        inline_keyboard = [
            [
                InlineKeyboardButton(
                    text=f"Задание {task.title}", callback_data=f"task_{task.id}"
                )
            ]
            for i, task in enumerate(tasks)
        ]
        inline_keyboard.extend(
            [
                [
                    InlineKeyboardButton(
                        text="Добавить задание", callback_data="add_task"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Удалить задание", callback_data="delete_task"
                    )
                ],
            ]
        )
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def task_info_keyboard(task: Task) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Удалить задание", callback_data=f"del_task_{task.id}"
            )
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="manage_tasks")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def delete_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"Задание {task.title}", callback_data=f"del_task_{task.id}"
            )
        ]
        for task in tasks
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="manage_tasks")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def back_to_tasks_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="manage_tasks")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
