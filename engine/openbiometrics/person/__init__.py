"""Person detection, tracking, and counting.

Provides YOLO-based person detection, IoU-based multi-object tracking,
and people counting via line crossings and zone occupancy.
"""

from openbiometrics.person.counter import (
    CountResult,
    CrossingEvent,
    LineCrossingCounter,
    PeopleCounter,
    ZoneCounter,
)
from openbiometrics.person.detector import DetectedPerson, PersonDetector
from openbiometrics.person.tracker import PersonTracker, TrackedPerson

__all__ = [
    "PersonDetector",
    "DetectedPerson",
    "PersonTracker",
    "TrackedPerson",
    "LineCrossingCounter",
    "CountResult",
    "CrossingEvent",
    "ZoneCounter",
    "PeopleCounter",
]
