from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any


class EventHub:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._lock = asyncio.Lock()

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "type": event_type,
            "payload": payload,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        async with self._lock:
            subscribers = tuple(self._subscribers)
        for queue in subscribers:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(event)

    async def subscribe(self) -> AsyncIterator[str]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.add(queue)
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20)
                    data = json.dumps(event, ensure_ascii=False)
                    yield f"event: {event['type']}\ndata: {data}\n\n"
                except TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            async with self._lock:
                self._subscribers.discard(queue)
