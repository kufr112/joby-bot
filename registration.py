import logging
import re
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from keyboards import (
    menu_keyboard,
    phone_keyboard,
    register_keyboard,
    remove_keyboard,
)
from supabase_client import supabase

logger = logging.getLogger(__name__)

router = Router()


class RegisterState(StatesGroup):
    name = State()
    city = State()
    phone = State()


async def user_exists(telegram_id: int) -> bool:
    try:
        data = (
            supabase.table("users")
            .select("id")
            .eq("id", telegram_id)
            .execute()
        )
        return bool(data.data)
    except Exception as e:
        logger.exception(f"Supabase check failed: {e}")
        return False


@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext) -> None:
    if await user_exists(message.from_user.id):
        await message.answer("📌 Главное меню:", reply_markup=menu_keyboard)
        return

    await state.clear()
    text = (
        "👋 Добро пожаловать в Joby — бот для поиска и размещения подработок!\n"
        "Давайте начнём с регистрации:"
    )
    await message.answer(text, reply_markup=register_keyboard)


@router.message(lambda m: m.text and "зарегистрироваться" in m.text.lower())
async def registration_start(message: Message, state: FSMContext) -> None:
    await message.answer("Введите ваше имя:", reply_markup=remove_keyboard)
    await state.set_state(RegisterState.name)


@router.message(RegisterState.name)
async def get_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await message.answer("Введите ваш город:")
    await state.set_state(RegisterState.city)


@router.message(RegisterState.city)
async def get_city(message: Message, state: FSMContext) -> None:
    await state.update_data(city=message.text.strip())
    await message.answer(
        "Укажите ваш номер телефона:", reply_markup=phone_keyboard
    )
    await state.set_state(RegisterState.phone)


def normalize_phone(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)

    if digits.startswith("375") and len(digits) == 12:
        code = digits[3:5]
        if code in {"25", "29", "33", "44"}:
            return "+375" + digits[3:]

    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]

    if digits.startswith("7") and len(digits) == 11:
        code = int(digits[1:4])
        if 901 <= code <= 999:
            return "+" + digits

    return None


@router.message(RegisterState.phone)
async def get_phone(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number if message.contact else message.text.strip()
    valid = normalize_phone(phone)
    if not valid:
        await message.answer(
            "⚠️ Номер выглядит некорректным. Введите белорусский или российский номер, например:\n"
            "+375291234567 или +79261234567"
        )
        return

    await state.update_data(phone=valid)
    data = await state.get_data()

    try:
        supabase.table("users").insert(
            {
                "id": message.from_user.id,
                "username": message.from_user.username,
                "name": data["name"],
                "city": data["city"],
                "phone": data["phone"],
                "created_at": datetime.utcnow().isoformat(),
            }
        ).execute()
    except Exception as e:
        logger.exception(f"Failed to save user: {e}")

    await message.answer(
        "✅ Регистрация завершена!", reply_markup=menu_keyboard
    )
    await state.clear()
