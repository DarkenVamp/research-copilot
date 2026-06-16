"""
In-process pub/sub for streaming workflow events to SSE subscribers.

A single backend process is assumed (fine for this assignment). Scaling to
multiple workers would swap this for Redis pub/sub or Postgres LISTEN/NOTIFY
behind the same interface.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict


class PubSub:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)

    def subscribe(self, session_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[session_id].add(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        subs = self._subscribers.get(session_id)
        if subs and queue in subs:
            subs.discard(queue)
            if not subs:
                self._subscribers.pop(session_id, None)

    async def publish(self, session_id: str, message: dict) -> None:
        for queue in list(self._subscribers.get(session_id, ())):
            await queue.put(message)


pubsub = PubSub()
