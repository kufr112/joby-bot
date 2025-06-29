import re
import os
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
from supabase_client import supabase, with_supabase_retry
from stats_logger import StatsLogger
from log_utils import logger

router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

class RegisterState(StatesGroup):
    name = State()
    city = State()
    phone_choice = State()
    phone = State()


async def user_exists(telegram_id: int) -> bool:
    try:
        data = await with_supabase_retry(
            lambda: supabase.table("users")
            .select("id")
            .eq("telegram_id", telegram_id)
            .execute()
        )
        return bool(getattr(data, "data", []))
    except Exception as e:
        logger.warning(f"Supabase check failed: {e}")
        StatsLogger.log(event="supabase_error", message=str(e))
        return False


@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext) -> None:
    StatsLogger.log(event="start_command")
    logger.info("start_cmd invoked for user %s", message.from_user.id)

    user_id = message.from_user.id
    username = message.from_user.username or ""
    name = message.from_user.full_name

    try:
        result = await with_supabase_retry(
            lambda: supabase.table("users")
            .select("id")
            .eq("telegram_id", user_id)
            .execute()
        )
        if not getattr(result, "data", []):
            StatsLogger.log(event="register_user_attempt", telegram_id=user_id)
            logger.info("Inserting new user %s into Supabase", user_id)
            await with_supabase_retry(
                lambda: supabase.table("users").insert(
                    {
                        "telegram_id": user_id,
                        "username": username,
                        "name": name,
                        "city": "Не указан",
                        "phone": "Не указан",
                        "created_at": datetime.utcnow().isoformat(),
                    }
                ).execute()
            )
            logger.info("Insert completed")
    except Exception as e:
        logger.warning(f"Failed to ensure user in Supabase: {e}")
        StatsLogger.log(event="supabase_error", message=str(e))

    await state.clear()
    await message.answer("👋 Добро пожаловать в Joby! Меню ниже ⬇️", reply_markup=menu_keyboard)


@router.message(lambda m: m.text and "зарегистрироваться" in m.text.lower())
async def registration_start(message: Message, state: FSMContext) -> None:
    await message.answer("Введите ваше имя:", reply_markup=remove_keyboard)
    await state.set_state(RegisterState.name)


@router.message(RegisterState.name)
async def get_name(message: Message, state: FSMContext) -> None:
    if not (message.text and message.text.strip()):
        await message.answer("⚠️ Пожалуйста, введите имя текстом.")
        return
    await state.update_data(name=message.text.strip())
    await message.answer("Введите ваш город:")
    await state.set_state(RegisterState.city)


@router.message(RegisterState.city)
async def get_city(message: Message, state: FSMContext) -> None:
    if not (message.text and message.text.strip()):
        await message.answer("⚠️ Пожалуйста, укажите город.")
        return
    await state.update_data(city=message.text.strip())
    await message.answer("Укажите ваш номер телефона:", reply_markup=phone_keyboard)
    await state.set_state(RegisterState.phone_choice)


def normalize_phone(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)

    # Беларусь
    if digits.startswith("375") and len(digits) == 12:
        code = digits[3:5]
        if code in {"25", "29", "33", "44"}:
            return "+375" + digits[3:]

    # Россия (8XXXXXXXXXX → +7)
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]

    if digits.startswith("7") and len(digits) == 11:
        return "+" + digits

    return None


async def _finish_registration(message: Message, state: FSMContext, phone: str) -> None:
    await state.update_data(phone=phone)
    data = await state.get_data()
    StatsLogger.log(
        event="register_user_attempt",
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    logger.info("Saving user %s to Supabase", message.from_user.id)
    try:
        await with_supabase_retry(
            lambda: supabase.table("users").insert(
                {
                    "telegram_id": message.from_user.id,
                    "username": message.from_user.username,
                    "name": data["name"],
                    "city": data["city"],
                    "phone": data["phone"],
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()
        )
        logger.info("Insert completed")
        StatsLogger.log(event="registration_success")
    except Exception as e:
        logger.exception(f"Failed to save user: {e}")
        StatsLogger.log(event="supabase_error", message=str(e))

    await message.answer("✅ Регистрация завершена!", reply_markup=menu_keyboard)
    await state.clear()


@router.message(RegisterState.phone_choice)
async def choose_phone_method(message: Message, state: FSMContext) -> None:
    if message.contact:
        phone = message.contact.phone_number
        valid = normalize_phone(phone)
        if not valid:
            await message.answer("⚠️ Номер выглядит некорректным. Попробуйте отправить другой номер.")
            return
        await _finish_registration(message, state, valid)
        return

    text = message.text.lower() if message.text else ""
    if "ввести" in text:
        await message.answer("Введите номер телефона:", reply_markup=remove_keyboard)
        await state.set_state(RegisterState.phone)
        return

    if message.text:
        phone = message.text.strip()
        valid = normalize_phone(phone)
        if valid:
            await _finish_registration(message, state, valid)
            return

    await message.answer(
        "⚠️ Номер выглядит некорректным. Введите белорусский или российский номер, например:\n"
        "+375291234567 или +79261234567"
    )


@router.message(RegisterState.phone)
async def get_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    valid = normalize_phone(phone)
    if not valid:
        await message.answer(
            "⚠️ Номер выглядит некорректным. Введите белорусский или российский номер, например:\n"
            "+375291234567 или +79261234567"
        )
        return

    await _finish_registration(message, state, valid)


@router.message(Command("logs"))
async def last_logs(message: Message) -> None:
    """Send last 10 logs from Supabase to the admin."""
    if message.from_user.id != ADMIN_ID:
        return
    try:
        result = await with_supabase_retry(
            lambda: supabase.table("logs")
            .select("timestamp,type,message")
            .order("timestamp", desc=True)
            .limit(10)
            .execute()
        )
        rows = getattr(result, "data", [])
    except Exception as e:
        await message.answer(f"Ошибка получения логов: {e}")
        return

    lines = []
    for row in rows:
        ts = row.get("timestamp", "")[:19].replace("T", " ")
        lines.append(f"{ts} [{row.get('type')}] {row.get('message')}")
    await message.answer("\n".join(lines) or "Нет логов")
