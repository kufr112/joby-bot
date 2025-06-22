from aiogram import Router, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Главное меню
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
    [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
    [InlineKeyboardButton(text="⭐ Подписка", callback_data="subscription")],
    [InlineKeyboardButton(text="📋 Мои подработки", callback_data="my_jobs")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
])

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Добро пожаловать в Joby Bot.\nВыбери нужный пункт из меню:",
        reply_markup=main_menu
    )

@router.callback_query(F.data == "profile")
async def show_profile(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text="👤 Здесь будет информация о твоём профиле.",
        reply_markup=main_menu
    )

@router.callback_query(F.data == "settings")
async def show_settings(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text="⚙️ Настройки пока в разработке.",
        reply_markup=main_menu
    )

@router.callback_query(F.data == "subscription")
async def show_subscription(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text="⭐ Здесь будет информация о подписке.",
        reply_markup=main_menu
    )

@router.callback_query(F.data == "my_jobs")
async def show_my_jobs(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text="📋 Здесь будут отображаться твои подработки.",
        reply_markup=main_menu
    )

@router.callback_query(F.data == "back")
async def back_to_menu(callback: types.CallbackQuery):
    await cmd_start(callback.message)
    await callback.answer()
