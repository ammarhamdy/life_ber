import time
import asyncio


class RateLimiter:
    """
    Ensures that operations are executed no more frequently than the
    configured minimum interval.

    This limiter serializes concurrent callers and guarantees that each
    successful acquisition is separated from the previous one by at least
    `min_interval` seconds.
    """

    def __init__(self, min_interval: float) -> None:
        #: Minimum number of seconds that must elapse between acquisitions.
        self._min_interval = min_interval

        #: Monotonic timestamp of the most recent successful acquisition.
        self._last_called: float = 0.0

        #: Synchronizes access to limiter state across concurrent coroutines.
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Wait until the configured rate limit allows the caller to proceed.

        Guarantees:
        - Only one coroutine updates limiter state at a time.
        - Consecutive acquisitions are separated by at least
          `self._min_interval` seconds.
        - Returns immediately when the required interval has already elapsed.
        """
        async with self._lock:
            elapsed = time.monotonic() - self._last_called
            wait = self._min_interval - elapsed

            if wait > 0:
                await asyncio.sleep(wait)

            self._last_called = time.monotonic()
