## Joby Bot

Telegram-бот для поиска и размещения подработок в Беларуси. Написан на **aiogram 3** и использует **Supabase** как бэкенд.

### Установка
1. Клонируйте репозиторий
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Создайте файл `.env` на основе `.env.example` и заполните переменные:
   - `BOT_TOKEN`
   - `WEBHOOK_HOST`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `ADMIN_ID`
   - `IS_PROD`
4. Запустите локально:
   ```bash
   python main.py
   ```

На Render эти переменные указываются в настройках проекта, бот запускается через `Procfile`.
