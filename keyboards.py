from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔍 Найти подработку"),
            KeyboardButton(text="➕ Разместить подработку")
        ],
        [
            KeyboardButton(text="🧾 Мои объявления"),
            KeyboardButton(text="📌 Подписки")
        ],
        [
            KeyboardButton(text="👤 Профиль / Настройки"),
            KeyboardButton(text="💬 Помощь / FAQ")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие ⤵️"
)
