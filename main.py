import asyncio
import os
import json
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from dotenv import load_dotenv

from registration import router as registration_router
from add_job import router as job_router
from keyboards import menu_keyboard
from logger_middleware import GlobalLoggerMiddleware  # ✅ Подключение глобального логгера

# -------------------- ЛОГИ --------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# -------------------- ENV ---------------------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN:
    logger.error("❌ BOT_TOKEN не найден в .env файле")
    exit("ОШИБКА: BOT_TOKEN отсутствует!")

if not ADMIN_ID:
    logger.error("❌ ADMIN_ID не найден в .env файле")
    exit("ОШИБКА: ADMIN_ID отсутствует!")

# -------------------- BOT ---------------------
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# ✅ Мидлварь логирования всех сообщений
dp.message.middleware(GlobalLoggerMiddleware())
dp.callback_query.middleware(GlobalLoggerMiddleware())

# -------------------- ROUTERS ---------------------
router = Router()
dp.include_router(router)
dp.include_router(registration_router)
dp.include_router(job_router)

# ------------------ МЕНЮ ------------------
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я Joby — бот для поиска и размещения подработок.\n\nОткройте меню снизу 👇",
        reply_markup=menu_keyboard
    )

@router.message(Command("stats"))
async def stats_command(message: Message):
    if str(message.from_user.id) != ADMIN_ID:
        await message.answer("🚫 У вас нет доступа к статистике.")
        return

    stats = {"total": 0, "исполнитель": 0, "заказчик": 0}
    if os.path.exists("stats.json"):
        with open("stats.json", "r", encoding="utf-8") as f:
            stats = json.load(f)

    await message.answer(
        f"📊 <b>Статистика</b>:\n"
        f"👥 Всего пользователей: {stats.get('total', 0)}\n"
        f"🔍 Ищут подработку: {stats.get('исполнитель', 0)}\n"
        f"➕ Размещают подработку: {stats.get('заказчик', 0)}"
    )

# ------------------ РЕАКЦИЯ НА КНОПКИ ------------------
@router.message(F.text.in_({
    "📢 Найти подработку",
    "🧾 Мои публикации",
    "👤 Профиль / Настройки",
    "📌 Подписки",
    "💬 Помощь / FAQ"
}))
async def log_buttons(message: Message):
    responses = {
        "📢 Найти подработку": "🔍 Сейчас подработок нет, но скоро появятся!",
        "🧾 Мои публикации": "📄 Здесь будут отображаться все твои размещённые подработки.",
        "👤 Профиль / Настройки": "⚙️ Здесь будут твои настройки профиля и данные.",
        "📌 Подписки": "🔔 Здесь будут ваши подписки на пользователей или категории.",
        "💬 Помощь / FAQ": "❓ Здесь будет список часто задаваемых вопросов и помощь."
    }

    await message.answer(responses.get(message.text, "🤔 Команда не распознана."))

# -------------------- MAIN --------------------
async def main():
    logger.info("🚀 Старт polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logger.info("▶ Запуск main.py")
    asyncio.run(main())
