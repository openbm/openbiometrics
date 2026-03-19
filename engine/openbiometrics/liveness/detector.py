"""Action detection for active liveness challenges.

Given a FaceMesh and a ChallengeType, determines whether the user
has performed the requested action (blink, head turn, smile, etc.)
and returns a confidence score.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from openbiometrics.liveness.challenges import ChallengeType
from openbiometrics.liveness.landmarks import FaceMesh

logger = logging.getLogger(__name__)


@dataclass
class ActionThresholds:
    """Configurable thresholds for each challenge type.

    All angle values are in degrees.  Aspect-ratio values are unitless
    ratios derived from landmark distances.
    """

    blink_ear: float = 0.2
    """EAR below this value counts as a blink (either eye)."""

    smile_mouth_width_ratio: float = 0.42
    """Mouth width / face width ratio above this counts as a smile."""

    open_mouth_mar: float = 0.6
    """Mouth aspect ratio above this counts as mouth open."""

    turn_left_yaw: float = -15.0
    """Yaw below this (degrees) counts as turning left."""

    turn_right_yaw: float = 15.0
    """Yaw above this (degrees) counts as turning right."""

    look_up_pitch: float = -10.0
    """Pitch below this (degrees) counts as looking up."""

    look_down_pitch: float = 10.0
    """Pitch above this (degrees) counts as looking down."""


class ActionDetector:
    """Checks whether a FaceMesh satisfies a given challenge.

    Usage:
        detector = ActionDetector()
        passed, confidence = detector.check(mesh, ChallengeType.BLINK)
    """

    def __init__(self, thresholds: ActionThresholds | None = None):
        """
        Args:
            thresholds: Custom detection thresholds. Uses defaults if None.
        """
        self._t = thresholds or ActionThresholds()

    def check(self, mesh: FaceMesh, challenge_type: ChallengeType) -> tuple[bool, float]:
        """Evaluate whether *mesh* satisfies *challenge_type*.

        Args:
            mesh: FaceMesh produced by FaceMeshDetector.detect().
            challenge_type: The challenge to verify.

        Returns:
            (passed, confidence) where *passed* is True if the threshold
            is met and *confidence* is in [0, 1].
        """
        handler = _CHALLENGE_HANDLERS.get(challenge_type)
        if handler is None:
            logger.warning("Unknown challenge type: %s", challenge_type)
            return False, 0.0
        return handler(self, mesh)

    # ── Per-challenge handlers ───────────────────────────────────────────

    def _check_blink(self, mesh: FaceMesh) -> tuple[bool, float]:
        min_ear = min(mesh.left_eye_ar, mesh.right_eye_ar)
        # Confidence: how far below the threshold the EAR dropped.
        # 1.0 when fully closed (EAR ≈ 0), 0.0 at threshold.
        if min_ear < self._t.blink_ear:
            confidence = min(1.0, (self._t.blink_ear - min_ear) / self._t.blink_ear)
            return True, confidence
        return False, 0.0

    def _check_smile(self, mesh: FaceMesh) -> tuple[bool, float]:
        # Mouth width relative to face width (outer eye corners span).
        import numpy as np

        landmarks = mesh.landmarks_468
        mouth_left = landmarks[78]
        mouth_right = landmarks[308]
        eye_left = landmarks[33]
        eye_right = landmarks[263]

        mouth_width = float(np.linalg.norm(mouth_left[:2] - mouth_right[:2]))
        face_width = float(np.linalg.norm(eye_left[:2] - eye_right[:2]))

        if face_width < 1e-6:
            return False, 0.0

        ratio = mouth_width / face_width
        if ratio > self._t.smile_mouth_width_ratio:
            excess = ratio - self._t.smile_mouth_width_ratio
            confidence = min(1.0, excess / 0.15)
            return True, confidence
        return False, 0.0

    def _check_open_mouth(self, mesh: FaceMesh) -> tuple[bool, float]:
        if mesh.mouth_ar > self._t.open_mouth_mar:
            excess = mesh.mouth_ar - self._t.open_mouth_mar
            confidence = min(1.0, excess / 0.4)
            return True, confidence
        return False, 0.0

    def _check_turn_left(self, mesh: FaceMesh) -> tuple[bool, float]:
        if mesh.head_yaw < self._t.turn_left_yaw:
            excess = abs(mesh.head_yaw - self._t.turn_left_yaw)
            confidence = min(1.0, excess / 30.0)
            return True, confidence
        return False, 0.0

    def _check_turn_right(self, mesh: FaceMesh) -> tuple[bool, float]:
        if mesh.head_yaw > self._t.turn_right_yaw:
            excess = mesh.head_yaw - self._t.turn_right_yaw
            confidence = min(1.0, excess / 30.0)
            return True, confidence
        return False, 0.0

    def _check_look_up(self, mesh: FaceMesh) -> tuple[bool, float]:
        if mesh.head_pitch < self._t.look_up_pitch:
            excess = abs(mesh.head_pitch - self._t.look_up_pitch)
            confidence = min(1.0, excess / 20.0)
            return True, confidence
        return False, 0.0

    def _check_look_down(self, mesh: FaceMesh) -> tuple[bool, float]:
        if mesh.head_pitch > self._t.look_down_pitch:
            excess = mesh.head_pitch - self._t.look_down_pitch
            confidence = min(1.0, excess / 20.0)
            return True, confidence
        return False, 0.0


# Map challenge types to their handler methods.
_CHALLENGE_HANDLERS: dict[ChallengeType, callable] = {
    ChallengeType.BLINK: ActionDetector._check_blink,
    ChallengeType.SMILE: ActionDetector._check_smile,
    ChallengeType.OPEN_MOUTH: ActionDetector._check_open_mouth,
    ChallengeType.TURN_LEFT: ActionDetector._check_turn_left,
    ChallengeType.TURN_RIGHT: ActionDetector._check_turn_right,
    ChallengeType.LOOK_UP: ActionDetector._check_look_up,
    ChallengeType.LOOK_DOWN: ActionDetector._check_look_down,
}
