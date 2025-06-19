import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
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
logging.basicConfig(
    level=logging.INFO,
    format="📘 [%(asctime)s] [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# === Загрузка .env ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
IS_PROD = os.getenv("IS_PROD", "1") == "1"

# === Проверка переменных ===
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден!")
if not WEBHOOK_HOST:
    raise ValueError("❌ WEBHOOK_HOST не найден!")

# === Инициализация бота и диспетчера ===
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# === Подключение роутеров ===
dp.include_router(registration_router)
dp.include_router(add_job_router)
dp.include_router(actions_router)

# === Middleware ===
dp.message.middleware(GlobalLoggerMiddleware())

# === Логирование всех апдейтов
@dp.update.outer_middleware()
async def log_incoming_updates(handler, event, data):
    logger.info(f"📥 Получен апдейт: {event}")
    return await handler(event, data)

# === Webhook хуки ===
async def on_startup(bot: Bot):
    logger.info("🚀 on_startup...")
    try:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")
    except Exception as e:
        logger.exception(f"❌ Ошибка установки webhook: {e}")

    if IS_PROD:
        try:
            await bot.send_message(chat_id=853076774, text="✅ Бот запущен и webhook установлен!")
            logger.info("📤 Уведомление о запуске успешно отправлено")
        except Exception as e:
            logger.exception("⚠️ Ошибка при отправке уведомления в Telegram")

async def on_shutdown(bot: Bot):
    logger.info("🛑 Остановка... удаляю webhook")
    try:
        await bot.delete_webhook()
        await bot.session.close()
        logger.info("✅ Webhook удалён и сессия закрыта")
    except Exception as e:
        logger.exception("❌ Ошибка при удалении webhook")

# === Создание AIOHTTP приложения ===
async def create_app():
    logger.info("🔧 Создаю AIOHTTP приложение...")
    app = web.Application()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    setup_application(app, dp, handle_class=SimpleRequestHandler, bot=bot, path=WEBHOOK_PATH)
    logger.info("📡 Webhook обработчик активен")
    return app

# === Точка входа ===
if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 10000))
        logger.info(f"🌐 Запускаю на порту {port}")
        app = asyncio.run(create_app())
        web.run_app(app, port=port)
    except Exception as e:
        logger.exception("❌ Ошибка запуска:")
