import asyncio

from db.session import SessionLocal
from utils.cube_requests import delete_old_canceled_games


async def cleanup_old_canceled_games(interval_seconds: int = 86400) -> None:
    while True:
        try:
            async with SessionLocal() as session:
                await delete_old_canceled_games(session)
        except Exception as e:
            print(f"[Cleanup Error] {e}")
        await asyncio.sleep(interval_seconds)
