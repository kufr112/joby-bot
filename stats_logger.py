import json
from datetime import datetime
from pathlib import Path
from typing import Any

from supabase_client import supabase


class StatsLogger:
    """Simple event logger for monitoring bot statistics."""

    path = Path("logs/stats.log")

    @classmethod
    def log(cls, event: str, **data) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            **data,
        }
        cls.path.parent.mkdir(exist_ok=True)
        with cls.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        log_to_supabase("ACTION", event, details=data)


def log_to_supabase(type_: str, message: str, details: Any | None = None) -> None:
    """Send a log record to the ``logs`` table in Supabase."""
    try:
        if supabase.dummy:
            return
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": type_,
            "message": message,
            "details": details,
        }
        supabase.table("logs").insert(entry).execute()
    except Exception:
        # Ignore logging failures to avoid interfering with bot
        pass
