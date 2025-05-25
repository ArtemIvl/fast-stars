from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.enums import DiceEmoji
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from keyboards.cube_keyboard import cube_keyboard, back_to_cube_keyboard, end_game_keyboard, throw_cube_keyboard
from utils.cube_requests import find_waiting_game, create_game, join_game, finish_game, get_game_by_id, cancel_game
from utils.user_requests import get_user_by_telegram_id, get_user_by_id
from db.models.user import User
from db.models.cube_game import GameStatus
from decimal import Decimal
from aiogram.exceptions import TelegramBadRequest
import asyncio
from aiogram import Bot
import time
from utils.game_settings_requests import get_game_setting

router = Router()

def register_cube_handlers(dp) -> None:
    dp.include_router(router)

class CubeGameState(StatesGroup):
    waiting_for_p1 = State()
    waiting_for_p2 = State()

active_throws = set()
user_cooldowns: dict[int, float] = {}
pending_throws: dict[int, asyncio.Task] = {}

async def start_throw_timeout(game_id: int, user_id: int, bet: Decimal, user: User, bot: Bot):
    await asyncio.sleep(30)

    async with SessionLocal() as session:
        game = await get_game_by_id(session, game_id)
        if not game or game.status != GameStatus.IN_PROGRESS:
            return
                
        leaver = await get_user_by_id(session, user_id)
        if not leaver:
            return

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

        try:
            await bot.send_message(
                leaver.telegram_id,
                "⏳ Вы покинули игру, не доиграв её до конца. К сожалению, ваша ставка списана."
            )
        except Exception:
            pass

        try:
            await bot.send_message(
                other_player.telegram_id,
                f"@{leaver.username or 'Игрок'} вышел 🤷🏻‍♂️\n"
                "Ждёте нового игрока или нажмите «Выйти», чтобы покинуть стол.",
                reply_markup=back_to_cube_keyboard(game.id)
            )
        except Exception:
            pass

        pending_throws.pop(game_id, None)
        active_throws.discard((game_id, 1))
        active_throws.discard((game_id, 2))


@router.callback_query(F.data == "cube_game")
async def cube_game_callback(callback: types.CallbackQuery) -> None:
    kb = await cube_keyboard()
    await callback.message.edit_text(
        "🎲 Добро пожаловать в игру Cube Game!\n\n"
        "Выберите стол — от этого зависит ставка: 1, 5 или 10 ⭐️.\n"
        "• После выбора стола ждите соперника. Когда второй игрок присоединится, вы по очереди бросаете кубики.\n"
        "• 🎯 Победитель — тот, у кого выпадет большее число, забирает банк!\n"
        "• 💸 Выигрыш: ×2 от ставки минус 20% комиссии игры.\n"
        "• ♻️ Ничья: Если числа совпали — бросаете кубики заново.\n\n"
        "🔍 Ищете соперника? Загляните в наш чат — https://t.me/+mKubmWJxJM5mZDUy\n\n"
        "Готовы испытать удачу? Тогда за стол!👇🏻",
        disable_web_page_preview=True,
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("cube_bet_"))
async def play_cube_game(callback: types.CallbackQuery) -> None:
    bet_amount = Decimal(callback.data.split("_")[-1])
    telegram_id = callback.from_user.id

    last_exit = user_cooldowns.get(telegram_id)
    if last_exit and (time.time() - last_exit) < 15:
        remaining = 15 - int(time.time() - last_exit)
        await callback.answer(f"⏳ Подождите {remaining} сек перед повторным входом", show_alert=True)
        return

    async with SessionLocal() as session:
        # clean up cancelled games here
        user: User = await get_user_by_telegram_id(session, telegram_id)
        if not user or user.stars < bet_amount:
            await callback.answer(
                "Недостаточно звезд для ставки! ⭐️",
                show_alert=True,
            )
            return

        waiting_game = await find_waiting_game(session, bet_amount)

        if not waiting_game:
            game = await create_game(session, user, bet_amount)
            await callback.message.edit_text(
                f"Вы присоединились к столу со ставкой {bet_amount} ⭐️.\n"
                "Ждём второго игрока и начинаем игру 🎲\n\n"
                "❗️Внимание: если вы начнёте игру со вторым игроком, покинуть её будет невозможно до завершения партии!\n\n"
                "⏱️У вас есть 30 секунд на бросок!",
                reply_markup=back_to_cube_keyboard(game.id)
            )
        else:
            game = await join_game(session, waiting_game, user)

            player1 = await get_user_by_id(session, game.player1_id)
            player2 = user

            if player1.telegram_id:
                await callback.bot.send_message(
                    player1.telegram_id,
                    f"Все игроки присоединились 🤝\n👤 @{player1.username or 'Игрок'} кидает кубик.",
                    reply_markup=throw_cube_keyboard(game.id, 1)
                )
            
            task = asyncio.create_task(start_throw_timeout(game.id, player1.id, game.bet, player1, callback.bot))
            pending_throws[game.id] = task

            if player2.telegram_id:
                await callback.bot.send_message(
                    player2.telegram_id,
                    f"Все игроки присоединились 🤝\n👤 @{player1.username or 'Игрок'} кидает кубик."
                )


