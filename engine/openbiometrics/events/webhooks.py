"""Webhook dispatcher for the OpenBiometrics event system.

Listens to an EventBus and POSTs JSON payloads to registered
webhook URLs. Supports HMAC-SHA256 signing and automatic retries
with exponential backoff.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import urllib.request
import urllib.error
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from openbiometrics.events.bus import EventBus
from openbiometrics.events.types import Event, EventType

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BACKOFF_SECONDS = (1, 2, 4)


@dataclass
class WebhookConfig:
    """Registered webhook configuration."""

    id: str
    url: str
    event_types: list[EventType]
    secret: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered: datetime | None = None
    failure_count: int = 0


class WebhookDispatcher:
    """Dispatches events to registered webhook URLs.

    Subscribes to an EventBus for all events and forwards matching
    events to each registered webhook endpoint via HTTP POST.

    Usage:
        bus = EventBus()
        dispatcher = WebhookDispatcher(bus)
        wh_id = dispatcher.register(
            "https://example.com/hook",
            [EventType.FACE_MATCHED, EventType.WATCHLIST_ALERT],
            secret="my-secret",
        )
    """

    def __init__(self, bus: EventBus):
        self._bus = bus
        self._webhooks: dict[str, WebhookConfig] = {}
        self._sub_id = bus.subscribe(None, self._on_event)

    def register(
        self,
        url: str,
        event_types: list[EventType],
        secret: str | None = None,
    ) -> str:
        """Register a new webhook endpoint.

        Args:
            url: Target URL for the POST request.
            event_types: Event types that trigger this webhook.
            secret: Optional HMAC-SHA256 secret for payload signing.

        Returns:
            Webhook ID.
        """
        webhook_id = str(uuid.uuid4())
        self._webhooks[webhook_id] = WebhookConfig(
            id=webhook_id,
            url=url,
            event_types=list(event_types),
            secret=secret,
        )
        return webhook_id

    def unregister(self, webhook_id: str) -> bool:
        """Remove a registered webhook.

        Returns:
            True if the webhook existed and was removed.
        """
        return self._webhooks.pop(webhook_id, None) is not None

    def list_webhooks(self) -> list[WebhookConfig]:
        """Return all registered webhooks."""
        return list(self._webhooks.values())

    def shutdown(self) -> None:
        """Unsubscribe from the event bus."""
        self._bus.unsubscribe(self._sub_id)

    def _on_event(self, event: Event) -> None:
        """Event bus callback — forward to matching webhooks."""
        for webhook in list(self._webhooks.values()):
            if event.type not in webhook.event_types:
                continue
            self._deliver(webhook, event)

    def _deliver(self, webhook: WebhookConfig, event: Event) -> None:
        """POST the event payload to a webhook URL with retries."""
        payload = json.dumps(event.to_dict()).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        if webhook.secret is not None:
            signature = hmac.new(
                webhook.secret.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).hexdigest()
            headers["X-Signature-SHA256"] = signature

        for attempt in range(_MAX_RETRIES):
            try:
                req = urllib.request.Request(
                    webhook.url,
                    data=payload,
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp.read()
                webhook.last_triggered = datetime.now(timezone.utc)
                webhook.failure_count = 0
                return
            except (urllib.error.URLError, OSError) as exc:
                logger.warning(
                    "Webhook %s attempt %d/%d failed: %s",
                    webhook.id,
                    attempt + 1,
                    _MAX_RETRIES,
                    exc,
                )
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_BACKOFF_SECONDS[attempt])

        webhook.failure_count += 1
        logger.error(
            "Webhook %s delivery failed after %d attempts (total failures: %d)",
            webhook.id,
            _MAX_RETRIES,
            webhook.failure_count,
        )
