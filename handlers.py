from aiogram import Router, F
from aiogram.types import Message
from keyboards import menu_keyboard  # reply-клавиатура снизу

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Добро пожаловать в Joby Bot.\nВыберите действие ниже ⤵️",
        reply_markup=menu_keyboard
    )
