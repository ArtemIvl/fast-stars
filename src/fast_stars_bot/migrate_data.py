from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
from datetime import datetime, date

from db.models.channel import Channel
from db.models.daily_bonus_claim import DailyBonusClaim
from db.models.subscription_log import SubscriptionLog
from db.models.user import User
from db.models.task import Task, TaskCompletion
from db.models.promo_code import PromoCode, PromoActivation
from db.models.referral import Referral
from db.models.x2game import X2Game
from db.models.withdrawal import Withdrawal, WithdrawalStatus
from db.models.vip_subscription import VipSubscription
from db.models.game_settings import GameSetting
from db.models.deposit import Deposit, DepositStatus
from db.models.cube_game import CubeGame
from db.models.basketball_log import BasketballLog
from db.models.base import Base

sqlite_engine = create_engine("sqlite:///db.db")
Base.metadata.create_all(bind=sqlite_engine)
SessionLocal = sessionmaker(bind=sqlite_engine)
sqlite_conn = sqlite_engine.raw_connection()
sqlite_cursor = sqlite_conn.cursor()

pg_engine = create_engine("postgresql://fstars_user:tgstars123@localhost:5432/fstars_db")
SessionPG = sessionmaker(bind=pg_engine)
pg_session = SessionPG()

def clear_tables():
    tables = [
        "withdrawals", "x2game", "subscription_logs", "referrals", "promo_activations", "promo_codes",
        "task_completions", "tasks", "daily_bonus_claims", "channels", "users"
    ]
    for table in tables:
        pg_session.execute(text(f"TRUNCATE {table} RESTART IDENTITY CASCADE;"))
    pg_session.commit()

def bulk_insert(objects, table_name):
    if not objects:
        return
    pg_session.bulk_save_objects(objects)
    pg_session.flush()
    if table_name == "x2game":
        pass
    else:
        pg_session.execute(text(
            f"SELECT setval(pg_get_serial_sequence(:table, 'id'), (SELECT MAX(id) FROM {table_name}))"
        ), {"table": table_name})
    pg_session.commit()

def migrate_users():
    sqlite_cursor.execute("SELECT id, telegram_id, phone, stars, reg_date, bonuses_streak, is_banned FROM user")
    users = []
    for row in sqlite_cursor.fetchall():
        id_, telegram_id, phone, stars, reg_date, _, is_banned = row
        reg_date = datetime.strptime(reg_date, "%Y-%m-%d").date() if reg_date else None
        users.append(User(
            id=id_,
            telegram_id=telegram_id,
            phone=phone,
            stars=Decimal(stars),
            reg_date=reg_date,
            is_banned=bool(is_banned),
            is_admin=False,
            username=None
        ))
    bulk_insert(users, "users")

def migrate_channels():
    sqlite_cursor.execute("SELECT id, name, url, username FROM channel")
    channels = [
        Channel(id=id_, name=name, link=url, username=username)
        for id_, name, url, username in sqlite_cursor.fetchall()
    ]
    bulk_insert(channels, "channels")

def migrate_daily_bonus_claims():
    existing_user_ids = set(pg_session.scalars(select(User.id)).all())

    sqlite_cursor.execute("SELECT id, user_id, stars, date FROM daily")
    records = sqlite_cursor.fetchall()

    valid_claims = [
        DailyBonusClaim(
            id=id_, user_id=user_id,
            bonus_amount=Decimal(stars),
            claim_date=datetime.strptime(date_str, "%Y-%m-%d").date(),
            streak=0
        )
        for id_, user_id, stars, date_str in records
        if user_id in existing_user_ids
    ]

    bulk_insert(valid_claims, "daily_bonus_claims")

def migrate_tasks():
    sqlite_cursor.execute("SELECT id, name, url, username, 'check' FROM task")
    tasks = [
        Task(
            id=id_, title=name, url=url,
            reward=Decimal("0.00"),
            requires_subscription=bool(check)
        )
        for id_, name, url, _, check in sqlite_cursor.fetchall()
    ]
    bulk_insert(tasks, "tasks")


