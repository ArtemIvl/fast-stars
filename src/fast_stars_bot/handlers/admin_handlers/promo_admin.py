from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from decimal import Decimal, InvalidOperation
from utils.promo_requests import is_promo_code_unique, add_promo_code
from keyboards.admin_keyboards import manage_promo_keyboard, promo_pages_keyboard, back_to_promo_keyboard
from utils.promo_requests import get_promo_code, get_promo_activations_page
import re
from db.models.promo_code import PromoCode, PromoActivation

promo_admin_router = Router()


class AddPromoState(StatesGroup):
    waiting_for_promo_code = State()
    waiting_for_activations = State()
    waiting_for_is_vip = State()
    waiting_for_reward = State()

class PromoInfoState(StatesGroup):
    waiting_for_promo_query = State()

@promo_admin_router.callback_query(F.data == "manage_promocodes")
async def manage_promocodes_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Управление промокодами:", reply_markup=manage_promo_keyboard()
    )

@promo_admin_router.callback_query(F.data == "add_promo_code")
async def add_promo_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    sent = await callback.message.edit_text("Введите промокод:", reply_markup=back_to_promo_keyboard())
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddPromoState.waiting_for_promo_code)

@promo_admin_router.message(AddPromoState.waiting_for_promo_code)
async def add_promo_name(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    code = message.text.strip()
    if not re.fullmatch(r"[A-Za-z0-9_!?,]{1,20}", code):
        sent = await message.answer(
            "❗ Промокод может содержать только латинские буквы, цифры и символы _ ! ? ,\n"
            "Он не должен быть длиннее 20 символов и не должен содержать пробелов.\n"
            "Попробуйте снова:",
            reply_markup=back_to_promo_keyboard()
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        return
    
    async with SessionLocal() as session:
        if not await is_promo_code_unique(session, code):
            sent = await message.answer("Промокод уже существует. Попробуйте другой.", reply_markup=back_to_promo_keyboard())
            await state.update_data(last_bot_message_id=sent.message_id)
            return

    await state.update_data(promo_code=code)
    sent = await message.answer("Введите количество активаций:", reply_markup=back_to_promo_keyboard())
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddPromoState.waiting_for_activations)

@promo_admin_router.message(AddPromoState.waiting_for_activations)
async def add_promo_activations(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    try:
        activations = int(message.text)
        if activations <= 0:
            sent = await message.answer("Количество активаций должно быть больше 0. Попробуйте снова.", reply_markup=back_to_promo_keyboard())
            await state.update_data(last_bot_message_id=sent.message_id)
            return
        await state.update_data(activations=activations)
    except ValueError:
        sent = await message.answer("Количество активаций должно быть целым числом. Попробуйте снова.", reply_markup=back_to_promo_keyboard())
        await state.update_data(last_bot_message_id=sent.message_id)
        return
    sent = await message.answer("Это вип промо? (да/нет)")
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddPromoState.waiting_for_is_vip)

@promo_admin_router.message(AddPromoState.waiting_for_is_vip)
async def add_promo_vip_state(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    try:
        vip_promo = message.text.strip().lower()
        if vip_promo not in ["да", "нет"]:
            sent = await message.answer("Пожалуйста, введите 'да' или 'нет'.", reply_markup=back_to_promo_keyboard())
            await state.update_data(last_bot_message_id=sent.message_id)
            return
        await state.update_data(is_vip=vip_promo)
    except ValueError:
        sent = await message.answer("Количество активаций должно быть целым числом. Попробуйте снова.", reply_markup=back_to_promo_keyboard())
        await state.update_data(last_bot_message_id=sent.message_id)
        return
    sent = await message.answer("Введите награду за активацию (⭐️):", reply_markup=back_to_promo_keyboard())
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(AddPromoState.waiting_for_reward)

@promo_admin_router.message(AddPromoState.waiting_for_reward)
async def add_promo_reward(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    try:
        reward = Decimal(message.text)
        if reward <= 0:
            sent = await message.answer("Награда должна быть больше 0. Попробуйте снова.", reply_markup=back_to_promo_keyboard())
            await state.update_data(last_bot_message_id=sent.message_id)
            return
        await state.update_data(reward=reward)
    except InvalidOperation:
        sent = await message.answer("Награда должна быть числом. Попробуйте снова.", reply_markup=back_to_promo_keyboard())
        await state.update_data(last_bot_message_id=sent.message_id)
        return

    data = await state.get_data()
    promo_code = data.get("promo_code")
    max_activations = data.get("activations")
    is_vip = data.get("is_vip") == "да"
    reward = data.get("reward")

    async with SessionLocal() as session:
        await add_promo_code(session, promo_code, max_activations, is_vip, reward)

    await message.answer(f"Промокод {promo_code} успешно добавлен с {max_activations} активациями и наградой {reward}⭐️.", reply_markup=back_to_promo_keyboard())
    await state.clear()


@promo_admin_router.callback_query(F.data == "view_promo_code")
async def view_promo_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    sent = await callback.message.edit_text("Введите название промокода, информацию о котором вы хотите посмотреть:", reply_markup=back_to_promo_keyboard())
    await state.update_data(last_bot_message_id=sent.message_id)
    await state.set_state(PromoInfoState.waiting_for_promo_query)

def generate_promo_info_text(promo: PromoCode, activations: list[PromoActivation], page: int = 1, per_page: int = 10) -> tuple[str, types.InlineKeyboardMarkup | None]:
    total_activations = promo.max_activations - promo.activations_left
    pages = (total_activations + per_page - 1) // per_page
    start = (page - 1) * per_page

    text = (
        f"💬 Промокод: <b>{promo.code}</b>\n"
        f"🔁 Осталось активаций: <b>{promo.activations_left}</b> из {promo.max_activations}\n"
        f"💰 Награда: <b>{promo.reward:.2f}⭐️</b>\n\n"
    )

    if total_activations > 0:
        text += "👥 Пользователи, использовавшие промокод:\n"
        for i, activation in enumerate(activations, start + 1):
            user = activation.user
            text += f"{i}. @{user.username or 'None'} | ID: {user.telegram_id}\n"
    else:
        text += "⛔ Промокод ещё никто не использовал."

    kb = promo_pages_keyboard(promo.code, page, pages)
    return text, kb

@promo_admin_router.message(PromoInfoState.waiting_for_promo_query)
async def process_promo_query(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    code = message.text.strip()
    async with SessionLocal() as session:
        promo = await get_promo_code(session, code)
        if not promo:
            sent = await message.answer("Промокод не найден.", reply_markup=back_to_promo_keyboard())
            await state.update_data(last_bot_message_id=sent.message_id)
            return

        activations = await get_promo_activations_page(session, promo.id, page=1)
        text, kb = generate_promo_info_text(promo, activations, page=1)
        await message.answer(text, parse_mode="HTML", reply_markup=kb)
    await state.clear()

@promo_admin_router.callback_query(F.data.startswith("promo_page_"))
async def handle_promo_page(callback: types.CallbackQuery) -> None:
    _, _, code, page_str = callback.data.split("_")
    page = int(page_str)

    async with SessionLocal() as session:
        promo = await get_promo_code(session, code)
        if not promo:
            await callback.answer("Промокод не найден.", show_alert=True)
            return

        activations = await get_promo_activations_page(session, promo.id, page=page)
        text, kb = generate_promo_info_text(promo, activations, page=page)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()