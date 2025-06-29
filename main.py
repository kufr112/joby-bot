import asyncio
import os
import time

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
from dotenv import load_dotenv

from registration import router as registration_router
from add_job import router as add_job_router
from menu_actions import router as menu_router
from logger_middleware import GlobalLoggerMiddleware
from log_utils import logger
from stats_logger import StatsLogger
from supabase_client import supabase, with_supabase_retry


class DummySession:
    async def close(self) -> None:
        pass


class DummyBot:
    def __init__(self) -> None:
        self.session = DummySession()

    async def set_webhook(self, *args, **kwargs) -> None:
        logger.debug("DummyBot.set_webhook called")

    async def delete_webhook(self, *args, **kwargs) -> None:
        logger.debug("DummyBot.delete_webhook called")

    async def send_message(self, *args, **kwargs) -> None:
        logger.debug("DummyBot.send_message called")

    async def get_updates(self, *args, **kwargs) -> list:
        await asyncio.sleep(0.1)
        return []


START_TIME = time.perf_counter()

# === Загрузка переменных окружения ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
IS_PROD = os.getenv("IS_PROD", "0") == "1"
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None

BOT_DUMMY = not BOT_TOKEN or BOT_TOKEN.lower() == "dummy"
if IS_PROD and not WEBHOOK_HOST:
    raise ValueError("❌ WEBHOOK_HOST не найден в .env для продакшена!")

# === Инициализация бота и диспетчера ===
if BOT_DUMMY:
    bot = DummyBot()
else:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher(storage=MemoryStorage())

# === Регистрация роутеров и middleware ===
dp.include_router(registration_router)
dp.include_router(add_job_router)
dp.include_router(menu_router)
dp.message.middleware(GlobalLoggerMiddleware())


@dp.error()
async def on_error(event, exception):
    logger.exception("Unhandled error", exc_info=exception)
    StatsLogger.log(event="unhandled_error", message=str(exception))


async def periodic_health_check() -> None:
    """Regularly check external services and log issues."""
    while True:
        issues: list[str] = []
        if BOT_DUMMY:
            issues.append("bot_token_missing")
        try:
            if not supabase.dummy:
                await with_supabase_retry(
                    lambda: supabase.table("users").select("id").limit(1).execute(),
                    max_retries=1,
                )
        except Exception as e:
            issues.append("supabase_error")
            StatsLogger.log(event="supabase_error", message=f"health:{e}")
        try:
            if not BOT_DUMMY:
                await bot.get_updates(limit=1, timeout=1)
        except Exception:
            issues.append("telegram_error")
        if issues:
            logger.warning(f"Health check issues: {issues}")
            StatsLogger.log(event="health_check_issue", issues=issues)
        await asyncio.sleep(180)


async def on_startup(app: web.Application):
    logger.info("🚀 Бот запускается...")
    asyncio.create_task(periodic_health_check())

    if IS_PROD and WEBHOOK_URL:
        async def _set_webhook():
            try:
                await bot.set_webhook(WEBHOOK_URL)
                logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")
            except Exception:
                logger.exception("❌ Не удалось установить webhook")

        asyncio.create_task(_set_webhook())

    if ADMIN_ID:
        async def _notify_admin():
            try:
                await bot.send_message(chat_id=ADMIN_ID, text="✅ Бот запущен")
            except Exception:
                logger.warning("⚠️ Не удалось отправить сообщение админу")

        asyncio.create_task(_notify_admin())

    elapsed = time.perf_counter() - START_TIME
    logger.info(f"Startup finished in {elapsed:.2f} sec")
    StatsLogger.log(event="startup_time", seconds=round(elapsed, 2))


async def on_shutdown(app: web.Application):
    logger.info("🛑 Остановка бота...")
    try:
        if IS_PROD:
            await bot.delete_webhook()
        await bot.session.close()
        logger.info("✅ Сессия закрыта")
    except Exception:
        logger.exception("❌ Ошибка при остановке")


async def create_app():
    logger.info("🔧 Инициализация AIOHTTP приложения")
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)

    async def ping(_request: web.Request) -> web.Response:
        return web.Response(text="pong")

    app.router.add_get("/ping", ping)
    return app


app = None
if IS_PROD:
    app = asyncio.run(create_app())

if __name__ == "__main__":
    if IS_PROD:
        web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
    else:
        if BOT_DUMMY:
            logger.info("Running in dummy mode — polling disabled")
            asyncio.run(asyncio.sleep(3600))
        else:
            asyncio.run(dp.start_polling(bot))
