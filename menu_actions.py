from aiogram import Router
from aiogram.types import Message

from keyboards import menu_keyboard
from stats_logger import StatsLogger

router = Router()

@router.message(lambda m: m.text and "найти подработку" in m.text.lower())
async def find_job(message: Message) -> None:
    StatsLogger.log(event="click_find_job")
    await message.answer("🔍 Поиск подработок пока не реализован.", reply_markup=menu_keyboard)

@router.message(lambda m: m.text and "мои объявления" in m.text.lower())
async def my_jobs(message: Message) -> None:
    StatsLogger.log(event="click_my_jobs")
    await message.answer("ℹ️ Раздел 'Мои объявления' пока не готов.", reply_markup=menu_keyboard)
