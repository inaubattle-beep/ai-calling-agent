import asyncio
import json
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional
from datetime import datetime, timezone

from ..config import settings
from ..schemas.event import SystemEvent

logger = logging.getLogger("event.bus")


class EventBus:
    """
    Central event dispatcher supporting Redis Pub/Sub and In-Memory Queue fallback.
    Broadcasts real-time call states, agent status, and audio/transcript events.
    """

    def __init__(self, redis_url: Optional[str] = None) -> None:
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis_client = None
        self._subscribers: List[Callable[[SystemEvent], Coroutine[Any, Any, None]]] = []
        self._recent_events: List[SystemEvent] = []
        self._max_recent = 100
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._running = True
        if self.redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
                await self._redis_client.ping()
                logger.info(f"Connected to Redis Pub/Sub at {self.redis_url}")
                self._listen_task = asyncio.create_task(self._listen_redis())
            except Exception as e:
                logger.warning(f"Failed to connect to Redis ({e}); falling back to In-Memory EventBus")
                self._redis_client = None
        else:
            logger.info("Using In-Memory EventBus for local development")

    async def stop(self) -> None:
        self._running = False
        if self._listen_task:
            self._listen_task.cancel()
        if self._redis_client:
            await self._redis_client.close()

    def subscribe(self, handler: Callable[[SystemEvent], Coroutine[Any, Any, None]]) -> None:
        self._subscribers.append(handler)

    def unsubscribe(self, handler: Callable[[SystemEvent], Coroutine[Any, Any, None]]) -> None:
        if handler in self._subscribers:
            self._subscribers.remove(handler)

    async def publish(
        self,
        event_name: str,
        data: Dict[str, Any],
        call_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> SystemEvent:
        event = SystemEvent(
            event=event_name,
            call_id=call_id or data.get("call_id"),
            agent_id=agent_id or data.get("agent_id"),
            data=data,
            timestamp=datetime.now(timezone.utc),
        )

        # Retain in recent events buffer
        self._recent_events.append(event)
        if len(self._recent_events) > self._max_recent:
            self._recent_events.pop(0)

        # Publish to Redis if available
        if self._redis_client:
            try:
                payload = json.dumps({
                    "id": event.id,
                    "event": event.event,
                    "call_id": event.call_id,
                    "agent_id": event.agent_id,
                    "data": event.data,
                    "timestamp": event.timestamp.isoformat(),
                })
                await self._redis_client.publish("call_events", payload)
            except Exception as e:
                logger.error(f"Redis publish error: {e}")

        # Dispatch to local subscribers (FastAPI WebSockets)
        await self._dispatch_local(event)
        return event

    async def _dispatch_local(self, event: SystemEvent) -> None:
        for handler in list(self._subscribers):
            try:
                await handler(event)
            except Exception as e:
                logger.debug(f"Error dispatching event to subscriber: {e}")

    async def _listen_redis(self) -> None:
        try:
            pubsub = self._redis_client.pubsub()
            await pubsub.subscribe("call_events")
            while self._running:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    raw = json.loads(message["data"])
                    event = SystemEvent(
                        id=raw["id"],
                        event=raw["event"],
                        call_id=raw.get("call_id"),
                        agent_id=raw.get("agent_id"),
                        data=raw.get("data", {}),
                        timestamp=datetime.fromisoformat(raw["timestamp"]),
                    )
                    await self._dispatch_local(event)
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis listener error: {e}")

    def get_recent_events(self, limit: int = 50) -> List[SystemEvent]:
        return list(reversed(self._recent_events))[:limit]


# Global singleton event bus
event_bus = EventBus()
