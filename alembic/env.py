from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from src.fast_stars_bot.config.settings import settings
from src.fast_stars_bot.db.models.base import Base
from src.fast_stars_bot.db.models.basketball_log import BasketballLog
from src.fast_stars_bot.db.models.channel import Channel
from src.fast_stars_bot.db.models.cube_game import CubeGame
from src.fast_stars_bot.db.models.daily_bonus_claim import DailyBonusClaim
from src.fast_stars_bot.db.models.deposit import Deposit
from src.fast_stars_bot.db.models.game_settings import GameSetting
from src.fast_stars_bot.db.models.giveaway import Giveaway, GiveawayTicket
from src.fast_stars_bot.db.models.promo_code import PromoActivation, PromoCode
from src.fast_stars_bot.db.models.referral import Referral
from src.fast_stars_bot.db.models.slot_machine_log import SlotMachineLog
from src.fast_stars_bot.db.models.subscription_log import SubscriptionLog
from src.fast_stars_bot.db.models.task import Task, TaskCompletion
from src.fast_stars_bot.db.models.user import User
from src.fast_stars_bot.db.models.vip_subscription import VipSubscription
from src.fast_stars_bot.db.models.withdrawal import Withdrawal
from src.fast_stars_bot.db.models.x2game import X2Game

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
# config.set_main_option("sqlalchemy.url", settings.DB_URL)

if config.get_main_option("sqlalchemy.url") == "url":
    config.set_main_option("sqlalchemy.url", settings.DB_URL.replace("+asyncpg", ""))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
