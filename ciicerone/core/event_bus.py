"""Shared async event bus for Ciicerone color-team communication.

The event bus provides an in-process async pub/sub channel used by the exercise
orchestrator to route events between color teams (Red, Blue, Purple, White,
Black). All events are persisted to the event store for audit trail.

Owner: Ajibola Shokunbi (@jiboo2022) — Core Software Lead
See dev-docs/maintainers/ThreatScene/maintainers/AJIBOLA_SHOKUNBI_CORE_IMPLEMENTATION.md
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from ciicerone.core.event_types import BusEvent, EventType

logger = logging.getLogger(__name__)

EventHandler = Callable[[BusEvent], Any]


class EventBus:
    """In-process async pub/sub event bus with optional persistence.

    The bus is designed to be created once per application and shared across
    all color teams. Handlers can be coroutines or regular functions. Events are
    delivered to handlers concurrently using asyncio.gather.

    Attributes:
        _handlers: Mapping from event type to list of subscribed handlers.
        _event_store: Optional event store for audit persistence.
    """

    def __init__(self, event_store: Optional[Any] = None):
        self._handlers: Dict[EventType, List[EventHandler]] = {
            event_type: [] for event_type in EventType
        }
        self._event_store: Optional[Any] = event_store
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: The event type to subscribe to.
            handler: Callable or coroutine that receives a :class:`BusEvent`.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug("Subscribed handler to %s", event_type.value)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Remove a handler from an event type.

        Args:
            event_type: The event type to unsubscribe from.
            handler: The handler to remove.
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug("Unsubscribed handler from %s", event_type.value)

    def subscribe_many(
        self, event_types: List[EventType], handler: EventHandler
    ) -> None:
        """Register a handler for multiple event types."""
        for event_type in event_types:
            self.subscribe(event_type, handler)

    async def publish(self, event: BusEvent) -> None:
        """Publish an event to all subscribers and optionally persist it.

        Args:
            event: The event to publish.
        """
        logger.debug(
            "Publishing %s for tenant %s", event.event_type.value, event.tenant_id
        )

        # Persist to event store if available
        if self._event_store is not None:
            try:
                await self._persist_event(event)
            except Exception as exc:
                logger.warning("Failed to persist event %s: %s", event.event_id, exc)

        handlers = list(self._handlers.get(event.event_type, []))
        if not handlers:
            return

        # Deliver to handlers concurrently
        results = await asyncio.gather(
            *[self._invoke_handler(handler, event) for handler in handlers],
            return_exceptions=True,
        )

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    "Event handler %s for %s failed: %s",
                    handlers[idx].__name__,
                    event.event_type.value,
                    result,
                )

    async def _invoke_handler(self, handler: EventHandler, event: BusEvent) -> None:
        """Invoke a single handler, supporting both sync and async handlers."""
        result = handler(event)
        if asyncio.iscoroutine(result):
            await result

    async def _persist_event(self, event: BusEvent) -> None:
        """Persist the event to the configured event store."""
        # Avoid leaking optional event store internals into the bus.
        # The event store is expected to have an async append() method.
        append = getattr(self._event_store, "append", None)
        if append is None:
            return
        await append(event.to_dict())

    def get_subscriber_count(self, event_type: EventType) -> int:
        """Return the number of subscribers for an event type."""
        return len(self._handlers.get(event_type, []))
