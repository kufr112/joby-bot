import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import datetime
from supabase import create_client
import os
from dotenv import load_dotenv

# === Supabase ===
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Логгер ===
logger = logging.getLogger(__name__)

# === Меню-клавиатура ===
menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Мои подработки")],
        [KeyboardButton(text="➕ Добавить подработку")],
        [KeyboardButton(text="🔍 Найти исполнителя")]
    ],
    resize_keyboard=True
)

router = Router()

# === Состояния ===
class Registration(StatesGroup):
    role = State()
    city = State()
    contact = State()

# === /start ===
@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    logger.info(f"[START] {message.from_user.id} начал регистрацию")
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

# === Выбор роли ===
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

    user_id = str(message.from_user.id)

    # Проверка в базе
    existing = supabase.table("users").select("roles").eq("id", user_id).execute()
    if existing.data:
        roles = existing.data[0].get("roles", [])
        if role not in roles:
            roles.append(role)
            supabase.table("users").update({"roles": roles}).eq("id", user_id).execute()
            await message.answer(f"✅ Роль <b>{role}</b> добавлена к вашему профилю.", reply_markup=menu_keyboard)
        else:
            await message.answer(f"✅ У вас уже есть роль <b>{role}</b>.", reply_markup=menu_keyboard)
        await state.clear()
        return

    await state.update_data(roles=[role])
    await message.answer("🏙 Введите ваш город:")
    await state.set_state(Registration.city)

# === Ввод города ===
@router.message(Registration.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    username = message.from_user.username
    if username:
        await state.update_data(contact=f"@{username}")
        await save_to_supabase(message.from_user.id, await state.get_data())
        await message.answer("✅ Регистрация завершена!\nТеперь вы можете пользоваться меню.", reply_markup=menu_keyboard)
        await state.clear()
    else:
        await message.answer("📞 Введите контакт для связи (номер телефона или @username):")
        await state.set_state(Registration.contact)

# === Ввод контакта ===
@router.message(Registration.contact)
async def get_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await save_to_supabase(message.from_user.id, await state.get_data())
    await message.answer("✅ Регистрация завершена!\nТеперь вы можете пользоваться меню.", reply_markup=menu_keyboard)
    await state.clear()

# === Сохранение в Supabase ===
async def save_to_supabase(user_id, data):
    try:
        supabase.table("users").insert({
            "id": str(user_id),
            "roles": data.get("roles", []),
            "city": data.get("city"),
            "contact": data.get("contact"),
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        logger.info(f"[REG] {user_id} зарегистрирован: {data}")
    except Exception as e:
        logger.exception(f"❌ Ошибка при сохранении в Supabase: {e}")
