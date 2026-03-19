"""Liveness session presets matching common industry verification modes.

Each preset defines a fixed set of challenges, thresholds, and timing
suitable for a specific verification scenario. Inspired by Innovatrics
DOT liveness variants (MagnifEye, Smile, Multi-Range) and similar
products from iProov, Jumio, etc.

Usage:
    from openbiometrics.liveness.presets import LivenessPreset, get_preset

    preset = get_preset("smile")
    session = manager.create_session(**preset.session_kwargs())
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from openbiometrics.liveness.challenges import ChallengeType
from openbiometrics.liveness.detector import ActionThresholds


class PresetName(Enum):
    """Available liveness preset modes."""

    EYE = "eye"
    SMILE = "smile"
    MULTI_RANGE = "multi_range"
    HEAD_TURN = "head_turn"
    FULL = "full"
    PASSIVE_ONLY = "passive_only"


@dataclass(frozen=True)
class LivenessPreset:
    """A named liveness configuration preset.

    Attributes:
        name: Preset identifier.
        description: Human-readable explanation of the mode.
        challenge_types: Allowed challenge types for this preset.
        num_challenges: How many challenges to present.
        timeout_seconds: Per-challenge timeout.
        thresholds: Custom detection thresholds for this mode.
        require_passive: Whether to also run passive liveness check.
    """

    name: PresetName
    description: str
    challenge_types: list[ChallengeType]
    num_challenges: int
    timeout_seconds: float
    thresholds: ActionThresholds
    require_passive: bool = True

    def session_kwargs(self) -> dict:
        """Return kwargs suitable for ActiveLivenessManager.create_session()."""
        return {
            "num_challenges": self.num_challenges,
            "timeout_seconds": self.timeout_seconds,
            "allowed_types": self.challenge_types,
        }


# ── Preset definitions ────────────────────────────────────────────────

_EYE_PRESET = LivenessPreset(
    name=PresetName.EYE,
    description=(
        "Eye-based liveness (MagnifEye-style). "
        "User blinks on command. Minimal friction, fast verification. "
        "Best for low-risk onboarding and repeat authentication."
    ),
    challenge_types=[ChallengeType.BLINK],
    num_challenges=2,
    timeout_seconds=4.0,
    thresholds=ActionThresholds(blink_ear=0.18),
    require_passive=True,
)

_SMILE_PRESET = LivenessPreset(
    name=PresetName.SMILE,
    description=(
        "Smile-based liveness. "
        "User smiles on command. Natural interaction, good UX. "
        "Detects static photo attacks that can't produce expressions."
    ),
    challenge_types=[ChallengeType.SMILE],
    num_challenges=1,
    timeout_seconds=5.0,
    thresholds=ActionThresholds(smile_mouth_width_ratio=0.40),
    require_passive=True,
)

_MULTI_RANGE_PRESET = LivenessPreset(
    name=PresetName.MULTI_RANGE,
    description=(
        "Multi-range liveness. "
        "User performs actions at varying distances — combines head movement "
        "and eye checks to defeat screen replay and 3D mask attacks. "
        "Higher security, moderate friction."
    ),
    challenge_types=[
        ChallengeType.BLINK,
        ChallengeType.LOOK_UP,
        ChallengeType.LOOK_DOWN,
        ChallengeType.TURN_LEFT,
        ChallengeType.TURN_RIGHT,
    ],
    num_challenges=4,
    timeout_seconds=6.0,
    thresholds=ActionThresholds(
        blink_ear=0.18,
        turn_left_yaw=-20.0,
        turn_right_yaw=20.0,
        look_up_pitch=-12.0,
        look_down_pitch=12.0,
    ),
    require_passive=True,
)

_HEAD_TURN_PRESET = LivenessPreset(
    name=PresetName.HEAD_TURN,
    description=(
        "Head-turn liveness. "
        "User turns head left/right. Defeats flat photo attacks. "
        "Good balance of security and usability."
    ),
    challenge_types=[ChallengeType.TURN_LEFT, ChallengeType.TURN_RIGHT],
    num_challenges=2,
    timeout_seconds=5.0,
    thresholds=ActionThresholds(turn_left_yaw=-18.0, turn_right_yaw=18.0),
    require_passive=True,
)

_FULL_PRESET = LivenessPreset(
    name=PresetName.FULL,
    description=(
        "Full multi-challenge liveness. "
        "Randomised sequence of blink, smile, head turns, and mouth open. "
        "Highest security. Use for high-value transactions or initial KYC."
    ),
    challenge_types=list(ChallengeType),
    num_challenges=4,
    timeout_seconds=5.0,
    thresholds=ActionThresholds(),
    require_passive=True,
)

_PASSIVE_ONLY_PRESET = LivenessPreset(
    name=PresetName.PASSIVE_ONLY,
    description=(
        "Passive liveness only — no active challenges. "
        "Uses MiniFASNet anti-spoofing model on a single frame. "
        "Zero friction, lowest security. Good for low-risk re-auth."
    ),
    challenge_types=[],
    num_challenges=0,
    timeout_seconds=0.0,
    thresholds=ActionThresholds(),
    require_passive=True,
)


_PRESETS: dict[PresetName, LivenessPreset] = {
    PresetName.EYE: _EYE_PRESET,
    PresetName.SMILE: _SMILE_PRESET,
    PresetName.MULTI_RANGE: _MULTI_RANGE_PRESET,
    PresetName.HEAD_TURN: _HEAD_TURN_PRESET,
    PresetName.FULL: _FULL_PRESET,
    PresetName.PASSIVE_ONLY: _PASSIVE_ONLY_PRESET,
}


def get_preset(name: str | PresetName) -> LivenessPreset:
    """Look up a liveness preset by name.

    Args:
        name: Preset name as string or PresetName enum.

    Returns:
        The matching LivenessPreset.

    Raises:
        KeyError: If the preset name is not recognized.
    """
    if isinstance(name, str):
        name = PresetName(name)
    return _PRESETS[name]


def list_presets() -> list[LivenessPreset]:
    """Return all available presets."""
    return list(_PRESETS.values())
