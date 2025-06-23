import logging
import os
from datetime import datetime

from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from supabase import create_client
from dotenv import load_dotenv

# === Логгер ===
logger = logging.getLogger(__name__)

# === Supabase ===
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Клавиатура меню ===
menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Мои подработки")],
        [KeyboardButton(text="➕ Добавить подработку")],
        [KeyboardButton(text="🔍 Найти исполнителя")]
    ],
    resize_keyboard=True
)

router = Router()

# === FSM Состояния ===
class Registration(StatesGroup):
    role = State()
    city = State()
    contact = State()

# === Supabase-функции ===
def save_user(user_id, data):
    existing = supabase.table("users").select("telegram_id").eq("telegram_id", user_id).execute()
    if existing.data:
        supabase.table("users").update({
            "roles": data["roles"],
            "city": data.get("city"),
            "contact": data.get("contact")
        }).eq("telegram_id", user_id).execute()
    else:
        supabase.table("users").insert({
            "telegram_id": user_id,
            "roles": data["roles"],
            "city": data.get("city"),
            "contact": data.get("contact")
        }).execute()

def get_user(user_id):
    res = supabase.table("users").select("*").eq("telegram_id", user_id).single().execute()
    return res.data if res.data else None

def write_log(text):
    logger.info(text)

# === Обработчики ===
@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    logger.info(f"[START] Получен /start от {message.from_user.id}")
    write_log(f"[START] {message.from_user.id} начал регистрацию")
    await message.answer(
        "👋 Привет! Я Joby — бот подработок.\n\nВыберите действие:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 Хочу найти подработку")],
                [KeyboardButton(text="➕ Хочу разместить подработку")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.set_state(Registration.role)

@router.message(Registration.role)
async def get_role(message: Message, state: FSMContext):
    role = None
    if "найти" in message.text.lower():
        role = "исполнитель"
    elif "разместить" in message.text.lower():
        role = "заказчик"
    else:
        await message.answer("Пожалуйста, выберите один из вариантов кнопками ниже.")
        return

    user_id = message.from_user.id
    user = get_user(user_id)

    if user:
        roles = user.get("roles", [])
        if role not in roles:
            roles.append(role)
            user["roles"] = roles
            save_user(user_id, user)
            write_log(f"[REG] {user_id} добавил роль {role}")
            await message.answer(f"✅ Роль <b>{role}</b> добавлена к вашему профилю.", reply_markup=menu_keyboard)
        else:
            await message.answer(f"✅ У вас уже есть роль <b>{role}</b>.", reply_markup=menu_keyboard)
        await state.clear()
        return

    await state.update_data(roles=[role])
    await message.answer("🏙 Введите ваш город:")
    await state.set_state(Registration.city)

@router.message(Registration.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    username = message.from_user.username
    if username:
        await state.update_data(contact=f"@{username}")
        data = await state.get_data()
        save_user(message.from_user.id, data)
        write_log(f"[REG] {message.from_user.id} зарегистрировался с ролями {data['roles']}")
        await message.answer("✅ Регистрация завершена!\nТеперь вы можете пользоваться меню.", reply_markup=menu_keyboard)
        await state.clear()
    else:
        await message.answer("📞 Введите контакт для связи (номер телефона или @username):")
        await state.set_state(Registration.contact)

@router.message(Registration.contact)
async def get_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    save_user(message.from_user.id, data)
    write_log(f"[REG] {message.from_user.id} зарегистрировался с ролями {data['roles']}")
    await message.answer("✅ Регистрация завершена!\nТеперь вы можете пользоваться меню.", reply_markup=menu_keyboard)
    await state.clear()
