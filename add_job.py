from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime
from keyboards import menu_keyboard
from supabase_client import supabase


router = Router()

# 💼 Состояния FSM
class AddJob(StatesGroup):
    title = State()
    description = State()
    price = State()

# 🚀 Старт добавления подработки
@router.message(lambda m: "разместить подработку" in m.text.lower())
async def start_add_job(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Проверяем регистрацию пользователя
    result = supabase.table("users").select("id").eq("telegram_id", user_id).execute()
    if not result.data:
        await message.answer("Сначала зарегистрируйтесь командой /start")
        return

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

    # Получаем контакт и город пользователя из Supabase
    user_id = message.from_user.id
    user_data = (
        supabase.table("users")
        .select("city,phone")
        .eq("telegram_id", user_id)
        .execute()
    )
    user = user_data.data[0] if user_data.data else {}

    job = {
        "user_id": str(user_id),
        "title": data["title"],
        "description": data["description"],
        "price": data["price"],
        "city": user.get("city", "Не указан"),
        "contact": user.get("phone", "Не указан"),
        "created_at": datetime.utcnow().isoformat()
    }

    # Сохраняем подработку в Supabase
    supabase.table("jobs").insert(job).execute()

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
