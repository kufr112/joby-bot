## Joby Bot

Telegram-бот для поиска и размещения подработок в Беларуси. Написан на **Aiogram 3** и использует **Supabase** как бэкенд.

При первом запуске бот предлагает пройти простую регистрацию: указать имя, город и номер телефона. Номер можно отправить контактом из Telegram или ввести вручную.  
Все данные сохраняются в таблицу `users` Supabase.

### Установка
1. Клонируйте репозиторий  
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt

   ```
3. Скопируйте `.env.example` в `.env` и укажите реальные значения. Обязательно
   задайте `BOT_TOKEN` — токен вашего Telegram-бота.
4. Запустите бот локально:
   ```bash
   python main.py
   ```
