import asyncio
import logging

from aiogram import Bot, Dispatcher
from config.settings import settings
from handlers.admin_handlers import register_admin_handlers
from handlers.daily_bonus_handlers import register_daily_bonus_handlers
from handlers.deposit_handlers import register_deposit_handlers
from handlers.giveaway_handlers import register_giveaway_handlers
from handlers.invite_friend_handlers import register_invite_friend_handlers
from handlers.menu_handlers import register_menu_handlers
from handlers.minigames_handlers.basketball_handlers import register_basketball_handlers
from handlers.minigames_handlers.cube_handlers import register_cube_handlers
from handlers.minigames_handlers.games_handlers import register_games_handlers
from handlers.minigames_handlers.slot_machine_handlers import (
    register_slot_machine_settings,
)
from handlers.minigames_handlers.x2game_handlers import register_x2game_handlers
from handlers.profile_handlers import register_profile_handlers
from handlers.promo_handlers import register_promo_handlers
from handlers.start_handlers import register_start_handlers
from handlers.stats_handlers import register_stats_handlers
from handlers.task_handlers import register_task_handlers
from handlers.top_10_handlers import register_top_10_handlers
from handlers.vip_handlers import register_vip_handlers
from handlers.withdrawal_handlers import register_withdrawal_handlers
from middlewares.ban_check import BanCheckMiddleware
from middlewares.block_actions_while_playing import BlockActionsWhilePlayingMiddleware
from middlewares.logging import LoggingMiddleware
from middlewares.private_chat_only import PrivateChatOnlyMiddleware
from middlewares.subscription_required import SubscriptionRequiredMiddleware
from middlewares.username_tracking import UserTrackingMiddleware
from services.cleanup import cleanup_old_canceled_games
from services.giveaway_scheduler import setup_weekly_giveaway
from services.scheduler import setup_daily_reminders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("bot_timing.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# Убираем лишние логи от aiogram.event
logging.getLogger("aiogram.event").setLevel(logging.WARNING)

bot = Bot(token=settings.TOKEN)
dp = Dispatcher()

# Middleware
dp.message.middleware(PrivateChatOnlyMiddleware())
dp.callback_query.middleware(PrivateChatOnlyMiddleware())
dp.message.middleware(UserTrackingMiddleware())
dp.callback_query.middleware(UserTrackingMiddleware())
dp.message.middleware(SubscriptionRequiredMiddleware())
dp.callback_query.middleware(SubscriptionRequiredMiddleware())
dp.message.middleware(BanCheckMiddleware())
dp.callback_query.middleware(BanCheckMiddleware())
dp.message.middleware(BlockActionsWhilePlayingMiddleware())
dp.callback_query.middleware(BlockActionsWhilePlayingMiddleware())
dp.message.middleware(LoggingMiddleware())
dp.callback_query.middleware(LoggingMiddleware())

# Handlers
register_start_handlers(dp)
register_menu_handlers(dp)
register_profile_handlers(dp)
register_admin_handlers(dp)
register_daily_bonus_handlers(dp)
register_top_10_handlers(dp)
register_basketball_handlers(dp)
register_vip_handlers(dp)
register_promo_handlers(dp)
register_task_handlers(dp)
register_cube_handlers(dp)
register_invite_friend_handlers(dp)
register_x2game_handlers(dp)
register_withdrawal_handlers(dp)
register_deposit_handlers(dp)
register_stats_handlers(dp)
register_games_handlers(dp)
register_giveaway_handlers(dp)
register_slot_machine_settings(dp)


async def main():
    # Scheduler
    setup_daily_reminders(bot)
    # Giveaway scheduler
    setup_weekly_giveaway(bot)
    # Cancelled games cleanup
    asyncio.create_task(cleanup_old_canceled_games())
    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
