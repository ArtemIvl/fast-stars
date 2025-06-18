from datetime import datetime, timedelta, timezone
from decimal import Decimal

from db.models.cube_game import CubeGame, GameStatus
from db.models.user import User
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.game_settings_requests import get_game_setting
from utils.user_requests import get_user_by_id


async def find_waiting_game(session: AsyncSession, bet: Decimal) -> CubeGame | None:
    result = await session.execute(
        select(CubeGame)
        .where(CubeGame.status == GameStatus.WAITING, CubeGame.bet == bet)
        .limit(1)
    )
    return result.scalars().first()


async def create_game(session: AsyncSession, player1: User, bet: Decimal) -> CubeGame:
    game = CubeGame(
        player1_id=player1.id,
        bet=bet,
        status=GameStatus.WAITING,
        created_at=datetime.now(),
    )
    session.add(game)
    await session.commit()
    await session.refresh(game)
    return game


async def join_game(session: AsyncSession, game: CubeGame, player2: User) -> CubeGame:
    game.player2_id = player2.id
    game.status = GameStatus.IN_PROGRESS
    await session.commit()
    await session.refresh(game)
    return game


async def finish_game(
    session: AsyncSession, game: CubeGame, p1_result: int, p2_result: int
) -> User:
    player1 = await get_user_by_id(session, game.player1_id)
    player2 = await get_user_by_id(session, game.player2_id)

    winner, loser = (player1, player2) if p1_result > p2_result else (player2, player1)

    commission = await get_game_setting(session, "cube_commission")
    if commission is None:
        commission = 20

    commission_decimal = Decimal(commission) / Decimal("100")
    multiplier = Decimal("1") - commission_decimal

    win_amount = game.bet * multiplier

    winner.stars += win_amount
    loser.stars -= game.bet

    game.winner_id = winner.id
    game.status = GameStatus.FINISHED

    await session.commit()
    return winner


async def cancel_game(session: AsyncSession, game: CubeGame) -> None:
    game.status = GameStatus.CANCELED
    await session.commit()


async def get_game_by_id(session: AsyncSession, game_id: int) -> CubeGame | None:
    result = await session.execute(select(CubeGame).where(CubeGame.id == game_id))
    return result.scalars().first()


async def get_active_game_by_user(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(CubeGame).where(
            CubeGame.status.in_([GameStatus.WAITING, GameStatus.IN_PROGRESS]),
            (CubeGame.player1_id == user_id) | (CubeGame.player2_id == user_id),
        )
    )
    return result.scalars().first()


async def get_waiting_count(session, bet: Decimal) -> int:
    result = await session.execute(
        select(CubeGame).where(
            CubeGame.status == GameStatus.WAITING, CubeGame.bet == bet
        )
    )
    players = result.scalars().all()
    return len(players) or 0


async def get_active_count(session, bet: Decimal) -> int:
    result = await session.execute(
        select(CubeGame).where(
            CubeGame.status == GameStatus.IN_PROGRESS, CubeGame.bet == bet
        )
    )
    games = result.scalars().all()
    return len(games) * 2 or 0


async def get_cube_game_stats(
    session: AsyncSession, commission: Decimal
) -> tuple[int, Decimal, Decimal, Decimal]:
    result = await session.execute(
        select(func.count(CubeGame.id), func.coalesce(func.sum(CubeGame.bet), 0)).where(
            CubeGame.status == GameStatus.FINISHED
        )
    )

    total_games, total_bet_sum = result.one()

    commission_decimal = commission / Decimal("100")
    multiplier = Decimal("1") - commission_decimal

    total_won = total_bet_sum * multiplier
    total_lost = total_bet_sum
    bot_commission = total_bet_sum * commission_decimal

    return total_games, total_won, total_lost, bot_commission


async def delete_old_canceled_games(session: AsyncSession) -> None:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(tzinfo=None)
    stmt = delete(CubeGame).where(
        CubeGame.status == GameStatus.CANCELED, CubeGame.created_at < cutoff
    )
    await session.execute(stmt)
    await session.commit()


async def handle_throw_timeout(
    session: AsyncSession, game_id: int, user_id: int, bet: Decimal
) -> tuple[User, User, CubeGame | None]:
    game = await get_game_by_id(session, game_id)
    if not game or game.status != GameStatus.IN_PROGRESS:
        return None, None, None

    leaver = await get_user_by_id(session, user_id)
    if not leaver:
        return None, None, None

    if leaver.stars >= bet:
        leaver.stars -= bet

    other_player_id = game.player2_id if game.player1_id == user_id else game.player1_id
    other_player = await get_user_by_id(session, other_player_id)

    if game.player1_id == user_id:
        game.player1_id = game.player2_id
    else:
        game.player2_id = None

    game.status = GameStatus.WAITING
    await session.commit()

    return leaver, other_player, game
