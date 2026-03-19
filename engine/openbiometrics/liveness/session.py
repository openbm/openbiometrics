"""Active liveness session management.

An ActiveLivenessSession drives a user through a sequence of challenges
(blink, turn head, etc.) and tracks their progress. ActiveLivenessManager
manages multiple concurrent sessions with TTL-based cleanup.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from openbiometrics.liveness.challenges import (
    Challenge,
    ChallengeSequence,
    ChallengeType,
)
from openbiometrics.liveness.detector import ActionDetector, ActionThresholds
from openbiometrics.liveness.landmarks import FaceMeshDetector

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Lifecycle states of an active liveness session."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class ChallengeResult:
    """Result returned after submitting a frame to the session.

    Attributes:
        session_id: UUID of the owning session.
        challenge_type: The challenge that was evaluated.
        passed: Whether the current challenge was passed in this frame.
        confidence: Detection confidence in [0, 1].
        challenges_remaining: Number of challenges still to complete.
        session_complete: True when all challenges have been passed.
        is_live: Final liveness verdict — None until session completes.
        state: Current session state.
    """

    session_id: str
    challenge_type: ChallengeType | None
    passed: bool
    confidence: float
    challenges_remaining: int
    session_complete: bool
    is_live: bool | None
    state: SessionState


class ActiveLivenessSession:
    """Drives a user through a randomised active liveness challenge sequence.

    Thread-safe — all public methods are protected by a lock.

    Usage:
        session = ActiveLivenessSession(num_challenges=3)
        challenge = session.get_current_challenge()
        result = session.submit_frame(bgr_frame)
    """

    def __init__(
        self,
        *,
        num_challenges: int = 3,
        timeout_seconds: float = 5.0,
        thresholds: ActionThresholds | None = None,
        allowed_types: list[ChallengeType] | None = None,
    ):
        """
        Args:
            num_challenges: Number of challenges in the sequence.
            timeout_seconds: Per-challenge timeout in seconds.
            thresholds: Custom action-detection thresholds.
            allowed_types: Subset of ChallengeType to use.
        """
        self._lock = threading.Lock()
        self.session_id: str = str(uuid.uuid4())
        self._state: SessionState = SessionState.PENDING
        self._created_at: float = time.monotonic()

        self._sequence = ChallengeSequence(
            num_challenges=num_challenges,
            timeout_seconds=timeout_seconds,
            allowed_types=allowed_types,
        )
        self._challenge_index: int = 0
        self._challenge_start_time: float | None = None

        self._mesh_detector = FaceMeshDetector()
        self._action_detector = ActionDetector(thresholds)

        logger.info(
            "ActiveLivenessSession %s created with %d challenges",
            self.session_id,
            num_challenges,
        )

    @property
    def state(self) -> SessionState:
        """Current session state."""
        with self._lock:
            return self._state

    @property
    def challenges(self) -> list[Challenge]:
        """The full challenge sequence (read-only copy)."""
        return list(self._sequence.challenges)

    def get_current_challenge(self) -> Challenge | None:
        """Return the current challenge, or None if the session is finished.

        Returns:
            The active Challenge, or None if completed / failed / expired.
        """
        with self._lock:
            if self._state in (
                SessionState.COMPLETED,
                SessionState.FAILED,
                SessionState.EXPIRED,
            ):
                return None
            if self._challenge_index >= len(self._sequence.challenges):
                return None
            return self._sequence.challenges[self._challenge_index]

    def submit_frame(self, image: np.ndarray) -> ChallengeResult:
        """Submit a video frame for the current challenge.

        On the first call the session transitions from PENDING to
        IN_PROGRESS.  Each frame is evaluated against the current
        challenge — when the action is detected, the session advances
        to the next challenge.  If a challenge times out, the session
        moves to FAILED.

        Args:
            image: BGR image (H, W, 3) as uint8.

        Returns:
            ChallengeResult describing the outcome of this frame.
        """
        with self._lock:
            return self._submit_frame_locked(image)

    # ── Internal ─────────────────────────────────────────────────────────

    def _submit_frame_locked(self, image: np.ndarray) -> ChallengeResult:
        """Core frame-processing logic (must be called under lock)."""
        now = time.monotonic()

        # Terminal states — nothing to do
        if self._state in (
            SessionState.COMPLETED,
            SessionState.FAILED,
            SessionState.EXPIRED,
        ):
            return self._make_result(
                challenge_type=None,
                passed=False,
                confidence=0.0,
            )

        # Transition PENDING → IN_PROGRESS on first frame
        if self._state == SessionState.PENDING:
            self._state = SessionState.IN_PROGRESS
            self._challenge_start_time = now

        challenge = self._sequence.challenges[self._challenge_index]

        # Check per-challenge timeout
        if (
            self._challenge_start_time is not None
            and (now - self._challenge_start_time) > challenge.timeout_seconds
        ):
            self._state = SessionState.FAILED
            logger.info(
                "Session %s FAILED — challenge %s timed out",
                self.session_id,
                challenge.type.value,
            )
            return self._make_result(
                challenge_type=challenge.type,
                passed=False,
                confidence=0.0,
            )

        # Detect face mesh
        mesh = self._mesh_detector.detect(image)
        if mesh is None:
            return self._make_result(
                challenge_type=challenge.type,
                passed=False,
                confidence=0.0,
            )

        # Check whether the action was performed
        passed, confidence = self._action_detector.check(mesh, challenge.type)

        if passed:
            logger.debug(
                "Session %s — challenge %s passed (confidence=%.2f)",
                self.session_id,
                challenge.type.value,
                confidence,
            )
            self._challenge_index += 1
            self._challenge_start_time = now  # reset timer for next challenge

            # All challenges done?
            if self._challenge_index >= len(self._sequence.challenges):
                self._state = SessionState.COMPLETED
                logger.info("Session %s COMPLETED — user is live", self.session_id)

        return self._make_result(
            challenge_type=challenge.type,
            passed=passed,
            confidence=confidence,
        )

    def _make_result(
        self,
        *,
        challenge_type: ChallengeType | None,
        passed: bool,
        confidence: float,
    ) -> ChallengeResult:
        remaining = max(
            0,
            len(self._sequence.challenges) - self._challenge_index,
        )
        session_complete = self._state == SessionState.COMPLETED
        is_live: bool | None = None
        if self._state == SessionState.COMPLETED:
            is_live = True
        elif self._state == SessionState.FAILED:
            is_live = False

        return ChallengeResult(
            session_id=self.session_id,
            challenge_type=challenge_type,
            passed=passed,
            confidence=confidence,
            challenges_remaining=remaining,
            session_complete=session_complete,
            is_live=is_live,
            state=self._state,
        )


class ActiveLivenessManager:
    """Manages multiple ActiveLivenessSession instances with TTL-based cleanup.

    Thread-safe — safe to call from multiple threads or async tasks.

    Usage:
        manager = ActiveLivenessManager(session_ttl=300)
        session = manager.create_session()
        result = manager.submit_frame(session.session_id, frame)
    """

    def __init__(
        self,
        *,
        session_ttl: float = 300.0,
        num_challenges: int = 3,
        timeout_seconds: float = 5.0,
        thresholds: ActionThresholds | None = None,
    ):
        """
        Args:
            session_ttl: Time-to-live for sessions in seconds (default 5 min).
            num_challenges: Default number of challenges per session.
            timeout_seconds: Per-challenge timeout in seconds.
            thresholds: Default action-detection thresholds.
        """
        self._lock = threading.Lock()
        self._sessions: dict[str, _ManagedSession] = {}
        self._session_ttl = session_ttl
        self._num_challenges = num_challenges
        self._timeout_seconds = timeout_seconds
        self._thresholds = thresholds

    def create_session(
        self,
        *,
        num_challenges: int | None = None,
        timeout_seconds: float | None = None,
        allowed_types: list[ChallengeType] | None = None,
    ) -> ActiveLivenessSession:
        """Create and register a new active liveness session.

        Args:
            num_challenges: Override default challenge count.
            timeout_seconds: Override default per-challenge timeout.
            allowed_types: Restrict challenge types.

        Returns:
            The newly created ActiveLivenessSession.
        """
        self._cleanup_expired()

        session = ActiveLivenessSession(
            num_challenges=num_challenges or self._num_challenges,
            timeout_seconds=timeout_seconds or self._timeout_seconds,
            thresholds=self._thresholds,
            allowed_types=allowed_types,
        )

        with self._lock:
            self._sessions[session.session_id] = _ManagedSession(
                session=session,
                created_at=time.monotonic(),
            )

        logger.debug("Manager: registered session %s", session.session_id)
        return session

    def get_session(self, session_id: str) -> ActiveLivenessSession | None:
        """Retrieve a session by ID, or None if not found / expired."""
        self._cleanup_expired()
        with self._lock:
            managed = self._sessions.get(session_id)
            if managed is None:
                return None
            return managed.session

    def submit_frame(self, session_id: str, image: np.ndarray) -> ChallengeResult:
        """Submit a frame to an existing session.

        Args:
            session_id: UUID of the target session.
            image: BGR image (H, W, 3) as uint8.

        Returns:
            ChallengeResult from the session.

        Raises:
            KeyError: If the session does not exist or has expired.
        """
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(f"Session {session_id} not found or expired")
        return session.submit_frame(image)

    def remove_session(self, session_id: str) -> bool:
        """Explicitly remove a session.

        Returns:
            True if the session existed and was removed.
        """
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    @property
    def active_session_count(self) -> int:
        """Number of currently tracked sessions (including expired ones pending cleanup)."""
        with self._lock:
            return len(self._sessions)

    def _cleanup_expired(self) -> None:
        """Remove sessions that have exceeded their TTL."""
        now = time.monotonic()
        expired_ids: list[str] = []

        with self._lock:
            for sid, managed in self._sessions.items():
                if (now - managed.created_at) > self._session_ttl:
                    managed.session._state = SessionState.EXPIRED
                    expired_ids.append(sid)

            for sid in expired_ids:
                del self._sessions[sid]

        if expired_ids:
            logger.info(
                "Manager: cleaned up %d expired session(s)",
                len(expired_ids),
            )


@dataclass
class _ManagedSession:
    """Internal wrapper associating a session with its creation timestamp."""

    session: ActiveLivenessSession
    created_at: float
