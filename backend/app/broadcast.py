from __future__ import annotations

import asyncio
import logging
from typing import List

from .models import Event

logger = logging.getLogger("app.broadcast")


class Broadcaster:
    """A tiny pub/sub for WebSocket clients.

    Each subscriber gets its own bounded asyncio.Queue to avoid a slow client
    blocking everyone else. If a queue is full, we drop events for that client.
    """

    def __init__(self, queue_size: int = 50) -> None:
        self._queue_size = queue_size
        self._subscribers: List[asyncio.Queue[Event]] = []
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=self._queue_size)
        async with self._lock:
            self._subscribers.append(queue)
            logger.info("subscriber connected (total=%s)", len(self._subscribers))
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[Event]) -> None:
        async with self._lock:
            if queue in self._subscribers:
                self._subscribers.remove(queue)
            logger.info("subscriber disconnected (total=%s)", len(self._subscribers))

    async def broadcast(self, event: Event) -> None:
        async with self._lock:
            for q in list(self._subscribers):
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    # Drop events for slow clients rather than blocking the system.
                    pass
