"""Centralized configuration for the OpenBiometrics engine.

BiometricConfig is the top-level configuration with subsections for each
processing module. FaceConfig absorbs the fields from the original
PipelineConfig for backward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FaceConfig:
    """Configuration for face processing (detection, recognition, liveness, demographics).

    Absorbs all fields from the original PipelineConfig so existing
    FacePipeline usage continues to work.
    """

    models_dir: str = "./models"
    ctx_id: int = 0  # GPU device (-1 for CPU)
    det_thresh: float = 0.5
    det_size: tuple[int, int] = (640, 640)
    max_faces: int = 0
    enable_liveness: bool = True
    enable_demographics: bool = True
    enable_quality: bool = True
    quality_gate: bool = False  # Skip recognition if quality fails


@dataclass
class DocumentConfig:
    """Configuration for document processing (Phase 2)."""

    models_dir: str = "./models"
    ctx_id: int = 0


@dataclass
class LivenessConfig:
    """Configuration for standalone liveness detection (Phase 2).

    For liveness within the face pipeline, use FaceConfig.enable_liveness.
    This is for advanced multi-frame / active liveness scenarios.
    """

    models_dir: str = "./models"
    ctx_id: int = 0


@dataclass
class PersonConfig:
    """Configuration for person detection / re-identification (Phase 2)."""

    models_dir: str = "./models"
    ctx_id: int = 0


@dataclass
class VideoConfig:
    """Configuration for video stream processing (Phase 2)."""

    max_fps: float = 30.0
    track_faces: bool = True
    buffer_size: int = 30


@dataclass
class EventsConfig:
    """Configuration for event emission / callbacks (Phase 2)."""

    enabled: bool = False


@dataclass
class BiometricConfig:
    """Top-level configuration for the OpenBiometrics engine.

    Groups subsection configs for each processing module.

    Usage:
        config = BiometricConfig(
            face=FaceConfig(ctx_id=0, enable_liveness=True),
        )
        kernel = BiometricKernel(config)
    """

    face: FaceConfig = field(default_factory=FaceConfig)
    document: DocumentConfig = field(default_factory=DocumentConfig)
    liveness: LivenessConfig = field(default_factory=LivenessConfig)
    person: PersonConfig = field(default_factory=PersonConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    events: EventsConfig = field(default_factory=EventsConfig)
