"""Thread-safe event bus for the OpenBiometrics engine.

Supports subscribe/unsubscribe with optional event-type filtering,
non-blocking dispatch via a thread pool, and a bounded recent-event
buffer for retrospective queries.
"""

from __future__ import annotations

import logging
import threading
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from openbiometrics.events.types import Event, EventType

logger = logging.getLogger(__name__)


class EventBus:
    """Publish-subscribe event bus with async dispatch.

    Usage:
        bus = EventBus()

        def on_face(event: Event):
            print(event.to_dict())

        sub_id = bus.subscribe(EventType.FACE_DETECTED, on_face)
        bus.publish(Event(type=EventType.FACE_DETECTED, source="pipeline"))
        bus.unsubscribe(sub_id)
    """

    def __init__(self, max_workers: int = 4, history_size: int = 1000):
        """
        Args:
            max_workers: Thread pool size for async dispatch.
            history_size: Maximum number of recent events to retain.
        """
        self._subscribers: dict[str, tuple[EventType | None, Callable[[Event], None]]] = {}
        self._lock = threading.Lock()
        self._history: deque[Event] = deque(maxlen=history_size)
        self._pool = ThreadPoolExecutor(max_workers=max_workers)

    def subscribe(
        self,
        event_type: EventType | None,
        callback: Callable[[Event], None],
    ) -> str:
        """Register a callback for an event type.

        Args:
            event_type: Type to listen for, or None to receive all events.
            callback: Function invoked with the Event when dispatched.

        Returns:
            Subscription ID used to unsubscribe later.
        """
        sub_id = str(uuid.uuid4())
        with self._lock:
            self._subscribers[sub_id] = (event_type, callback)
        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription.

        Returns:
            True if the subscription existed and was removed.
        """
        with self._lock:
            return self._subscribers.pop(subscription_id, None) is not None

    def publish(self, event: Event) -> None:
        """Dispatch an event to matching subscribers (non-blocking).

        The event is appended to the history buffer and each matching
        subscriber callback is invoked in the thread pool.
        """
        self._history.append(event)

        with self._lock:
            targets = list(self._subscribers.values())

        for event_type, callback in targets:
            if event_type is not None and event_type != event.type:
                continue
            self._pool.submit(self._safe_invoke, callback, event)

    def recent(
        self,
        limit: int = 100,
        event_type: EventType | None = None,
    ) -> list[Event]:
        """Return recent events from the history buffer.

        Args:
            limit: Maximum number of events to return.
            event_type: Filter by type, or None for all.

        Returns:
            List of events, most recent last.
        """
        events: list[Event] = []
        for event in reversed(self._history):
            if event_type is not None and event.type != event_type:
                continue
            events.append(event)
            if len(events) >= limit:
                break
        events.reverse()
        return events

    def shutdown(self) -> None:
        """Shut down the thread pool. Call on application exit."""
        self._pool.shutdown(wait=False)

    @staticmethod
    def _safe_invoke(callback: Callable[[Event], None], event: Event) -> None:
        """Invoke a callback, catching and logging any exceptions."""
        try:
            callback(event)
        except Exception as exc:
            logger.error("Event callback error: %s", exc, exc_info=True)
