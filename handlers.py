from aiogram import Router, types, F
from aiogram.types import Message
from keyboards import menu_keyboard  # ✅ reply-клавиатура

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Добро пожаловать в Joby Bot.\nВыберите действие ниже ⤵️",
        reply_markup=menu_keyboard
    )

# ⛔ Inline-меню отключено, но обработчики оставлены на будущее:

@router.callback_query(F.data == "profile")
async def show_profile(callback: types.CallbackQuery):
    await callback.message.edit_text("👤 Здесь будет информация о твоём профиле.")
    await callback.answer()

@router.callback_query(F.data == "settings")
async def show_settings(callback: types.CallbackQuery):
    await callback.message.edit_text("⚙️ Настройки пока в разработке.")
    await callback.answer()

@router.callback_query(F.data == "subscription")
async def show_subscription(callback: types.CallbackQuery):
    await callback.message.edit_text("⭐ Здесь будет информация о подписке.")
    await callback.answer()

@router.callback_query(F.data == "my_jobs")
async def show_my_jobs(callback: types.CallbackQuery):
    await callback.message.edit_text("📋 Здесь будут отображаться твои подработки.")
    await callback.answer()

@router.callback_query(F.data == "back")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("👋 Добро пожаловать обратно.")
    await callback.answer()