@router.callback_query(F.data.startswith("throw_cube_"))
async def handle_throw_cube(callback: types.CallbackQuery, state: FSMContext) -> None:
            parts = callback.data.split("_")
            game_id = int(parts[2])
            player  = int(parts[3])
            first_value = int(parts[4]) if len(parts) == 5 else None

            key = (game_id, player)
            if key in active_throws:
                await callback.answer("⏳ Вы уже бросили кубик", show_alert=True)
                return
            
            active_throws.add(key)

            async with SessionLocal() as session:
                game = await get_game_by_id(session, game_id)
                if not game:
                    await callback.answer("Игра не найдена", show_alert=True)
                    return
                
                player1 = await get_user_by_id(session, game.player1_id)
                player2 = await get_user_by_id(session, game.player2_id)

                sent_dice = await callback.message.answer_dice(emoji=DiceEmoji.DICE)
                await callback.message.edit_reply_markup(reply_markup=None)
                value = sent_dice.dice.value
                await asyncio.sleep(4)

                if player == 1:
                    task = pending_throws.pop(game.id, None)
                    if task:
                        task.cancel()
                    await callback.bot.forward_message(
                        chat_id=player2.telegram_id,
                        from_chat_id=player1.telegram_id,
                        message_id=sent_dice.message_id
                    )
                     
                    txt_p1 = f"👤 @{player1.username or 'Игрок'} выбил {value}.\n" \
                             f"👤 @{player2.username or 'Игрок'} кидает кубик!"
                    kb = types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [types.InlineKeyboardButton(
                                text="🎲 Бросить кубик",
                                callback_data=f"throw_cube_{game_id}_2_{value}"
                            )]
                        ]
                    )

                    await callback.bot.send_message(player2.telegram_id, txt_p1, reply_markup=kb)
                    await callback.bot.send_message(player1.telegram_id, txt_p1)

                    task = asyncio.create_task(start_throw_timeout(game.id, player2.id, game.bet, player2, callback.bot))
                    pending_throws[game.id] = task

                    await callback.answer()

                    return

                else:
                    task = pending_throws.pop(game.id, None)
                    if task:
                        task.cancel()

                    p1_result = first_value
                    p2_result = value

                    await callback.bot.forward_message(
                        chat_id=player1.telegram_id,
                        from_chat_id=player2.telegram_id,
                        message_id=sent_dice.message_id
                    )

                    # info = (
                    #     f"👤 @{player2.username or 'Игрок'} бросил кубик и выбил {p2_result}."
                    # )
                    # await asyncio.gather(
                    #     callback.bot.send_message(player1.telegram_id, info),
                    #     callback.bot.send_message(player2.telegram_id, info)
                    # )
                    if p1_result == p2_result:
                        active_throws.discard((game_id, 1))
                        active_throws.discard((game_id, 2))
                        # клавиатура только первому игроку
                        await callback.bot.send_message(
                            player1.telegram_id,
                            "Ничья! 🎲\nКидаем кубики заново.",
                            reply_markup=throw_cube_keyboard(game.id, 1)   # тут кнопка
                        )

                        # второму игроку — просто сообщение, без клавиатуры
                        await callback.bot.send_message(
                            player2.telegram_id,
                            "Ничья! 🎲\nОжидаем ход соперника."
                        )

                        task = asyncio.create_task(start_throw_timeout(game.id, player1.id, game.bet, player1, callback.bot))
                        pending_throws[game.id] = task

                        await state.clear()
                        await callback.answer()
                        return

                    winner, loser = (player1, player2) if p1_result > p2_result else (player2, player1)
                    commission = await get_game_setting(session, "cube_commission")
                    if commission is None:
                        commission = 20

                    commission_decimal = Decimal(commission) / Decimal("100")
                    multiplier = Decimal("1") - commission_decimal

                    win_amount = game.bet * multiplier
                    winner.stars += win_amount
                    loser.stars -= game.bet
                    await finish_game(session, game, winner)
                    await session.commit()
                    await state.clear()

                    msg = (
                        f"👤 @{player2.username} выпало {p2_result}.\n"
                        f"<b>@{winner.username} победил! 🎉</b>\n"
                        f"<b>Ваш баланс: {player1.stars:.2f} ⭐️</b>\n"
                        f"<b>Продолжим?👇🏻</b>"
                    )
                    await callback.bot.send_message(player1.telegram_id, msg, parse_mode="HTML", reply_markup=end_game_keyboard(game.bet))

                    msg = (
                        f"👤 @{player2.username} выпало {p2_result}.\n"
                        f"<b>@{winner.username} победил! 🎉</b>\n"
                        f"Ваш баланс: {player2.stars:.2f} ⭐️\n"
                        f"<b>Продолжим?👇🏻</b>"
                    )
                    await callback.bot.send_message(player2.telegram_id, msg, parse_mode="HTML", reply_markup=end_game_keyboard(game.bet))

                active_throws.discard(key)
                await callback.answer()
                

