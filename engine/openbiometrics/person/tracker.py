"""IoU-based person tracker.

Implements a simple multi-object tracker using IoU matching and
track lifecycle management (tentative -> confirmed -> lost).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

from openbiometrics.person.detector import DetectedPerson

logger = logging.getLogger(__name__)


@dataclass
class TrackedPerson:
    """A tracked person with temporal state.

    Attributes:
        bbox: Current bounding box (x1, y1, x2, y2).
        confidence: Latest detection confidence.
        class_name: Always "person".
        track_id: Unique integer track identifier.
        trajectory: List of center points over time.
        age: Total number of frames since track creation.
        hits: Number of frames with a matching detection.
        time_since_update: Frames since last matched detection.
    """

    bbox: tuple[float, float, float, float]
    confidence: float
    class_name: str
    track_id: int
    trajectory: list[tuple[float, float]] = field(default_factory=list)
    age: int = 1
    hits: int = 1
    time_since_update: int = 0


class _Track:
    """Internal track representation for lifecycle management."""

    _next_id: int = 1

    def __init__(self, detection: DetectedPerson):
        self.track_id = _Track._next_id
        _Track._next_id += 1

        self.bbox = detection.bbox
        self.confidence = detection.confidence
        self.class_name = detection.class_name
        self.trajectory: list[tuple[float, float]] = [detection.center]
        self.age: int = 1
        self.hits: int = 1
        self.time_since_update: int = 0

    def update(self, detection: DetectedPerson) -> None:
        """Update track with a matched detection."""
        self.bbox = detection.bbox
        self.confidence = detection.confidence
        self.trajectory.append(detection.center)
        self.hits += 1
        self.time_since_update = 0

    def mark_missed(self) -> None:
        """Mark track as unmatched this frame."""
        self.age += 1
        self.time_since_update += 1

    def to_tracked_person(self) -> TrackedPerson:
        return TrackedPerson(
            bbox=self.bbox,
            confidence=self.confidence,
            class_name=self.class_name,
            track_id=self.track_id,
            trajectory=list(self.trajectory),
            age=self.age,
            hits=self.hits,
            time_since_update=self.time_since_update,
        )


def _iou(box_a: tuple[float, float, float, float], box_b: tuple[float, float, float, float]) -> float:
    """Compute Intersection over Union between two bounding boxes."""
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])

    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if inter == 0.0:
        return 0.0

    area_a = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
    area_b = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
    union = area_a + area_b - inter

    return inter / union if union > 0 else 0.0


def _build_cost_matrix(
    tracks: list[_Track],
    detections: list[DetectedPerson],
) -> np.ndarray:
    """Build a cost matrix (1 - IoU) between tracks and detections."""
    n_tracks = len(tracks)
    n_dets = len(detections)
    cost = np.ones((n_tracks, n_dets), dtype=np.float64)

    for t_idx, track in enumerate(tracks):
        for d_idx, det in enumerate(detections):
            cost[t_idx, d_idx] = 1.0 - _iou(track.bbox, det.bbox)

    return cost


def _hungarian_match(
    cost_matrix: np.ndarray,
    iou_threshold: float,
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """Match tracks to detections using the Hungarian algorithm.

    Falls back to greedy matching if scipy is unavailable.

    Returns:
        (matched_pairs, unmatched_track_indices, unmatched_detection_indices)
    """
    n_tracks, n_dets = cost_matrix.shape

    try:
        from scipy.optimize import linear_sum_assignment

        row_ind, col_ind = linear_sum_assignment(cost_matrix)
    except ImportError:
        logger.debug("scipy not available, falling back to greedy matching")
        row_ind, col_ind = _greedy_match(cost_matrix)

    max_cost = 1.0 - iou_threshold  # cost = 1 - iou

    matched: list[tuple[int, int]] = []
    unmatched_tracks = set(range(n_tracks))
    unmatched_dets = set(range(n_dets))

    for r, c in zip(row_ind, col_ind):
        if cost_matrix[r, c] <= max_cost:
            matched.append((r, c))
            unmatched_tracks.discard(r)
            unmatched_dets.discard(c)

    return matched, sorted(unmatched_tracks), sorted(unmatched_dets)


def _greedy_match(cost_matrix: np.ndarray) -> tuple[list[int], list[int]]:
    """Simple greedy matching as fallback when scipy is not available."""
    n_tracks, n_dets = cost_matrix.shape
    row_indices: list[int] = []
    col_indices: list[int] = []

    used_rows: set[int] = set()
    used_cols: set[int] = set()

    # Flatten and sort by cost (ascending)
    flat_indices = np.argsort(cost_matrix, axis=None)
    for flat_idx in flat_indices:
        r = int(flat_idx // n_dets)
        c = int(flat_idx % n_dets)
        if r in used_rows or c in used_cols:
            continue
        row_indices.append(r)
        col_indices.append(c)
        used_rows.add(r)
        used_cols.add(c)
        if len(used_rows) == min(n_tracks, n_dets):
            break

    return row_indices, col_indices


class PersonTracker:
    """IoU-based multi-object tracker for person detections.

    Manages track lifecycle: tentative tracks require `n_init` consecutive
    hits to become confirmed. Confirmed tracks are deleted after
    `max_age` consecutive misses.

    Usage:
        tracker = PersonTracker()
        tracked = tracker.update(detections)
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_age: int = 30,
        n_init: int = 3,
        max_trajectory_len: int = 300,
    ):
        """
        Args:
            iou_threshold: Minimum IoU to match a detection to a track.
            max_age: Delete tracks after this many consecutive misses.
            n_init: Number of hits required to confirm a tentative track.
            max_trajectory_len: Maximum trajectory points to keep per track.
        """
        self._iou_threshold = iou_threshold
        self._max_age = max_age
        self._n_init = n_init
        self._max_trajectory_len = max_trajectory_len
        self._tracks: list[_Track] = []

    def update(self, detections: list[DetectedPerson]) -> list[TrackedPerson]:
        """Update tracker with new detections.

        Args:
            detections: Person detections for the current frame.

        Returns:
            List of confirmed TrackedPerson instances.
        """
        if self._tracks and detections:
            cost_matrix = _build_cost_matrix(self._tracks, detections)
            matched, unmatched_t, unmatched_d = _hungarian_match(
                cost_matrix, self._iou_threshold
            )
        else:
            matched = []
            unmatched_t = list(range(len(self._tracks)))
            unmatched_d = list(range(len(detections)))

        # Update matched tracks
        for t_idx, d_idx in matched:
            self._tracks[t_idx].update(detections[d_idx])
            self._tracks[t_idx].age += 1
            # Trim trajectory
            if len(self._tracks[t_idx].trajectory) > self._max_trajectory_len:
                self._tracks[t_idx].trajectory = self._tracks[t_idx].trajectory[
                    -self._max_trajectory_len :
                ]

        # Mark missed tracks
        for t_idx in unmatched_t:
            self._tracks[t_idx].mark_missed()

        # Create new tracks for unmatched detections
        for d_idx in unmatched_d:
            self._tracks.append(_Track(detections[d_idx]))

        # Remove dead tracks
        self._tracks = [
            t for t in self._tracks if t.time_since_update <= self._max_age
        ]

        # Return confirmed tracks only
        confirmed: list[TrackedPerson] = []
        for track in self._tracks:
            if track.hits >= self._n_init and track.time_since_update == 0:
                confirmed.append(track.to_tracked_person())

        return confirmed

    def reset(self) -> None:
        """Clear all tracks."""
        self._tracks.clear()

    def __repr__(self) -> str:
        return (
            f"PersonTracker(active_tracks={len(self._tracks)}, "
            f"iou_threshold={self._iou_threshold})"
        )
