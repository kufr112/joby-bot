import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import setup_application, SimpleRequestHandler
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
from dotenv import load_dotenv

from registration import router as registration_router
from add_job import router as add_job_router
from actions import router as actions_router
from logger_middleware import GlobalLoggerMiddleware

# === Логирование ===
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("📘 [%(asctime)s] [%(levelname)s] %(message)s")

file_handler = logging.FileHandler("full_debug.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# === Загрузка .env переменных ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # пример: https://bot-name.onrender.com
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
IS_PROD = os.getenv("IS_PROD", "1") == "1"

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env!")
if not WEBHOOK_HOST:
    raise ValueError("❌ WEBHOOK_HOST не найден в .env!")

# === Инициализация бота и диспетчера ===
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# === Роутеры ===
dp.include_router(registration_router)
dp.include_router(add_job_router)
dp.include_router(actions_router)

# === Middleware ===
dp.message.middleware(GlobalLoggerMiddleware())

# === Логирование входящих обновлений ===
@dp.update.outer_middleware()
async def log_incoming_updates(handler, event, data):
    logger.debug(f"📥 [Update] Тип: {type(event)} | Содержимое: {event}")
    return await handler(event, data)

# === Запуск при старте (установка webhook и сообщение) ===
async def on_startup(bot: Bot):
    logger.info("🚀 Бот запускается...")
    try:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")
    except Exception as e:
        logger.exception("❌ Не удалось установить webhook")

    if IS_PROD:
        try:
            await bot.send_message(chat_id=853076774, text="✅ Бот запущен и Webhook активен!")
        except Exception as e:
            logger.warning("⚠️ Не удалось отправить уведомление в Telegram")

# === Остановка (удаление webhook) ===
async def on_shutdown(bot: Bot):
    logger.info("🛑 Остановка бота...")
    try:
        await bot.delete_webhook()
        await bot.session.close()
        logger.info("✅ Webhook удалён, сессия закрыта")
    except Exception as e:
        logger.exception("❌ Ошибка при удалении webhook")

# === Создание aiohttp приложения ===
async def create_app():
    logger.info("🔧 Создание AIOHTTP приложения...")
    app = web.Application()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    setup_application(app, dp, handle_class=SimpleRequestHandler, bot=bot, path=WEBHOOK_PATH)
    return app

# === Запуск сервера ===
if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 10000))
        logger.info(f"🌍 Запуск приложения на порту {port}")
        app = asyncio.run(create_app())
        web.run_app(app, port=port)
    except Exception as e:
        logger.exception("❌ Ошибка при запуске сервера")
