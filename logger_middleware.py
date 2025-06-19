from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from datetime import datetime

class GlobalLoggerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        text = getattr(event, "text", "") or getattr(event, "data", "") or str(event)

        with open("actions.log", "a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{user.id if user else '??'} ({user.username if user else '-'}) → {text}\n"
            )

        return await handler(event, data)
