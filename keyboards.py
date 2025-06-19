from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📢 Найти подработку"),
            KeyboardButton(text="➕ Разместить подработку")
        ],
        [
            KeyboardButton(text="🧾 Мои публикации"),
            KeyboardButton(text="👤 Профиль / Настройки")
        ],
        [
            KeyboardButton(text="📌 Подписки"),
            KeyboardButton(text="💬 Помощь / FAQ")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие ⤵️"
)