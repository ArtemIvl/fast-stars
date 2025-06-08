from db.session import SessionLocal
from utils.user_requests import get_all_users
from utils.vip_requests import get_all_vip_users
import asyncio
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNotFound, TelegramNetworkError, TelegramAPIError

async def send_broadcast(bot, data: dict) -> None:
    async with SessionLocal() as session:
        users = await get_all_vip_users(session) if data["audience"] == "vip" else await get_all_users(session)
        for user in users:
            try:
                if data.get("photo"):
                    await bot.send_photo(
                        chat_id=user.telegram_id,
                        photo=data["photo"],
                        caption=data.get("text"),
                        caption_entities=data.get("entities")
                    )
                else:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=data["text"],
                        entities=data.get("entities")
                    )
                await asyncio.sleep(0.05)
            except TelegramForbiddenError:
                print(f"Бот заблокирован пользователем {user.telegram_id}.")
                continue
            except TelegramNotFound:
                print(f"Чат с пользователем {user.telegram_id} не найден.")
                continue
            except TelegramNetworkError as e:
                print(f"Проблема с сетью при отправке пользователю {user.telegram_id}: {e}")
                await asyncio.sleep(1)
                continue
            except TelegramBadRequest as e:
                print(f"Некорректный запрос Telegram для {user.telegram_id}: {e}")
                continue
            except TelegramAPIError as e:
                print(f"Ошибка Telegram API для {user.telegram_id}: {e}")
                continue
            except Exception as e:
                print(f"Неизвестная ошибка при отправке пользователю {user.telegram_id}: {e}")
                continue

async def delayed_broadcast(bot, delay: float, data: dict) -> None:
    await asyncio.sleep(delay)
    await send_broadcast(bot, data)