def migrate_task_completions():
    existing_user_ids = set(pg_session.scalars(select(User.id)).all())
    sqlite_cursor.execute("SELECT id, user_id, task_id FROM completed")
    records = sqlite_cursor.fetchall()
    valid_task_completions = [
        TaskCompletion(id=id_, user_id=user_id, task_id=task_id)
        for id_, user_id, task_id in records
        if user_id in existing_user_ids
    ]
    bulk_insert(valid_task_completions, "task_completions")

def migrate_promo_codes():
    sqlite_cursor.execute("SELECT id, name, stars, usages FROM promo")
    promo_codes = [
        PromoCode(
            id=id_, code=name, reward=Decimal(stars),
            max_activations=usages or 0,
            activations_left=usages or 0
        )
        for id_, name, stars, usages in sqlite_cursor.fetchall()
    ]
    bulk_insert(promo_codes, "promo_codes")

def migrate_promo_activations():
    existing_user_ids = set(pg_session.scalars(select(User.id)).all())
    sqlite_cursor.execute("SELECT id, user_id, promo_id FROM promo_usage")
    records = sqlite_cursor.fetchall()
    valid = [
        PromoActivation(id=id_, user_id=user_id, promo_code_id=promo_id)
        for id_, user_id, promo_id in records
        if user_id in existing_user_ids
    ]
    bulk_insert(valid, "promo_activations")

def migrate_referrals():
    existing_user_ids = set(pg_session.scalars(select(User.id)).all())
    sqlite_cursor.execute("SELECT id, referrer_id, referral_id FROM referral")
    records = sqlite_cursor.fetchall()
    valid = [
        Referral(id=id_, referrer_id=referrer_id, referral_id=referral_id)
        for id_, referrer_id, referral_id in records
        if referrer_id in existing_user_ids and referral_id in existing_user_ids
    ]
    bulk_insert(valid, "referrals")

def migrate_subscription_logs():
    # Получаем уже существующие ID пользователей и каналов
    existing_user_ids = set(pg_session.scalars(select(User.id)).all())
    existing_channel_ids = set(pg_session.scalars(select(Channel.id)).all())

    # Коммитим на случай, если до этого были несохранённые вставки
    pg_session.commit()

    # Получаем уже существующие пары user_id + channel_id
    existing_pairs = set(
        pg_session.query(SubscriptionLog.user_id, SubscriptionLog.channel_id).all()
    )

    # Загружаем данные из SQLite
    sqlite_cursor.execute("SELECT id, user_id, channel_id FROM subscribed")
    records = sqlite_cursor.fetchall()

    valid = []
    seen_pairs = set()

    for id_, user_id, channel_id in records:
        pair = (user_id, channel_id)
        if (
            user_id in existing_user_ids
            and channel_id in existing_channel_ids
            and pair not in existing_pairs
            and pair not in seen_pairs
        ):
            valid.append(SubscriptionLog(id=id_, user_id=user_id, channel_id=channel_id))
            seen_pairs.add(pair)

    bulk_insert(valid, "subscription_logs")


def migrate_x2game():
    sqlite_cursor.execute("SELECT id, lose, win FROM casino")
    x2game = [
        X2Game(id=id_, lost=Decimal(lose), won=Decimal(win))
        for id_, lose, win in sqlite_cursor.fetchall()
    ]
    bulk_insert(x2game, "x2game")

def migrate_withdrawals():
    existing_user_ids = set(pg_session.scalars(select(User.id)).all())
    sqlite_cursor.execute("SELECT id, user_id, stars, username FROM withdraw")
    records = sqlite_cursor.fetchall()
    valid = [
        Withdrawal(
            id=id_, user_id=user_id, stars=Decimal(stars),
            ton_address=None, status=WithdrawalStatus.APPROVED,
            created_at=date.today()
        )
        for id_, user_id, stars, _ in records
        if user_id in existing_user_ids
    ]
    bulk_insert(valid, "withdrawals")

def main():
    clear_tables()
    migrate_users()
    migrate_channels()
    migrate_daily_bonus_claims()
    migrate_tasks()
    migrate_task_completions()
    migrate_promo_codes()
    migrate_promo_activations()
    migrate_referrals()
    migrate_subscription_logs()
    migrate_x2game()
    migrate_withdrawals()

if __name__ == "__main__":
    main()