@router.callback_query(F.data.startswith("cancel_game_"))
async def cancel_game_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    game_id = int(callback.data.split("_")[-1])
    telegram_id = callback.from_user.id

    async with SessionLocal() as session:
        game = await get_game_by_id(session, game_id)
        user = await get_user_by_telegram_id(session, telegram_id)
        if game and game.status == GameStatus.WAITING and game.player1_id == user.id:
            await cancel_game(session, game)
            user_cooldowns[telegram_id] = time.time()
            sent = await callback.message.answer("❌ Вы покинули комнату.")
            kb = await cube_keyboard()
            await callback.message.edit_text(
                "🎲 Добро пожаловать в игру Cube Game!\n\n"
                "Выберите стол — от этого зависит ставка: 1, 5 или 10 ⭐️.\n"
                "• После выбора стола ждите соперника. Когда второй игрок присоединится, вы по очереди бросаете кубики.\n"
                "• 🎯 Победитель — тот, у кого выпадет большее число, забирает банк!\n"
                "• 💸 Выигрыш: ×2 от ставки минус 20% комиссии игры.\n"
                "• ♻️ Ничья: Если числа совпали — бросаете кубики заново.\n\n"
                "🔍 Ищете соперника? Загляните в наш чат — https://t.me/+mKubmWJxJM5mZDUy\n\n"
                "Готовы испытать удачу? Тогда за стол!👇🏻",
                disable_web_page_preview=True,
                reply_markup=kb,
            )
            await asyncio.sleep(5)
            await sent.delete()
            await state.clear()


@router.callback_query(F.data == "cube_refresh")
async def refresh_cube_menu(callback: types.CallbackQuery) -> None:
    kb = await cube_keyboard()
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except TelegramBadRequest as e:
        # Ничего не изменилось – это не критично
        if "message is not modified" in str(e):
            await callback.answer("Уже актуально ✅", show_alert=False)
            return
        raise

    await callback.answer("Обновлено ✅", show_alert=False)

