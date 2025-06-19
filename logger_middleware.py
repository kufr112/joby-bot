from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from datetime import datetime
import json
import logging

class GlobalLoggerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            user = getattr(event, "from_user", None)
            event_type = type(event).__name__
            content = {}

            # Пробуем вытащить максимально подробное содержимое
            if isinstance(event, Message):
                content = {
                    "message_id": event.message_id,
                    "text": event.text,
                    "caption": event.caption,
                    "chat_id": event.chat.id,
                    "chat_type": event.chat.type,
                    "content_type": event.content_type,
                }
                if event.photo:
                    content["photo"] = f"{len(event.photo)} images"
                if event.document:
                    content["document"] = event.document.file_name

            elif isinstance(event, CallbackQuery):
                content = {
                    "data": event.data,
                    "message_id": event.message.message_id if event.message else None
                }

            else:
                content = str(event)

            log_entry = {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "user_id": user.id if user else None,
                "username": user.username if user else None,
                "event_type": event_type,
                "content": content
            }

            with open("actions.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        except Exception as e:
            logging.exception(f"Ошибка в GlobalLoggerMiddleware: {e}")

        return await handler(event, data)
