"""Challenge definitions for active liveness verification.

Defines the set of challenges a user can be asked to perform (blink,
turn head, smile, etc.) and a sequence generator that produces a
randomised, non-repetitive challenge order.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum


class ChallengeType(Enum):
    """Actions the user can be asked to perform."""

    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    LOOK_UP = "look_up"
    LOOK_DOWN = "look_down"
    BLINK = "blink"
    SMILE = "smile"
    OPEN_MOUTH = "open_mouth"


# Human-readable default instructions per challenge type.
_DEFAULT_INSTRUCTIONS: dict[ChallengeType, str] = {
    ChallengeType.TURN_LEFT: "Please turn your head to the left.",
    ChallengeType.TURN_RIGHT: "Please turn your head to the right.",
    ChallengeType.LOOK_UP: "Please look up.",
    ChallengeType.LOOK_DOWN: "Please look down.",
    ChallengeType.BLINK: "Please blink your eyes.",
    ChallengeType.SMILE: "Please smile.",
    ChallengeType.OPEN_MOUTH: "Please open your mouth.",
}

# Groups of challenge types that are considered "similar" — we avoid
# placing two from the same group consecutively.
_SIMILARITY_GROUPS: list[set[ChallengeType]] = [
    {ChallengeType.TURN_LEFT, ChallengeType.TURN_RIGHT},
    {ChallengeType.LOOK_UP, ChallengeType.LOOK_DOWN},
]


def _are_similar(a: ChallengeType, b: ChallengeType) -> bool:
    """Return True if *a* and *b* belong to the same similarity group."""
    for group in _SIMILARITY_GROUPS:
        if a in group and b in group:
            return True
    return False


@dataclass(frozen=True)
class Challenge:
    """A single challenge presented to the user.

    Attributes:
        type: The type of action requested.
        instruction: Human-readable instruction string.
        timeout_seconds: How long the user has to complete the challenge.
    """

    type: ChallengeType
    instruction: str = ""
    timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        # Fill in the default instruction when none was provided.
        if not self.instruction:
            object.__setattr__(
                self,
                "instruction",
                _DEFAULT_INSTRUCTIONS.get(self.type, ""),
            )


@dataclass
class ChallengeSequence:
    """Generates a randomised, non-repetitive sequence of challenges.

    Args:
        num_challenges: Number of challenges to generate.
        timeout_seconds: Per-challenge timeout.
        allowed_types: Subset of ChallengeType to draw from.
            Defaults to all types.

    Usage:
        seq = ChallengeSequence(num_challenges=3)
        for challenge in seq.challenges:
            print(challenge.instruction)
    """

    num_challenges: int = 3
    timeout_seconds: float = 5.0
    allowed_types: list[ChallengeType] | None = None
    challenges: list[Challenge] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        pool = list(self.allowed_types or ChallengeType)
        if not pool:
            raise ValueError("allowed_types must not be empty")
        self.challenges = self._generate(pool)

    def _generate(self, pool: list[ChallengeType]) -> list[Challenge]:
        """Build a challenge list avoiding consecutive similar types."""
        selected: list[ChallengeType] = []

        for _ in range(self.num_challenges):
            candidates = list(pool)
            if selected:
                last = selected[-1]
                candidates = [c for c in candidates if not _are_similar(c, last)]
                # Fall back to full pool if filtering removed everything
                if not candidates:
                    candidates = list(pool)

            choice = random.choice(candidates)
            selected.append(choice)

        return [
            Challenge(type=ct, timeout_seconds=self.timeout_seconds)
            for ct in selected
        ]
