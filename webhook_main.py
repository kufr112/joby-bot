import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import os

from registration import router as registration_router
from add_job import router as add_job_router
from keyboards import menu_keyboard

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # например, https://jobybot.onrender.com
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_routers(registration_router, add_job_router)

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

app = web.Application()
setup_application(app, dp, bot=bot)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    web.run_app(app, host="0.0.0.0", port=8000)
