from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Главное меню, общее для всех пользователей
menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📢 Найти подработку"),
            KeyboardButton(text="➕ Разместить подработку"),
        ],
        [
            KeyboardButton(text="🧾 Мои объявления"),
            KeyboardButton(text="🔔 Подписки / уведомления"),
        ],
        [
            KeyboardButton(text="👤 Профиль / Настройки"),
            KeyboardButton(text="ℹ️ Помощь / FAQ"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие ⤵️",
)

# Кнопка начала регистрации
register_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔐 Зарегистрироваться")]],
    resize_keyboard=True,
)

# Кнопки для выбора способа отправки телефона
phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📞 Отправить номер из Telegram", request_contact=True)],
        [KeyboardButton(text="✍️ Ввести вручную")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# Удаление клавиатуры
remove_keyboard = ReplyKeyboardRemove()
