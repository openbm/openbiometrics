"""People counting: line crossing and zone occupancy.

Provides LineCrossingCounter for directional counting across a virtual
line, ZoneCounter for occupancy within a polygon, and PeopleCounter
that combines both.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from openbiometrics.person.tracker import TrackedPerson


@dataclass
class CrossingEvent:
    """A single line-crossing event.

    Attributes:
        track_id: ID of the track that crossed the line.
        direction: "in" or "out" relative to the line normal.
        timestamp: Unix timestamp when the crossing was detected.
    """

    track_id: int
    direction: str  # "in" or "out"
    timestamp: float


@dataclass
class CountResult:
    """Result from a line crossing counter update.

    Attributes:
        in_count: Cumulative count of "in" crossings.
        out_count: Cumulative count of "out" crossings.
        total_crossings: Total crossings (in + out).
        events: New crossing events detected in this update.
    """

    in_count: int
    out_count: int
    total_crossings: int
    events: list[CrossingEvent] = field(default_factory=list)


def _cross_product_sign(
    line_start: tuple[float, float],
    line_end: tuple[float, float],
    point: tuple[float, float],
) -> float:
    """Compute the sign of the cross product (line_end - line_start) x (point - line_start).

    Positive means point is to the left of the line, negative to the right.
    """
    dx = line_end[0] - line_start[0]
    dy = line_end[1] - line_start[1]
    px = point[0] - line_start[0]
    py = point[1] - line_start[1]
    return dx * py - dy * px


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    """Ray casting algorithm for point-in-polygon test.

    Casts a ray from the point to the right and counts edge crossings.
    An odd count means the point is inside the polygon.
    """
    x, y = point
    n = len(polygon)
    inside = False

    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]

        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i

    return inside


class LineCrossingCounter:
    """Counts people crossing a virtual line.

    Detects when a tracked person's trajectory crosses the defined line
    and classifies the direction as "in" or "out" based on which side
    of the line the person moved to.

    Usage:
        counter = LineCrossingCounter(line_start=(100, 300), line_end=(500, 300))
        result = counter.update(tracked_persons)
        print(f"In: {result.in_count}, Out: {result.out_count}")
    """

    def __init__(
        self,
        line_start: tuple[float, float],
        line_end: tuple[float, float],
    ):
        """
        Args:
            line_start: Start point (x, y) of the counting line.
            line_end: End point (x, y) of the counting line.
        """
        self._line_start = line_start
        self._line_end = line_end
        self._in_count = 0
        self._out_count = 0
        # Track the last known side for each track_id to detect crossings
        self._last_side: dict[int, float] = {}

    def update(self, tracked: list[TrackedPerson]) -> CountResult:
        """Check for new line crossings.

        Args:
            tracked: List of tracked persons from PersonTracker.

        Returns:
            CountResult with cumulative counts and new events.
        """
        events: list[CrossingEvent] = []
        active_ids: set[int] = set()

        for person in tracked:
            active_ids.add(person.track_id)

            if len(person.trajectory) < 2:
                # Need at least 2 points to detect crossing
                current_side = _cross_product_sign(
                    self._line_start, self._line_end, person.trajectory[-1]
                )
                self._last_side[person.track_id] = current_side
                continue

            # Check the last two trajectory points for a crossing
            prev_point = person.trajectory[-2]
            curr_point = person.trajectory[-1]

            prev_side = _cross_product_sign(self._line_start, self._line_end, prev_point)
            curr_side = _cross_product_sign(self._line_start, self._line_end, curr_point)

            # A crossing occurs when the sign changes (and neither is zero)
            if prev_side != 0 and curr_side != 0 and (prev_side > 0) != (curr_side > 0):
                # Check that we haven't already counted this crossing
                last_known = self._last_side.get(person.track_id)
                if last_known is None or (last_known > 0) != (curr_side > 0):
                    direction = "in" if curr_side > 0 else "out"
                    event = CrossingEvent(
                        track_id=person.track_id,
                        direction=direction,
                        timestamp=time.time(),
                    )
                    events.append(event)

                    if direction == "in":
                        self._in_count += 1
                    else:
                        self._out_count += 1

            self._last_side[person.track_id] = curr_side

        # Clean up stale track IDs
        stale = [tid for tid in self._last_side if tid not in active_ids]
        for tid in stale:
            del self._last_side[tid]

        return CountResult(
            in_count=self._in_count,
            out_count=self._out_count,
            total_crossings=self._in_count + self._out_count,
            events=events,
        )

    def reset(self) -> None:
        """Reset all counts and state."""
        self._in_count = 0
        self._out_count = 0
        self._last_side.clear()

    def __repr__(self) -> str:
        return (
            f"LineCrossingCounter(in={self._in_count}, out={self._out_count}, "
            f"line={self._line_start}->{self._line_end})"
        )


class ZoneCounter:
    """Counts people currently inside a polygon zone.

    Uses ray casting to determine if a tracked person's center point
    is within the defined polygon.

    Usage:
        zone = ZoneCounter(polygon=[(100, 100), (400, 100), (400, 400), (100, 400)])
        count = zone.update(tracked_persons)
    """

    def __init__(self, polygon: list[tuple[float, float]]):
        """
        Args:
            polygon: List of (x, y) vertices defining the zone polygon.
                     Must have at least 3 vertices.
        """
        if len(polygon) < 3:
            raise ValueError("Polygon must have at least 3 vertices")
        self._polygon = polygon

    def update(self, tracked: list[TrackedPerson]) -> int:
        """Count people currently inside the zone.

        Args:
            tracked: List of tracked persons from PersonTracker.

        Returns:
            Number of tracked persons whose center is inside the polygon.
        """
        count = 0
        for person in tracked:
            if not person.trajectory:
                continue
            center = person.trajectory[-1]
            if _point_in_polygon(center, self._polygon):
                count += 1
        return count

    def get_persons_in_zone(self, tracked: list[TrackedPerson]) -> list[TrackedPerson]:
        """Return the list of tracked persons currently inside the zone.

        Args:
            tracked: List of tracked persons from PersonTracker.

        Returns:
            Filtered list of persons inside the polygon.
        """
        result: list[TrackedPerson] = []
        for person in tracked:
            if not person.trajectory:
                continue
            center = person.trajectory[-1]
            if _point_in_polygon(center, self._polygon):
                result.append(person)
        return result

    def __repr__(self) -> str:
        return f"ZoneCounter(vertices={len(self._polygon)})"


class PeopleCounter:
    """Combined people counter with line crossings and zone counting.

    Manages multiple line counters and zone counters for a scene.

    Usage:
        counter = PeopleCounter()
        counter.add_line("entrance", (100, 300), (500, 300))
        counter.add_zone("lobby", [(0, 0), (200, 0), (200, 200), (0, 200)])
        line_results, zone_counts = counter.update(tracked_persons)
    """

    def __init__(self) -> None:
        self._lines: dict[str, LineCrossingCounter] = {}
        self._zones: dict[str, ZoneCounter] = {}

    def add_line(
        self,
        name: str,
        line_start: tuple[float, float],
        line_end: tuple[float, float],
    ) -> None:
        """Add a line crossing counter.

        Args:
            name: Identifier for this line counter.
            line_start: Start point (x, y) of the counting line.
            line_end: End point (x, y) of the counting line.
        """
        self._lines[name] = LineCrossingCounter(line_start, line_end)

    def add_zone(
        self,
        name: str,
        polygon: list[tuple[float, float]],
    ) -> None:
        """Add a zone counter.

        Args:
            name: Identifier for this zone counter.
            polygon: List of (x, y) vertices defining the zone.
        """
        self._zones[name] = ZoneCounter(polygon)

    def update(
        self,
        tracked: list[TrackedPerson],
    ) -> tuple[dict[str, CountResult], dict[str, int]]:
        """Update all counters with tracked persons.

        Args:
            tracked: List of tracked persons from PersonTracker.

        Returns:
            Tuple of (line_results, zone_counts) where line_results maps
            line names to CountResult and zone_counts maps zone names
            to occupancy counts.
        """
        line_results: dict[str, CountResult] = {}
        for name, counter in self._lines.items():
            line_results[name] = counter.update(tracked)

        zone_counts: dict[str, int] = {}
        for name, zone in self._zones.items():
            zone_counts[name] = zone.update(tracked)

        return line_results, zone_counts

    def remove_line(self, name: str) -> None:
        """Remove a line crossing counter by name."""
        self._lines.pop(name, None)

    def remove_zone(self, name: str) -> None:
        """Remove a zone counter by name."""
        self._zones.pop(name, None)

    def reset(self) -> None:
        """Reset all counters."""
        for counter in self._lines.values():
            counter.reset()

    def __repr__(self) -> str:
        return (
            f"PeopleCounter(lines={list(self._lines.keys())}, "
            f"zones={list(self._zones.keys())})"
        )
