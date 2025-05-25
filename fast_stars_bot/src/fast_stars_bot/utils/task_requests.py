from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from db.models.task import Task, TaskCompletion
from db.models.user import User
from decimal import Decimal

async def add_task(session: AsyncSession, title: str, username: str, url: str, reward: Decimal, requires_subscription: bool) -> Task:
    new_task = Task(title=title, username=username, url=url, reward=reward, requires_subscription=requires_subscription)
    session.add(new_task)
    await session.commit()
    return new_task

async def get_all_tasks(session: AsyncSession) -> list[Task]:
    result = await session.execute(select(Task))
    tasks = result.scalars().all()
    return tasks

async def get_task_by_id(session: AsyncSession, task_id: int) -> Task | None:
    task = await session.get(Task, task_id)
    return task

async def get_task_completion_count(session: AsyncSession, task_id: int) -> int:
    result = await session.execute(
        select(func.count()).select_from(TaskCompletion).where(TaskCompletion.task_id == task_id)
    )
    return result.scalar_one()

async def delete_task(session: AsyncSession, task_id: int) -> None:
    task = await session.get(Task, task_id)
    if task:
        await session.execute(delete(TaskCompletion).where(TaskCompletion.task_id == task_id))
        await session.execute(delete(Task).where(Task.id == task_id))
        await session.commit()

async def is_task_completed(session: AsyncSession, user_id: int, task_id: int) -> bool:
    result = await session.execute(
        select(TaskCompletion).where(
            TaskCompletion.user_id == user_id,
            TaskCompletion.task_id == task_id
        )
    )
    return result.scalars().first() is not None

async def is_user_subscribed_to_task(bot: Bot, user_id: int, task: Task) -> bool:
    try:
        if "joinchat" in task.url or "+" in task.url:
            chat_id = task.username 
        else:
            url_part = task.url.strip().rstrip("/").split("/")[-1]
            chat_id = "@" + url_part

        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking subscription for user {user_id} in task {task.id}: {e}")
        return False

async def complete_task(session: AsyncSession, user: User, task: Task) -> None:
    task_completion = TaskCompletion(user_id=user.id, task_id=task.id)
    session.add(task_completion)
    user.stars += task.reward
    session.add(user)
    await session.commit()
