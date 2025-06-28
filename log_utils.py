import logging
import os
import sys
import traceback
from datetime import datetime


class SupabaseLogHandler(logging.Handler):
    """Send WARNING+ logs to the ``logs`` table in Supabase."""

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - network
        try:
            from supabase_client import supabase  # imported lazily to avoid circular import
            if supabase.dummy:
                return

            message = record.getMessage()
            tb = ""
            if record.exc_info:
                tb = "".join(traceback.format_exception(*record.exc_info))
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": message,
                "traceback": tb,
            }
            supabase.table("logs").insert(entry).execute()
        except Exception:
            # Avoid recursive logging on failure
            pass


def setup_logger() -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/stats.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
            SupabaseLogHandler(level=logging.WARNING),
        ],
    )
    return logging.getLogger(__name__)


logger = setup_logger()


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    from stats_logger import log_to_supabase
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_to_supabase("ERROR", str(exc_value), context={"traceback": tb})


sys.excepthook = handle_exception
