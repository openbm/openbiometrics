"""Active liveness detection via interactive challenge-response.

Unlike passive liveness (``openbiometrics.core.liveness``), active liveness
requires user cooperation — performing actions like blinking, turning their
head, or smiling — to prove the person in front of the camera is real.

Usage:
    from openbiometrics.liveness import ActiveLivenessSession

    session = ActiveLivenessSession(num_challenges=3)
    challenge = session.get_current_challenge()
    result = session.submit_frame(bgr_frame)
"""

from openbiometrics.liveness.challenges import (
    Challenge,
    ChallengeType,
)
from openbiometrics.liveness.detector import ActionDetector
from openbiometrics.liveness.landmarks import FaceMesh, FaceMeshDetector
from openbiometrics.liveness.session import (
    ActiveLivenessManager,
    ActiveLivenessSession,
    ChallengeResult,
    SessionState,
)

__all__ = [
    "ActiveLivenessManager",
    "ActiveLivenessSession",
    "ActionDetector",
    "Challenge",
    "ChallengeResult",
    "ChallengeType",
    "FaceMesh",
    "FaceMeshDetector",
    "SessionState",
]
