from aiogram import Router
from filters.is_admin import IsAdmin

from .base_admin import base_admin_router
from .channel_admin import channel_admin_router
from .games_admin import games_admin_router
from .giveaway_admin import giveaway_admin_router
from .message_admin import message_admin_router
from .promo_admin import promo_admin_router
from .task_admin import task_admin_router
from .user_admin import user_admin_router
from .withdraw_admin import withdraw_admin_router


def register_admin_handlers(dp):
    admin_router = Router()
    admin_router.message.filter(IsAdmin())
    admin_router.callback_query.filter(IsAdmin())

    admin_router.include_router(base_admin_router)
    admin_router.include_router(channel_admin_router)
    admin_router.include_router(user_admin_router)
    admin_router.include_router(promo_admin_router)
    admin_router.include_router(task_admin_router)
    admin_router.include_router(games_admin_router)
    admin_router.include_router(message_admin_router)
    admin_router.include_router(withdraw_admin_router)
    admin_router.include_router(giveaway_admin_router)

    dp.include_router(admin_router)
