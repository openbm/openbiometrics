"""Event type definitions for the OpenBiometrics event system.

Defines the canonical event types emitted by processing modules
and the Event dataclass used as the universal event envelope.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class EventType(Enum):
    """Canonical event types emitted by the OpenBiometrics engine."""

    FACE_DETECTED = "face_detected"
    FACE_MATCHED = "face_matched"
    WATCHLIST_ALERT = "watchlist_alert"
    LIVENESS_PASSED = "liveness_passed"
    LIVENESS_FAILED = "liveness_failed"
    DOCUMENT_SCANNED = "document_scanned"
    PERSON_ENTERED = "person_entered"
    PERSON_EXITED = "person_exited"
    LINE_CROSSED = "line_crossed"
    SYSTEM_ERROR = "system_error"


@dataclass
class Event:
    """Universal event envelope for the OpenBiometrics engine.

    Attributes:
        id: Unique event identifier (auto-generated UUID4).
        type: The canonical event type.
        timestamp: UTC timestamp of when the event occurred.
        source: Identifier of the module that produced the event.
        data: Arbitrary payload dict specific to the event type.
        camera_id: Optional camera/stream identifier.
    """

    type: EventType
    source: str
    data: dict = field(default_factory=dict)
    camera_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serialize the event to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data,
            "camera_id": self.camera_id,
        }
