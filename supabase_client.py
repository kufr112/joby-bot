"""Lazy Supabase client with dummy fallback.

The original implementation instantiated Supabase on import which could
perform network operations and raised errors when credentials were not
provided.  For fast and predictable startup we create the client only on
first use and return a no-op stub when credentials are missing or set to
``"dummy"``.
"""

from __future__ import annotations

import os
from typing import Any, Callable
import asyncio
from log_utils import logger

from dotenv import load_dotenv
from supabase import Client, create_client


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Temporary debug output to verify credentials are loaded correctly
logger.info("SUPABASE_URL present: %s", bool(SUPABASE_URL))
logger.info("SUPABASE_KEY present: %s", bool(SUPABASE_KEY))


def _is_dummy(value: str) -> bool:
    return not value or value.lower() == "dummy"


class _DummyResponse:
    """Minimal object returned from DummyTable.execute()."""

    data: list[Any] = []


class _DummyTable:
    """Mimic Supabase table/query interface and return empty data."""

    def select(self, *args: Any, **kwargs: Any) -> "_DummyTable":  # noqa: D401
        return self

    def insert(self, *args: Any, **kwargs: Any) -> "_DummyTable":  # noqa: D401
        return self

    def update(self, *args: Any, **kwargs: Any) -> "_DummyTable":  # noqa: D401
        return self

    def eq(self, *args: Any, **kwargs: Any) -> "_DummyTable":  # noqa: D401
        return self

    def execute(self) -> _DummyResponse:  # noqa: D401
        return _DummyResponse()


class _DummySupabase:
    def table(self, name: str) -> _DummyTable:  # noqa: D401
        return _DummyTable()


class LazySupabase:
    """Wrapper that lazily creates the Supabase client."""

    def __init__(self) -> None:
        self._client: Client | None = None
        self.dummy = _is_dummy(SUPABASE_URL) or _is_dummy(SUPABASE_KEY)
        logger.info("Dummy mode: %s", self.dummy)

    def _ensure_client(self) -> Client | _DummySupabase:
        if self.dummy:
            return _DummySupabase()
        if self._client is None:
            logger.info("Creating Supabase client")
            self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return self._client

    def table(self, name: str) -> Any:  # noqa: D401
        return self._ensure_client().table(name)


supabase = LazySupabase()


async def with_supabase_retry(func: Callable[[], Any], max_retries: int = 3) -> Any:
    """Execute ``func`` with retries for transient Supabase errors."""

    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as e:  # pragma: no cover - network depending
            logger.warning(f"Supabase error on attempt {attempt}: {e}")
            if attempt >= max_retries or not any(code in str(e) for code in ("500", "503")):
                raise
            await asyncio.sleep(1)


