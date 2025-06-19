from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import json
import os
from datetime import datetime
from keyboards import menu_keyboard

router = Router()

USERS_FILE = "users.json"
STATS_FILE = "stats.json"
LOG_FILE = "actions.log"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_user(user_id, data):
    users = load_users()
    users[str(user_id)] = data
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def update_stats(new_role):
    stats = {"total": 0, "исполнитель": 0, "заказчик": 0}
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            try:
                stats = json.load(f)
            except json.JSONDecodeError:
                pass
    stats["total"] += 1
    if new_role in stats:
        stats[new_role] += 1
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def write_log(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")

class Registration(StatesGroup):
    role = State()
    city = State()
    contact = State()

@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
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

    user_id = str(message.from_user.id)
    users = load_users()
    user = users.get(user_id)

    if user:
        roles = user.get("roles", [])
        if role not in roles:
            roles.append(role)
            user["roles"] = roles
            save_user(user_id, user)
            update_stats(role)
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
        for r in data.get("roles", []):
            update_stats(r)
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
    for r in data.get("roles", []):
        update_stats(r)
    write_log(f"[REG] {message.from_user.id} зарегистрировался с ролями {data['roles']}")
    await message.answer("✅ Регистрация завершена!\nТеперь вы можете пользоваться меню.", reply_markup=menu_keyboard)
    await state.clear()
