import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import setup_application, SimpleRequestHandler
from aiohttp import web
from dotenv import load_dotenv

from registration import router as registration_router
from add_job import router as add_job_router
from actions import router as actions_router
from logger_middleware import GlobalLoggerMiddleware

# === Загрузка переменных окружения ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# === Проверка токена ===
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env или переменных окружения")

# === Настройка логов ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Создание бота и диспетчера ===
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# === Подключение роутеров ===
dp.include_router(registration_router)
dp.include_router(add_job_router)
dp.include_router(actions_router)

# === Middleware ===
dp.message.middleware(GlobalLoggerMiddleware())

# === Webhook: запуск и остановка ===
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logger.info("🛑 Webhook удалён")

# === Основной запуск ===
async def create_app():
    app = web.Application()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    setup_application(app, dp, handle_class=SimpleRequestHandler, bot=bot, path=WEBHOOK_PATH)

    logger.info("🚀 Бот с webhook запущен!")
    return app

# Для Render нужен именно create_app()
app = asyncio.run(create_app()) if __name__ == "__main__" else create_app()
