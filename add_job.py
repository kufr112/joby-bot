from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import json
import os
from datetime import datetime

from keyboards import menu_keyboard
from registration import load_users, save_user, update_stats, write_log  # подключаем нужные функции

router = Router()

JOBS_FILE = "jobs.json"
LOG_FILE = "actions.log"

# 💼 Состояния FSM для пошагового ввода подработки
class AddJob(StatesGroup):
    title = State()
    description = State()
    price = State()

# 📂 Загрузка и сохранение подработок
def load_jobs():
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_job(job):
    jobs = load_jobs()
    jobs.append(job)
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    write_log(f"[JOB] Новая подработка от {job['user_id']} — {job['title']} ({job['price']} руб.)")

# 🚀 Обработка команды "Разместить подработку"
@router.message(lambda m: "разместить подработку" in m.text.lower())
async def start_add_job(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    users = load_users()
    user = users.get(user_id)

    # 🧠 Если пользователь не существует — создать его с ролью "заказчик"
    if not user:
        user = {
            "roles": ["заказчик"],
            "city": "Не указан",
            "contact": f"@{message.from_user.username}" if message.from_user.username else "Не указан"
        }
        save_user(user_id, user)
        update_stats("заказчик")
        write_log(f"[REG-AUTO] {user_id} зарегистрирован как заказчик (через размещение)")
    # 🔄 Если есть, но нет роли — добавить роль "заказчик"
    elif "заказчик" not in user.get("roles", []):
        user["roles"].append("заказчик")
        save_user(user_id, user)
        update_stats("заказчик")
        write_log(f"[REG-AUTO] {user_id} добавлена роль заказчик (через размещение)")

    await message.answer("✏️ Введите заголовок подработки (например: 'Помощь на складе'):")
    await state.set_state(AddJob.title)

# 🧩 Сбор заголовка
@router.message(AddJob.title)
async def get_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("📄 Напишите описание подработки:")
    await state.set_state(AddJob.description)

# 📄 Сбор описания
@router.message(AddJob.description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer("💰 Укажите оплату (в рублях):")
    await state.set_state(AddJob.price)

# 💰 Сбор цены и финализация
@router.message(AddJob.price)
async def get_price(message: Message, state: FSMContext):
    price_text = message.text.strip()

    if not price_text.isdigit():
        await message.answer("⚠️ Укажите корректную сумму числом, без символов.")
        return

    await state.update_data(price=price_text)
    data = await state.get_data()

    users = load_users()
    user = users.get(str(message.from_user.id), {})

    job = {
        "user_id": message.from_user.id,
        "title": data["title"],
        "description": data["description"],
        "price": data["price"],
        "city": user.get("city", "Не указан"),
        "contact": user.get("contact", "Не указан"),
        "timestamp": datetime.now().isoformat()
    }

    save_job(job)

    await message.answer(
        f"✅ <b>Подработка размещена!</b>\n\n"
        f"<b>{job['title']}</b>\n"
        f"{job['description']}\n"
        f"💰 {job['price']} руб.\n"
        f"📍 {job['city']}\n"
        f"📞 {job['contact']}",
        reply_markup=menu_keyboard
    )
    await state.clear()
