
async def on_shutdown(app: web.Application):
    logger.info("🛑 Остановка бота...")
    try:
        if IS_PROD:
            await bot.delete_webhook()
        await bot.session.close()
        logger.info("✅ Сессия закрыта")
    except Exception:
        logger.exception("❌ Ошибка при остановке")

