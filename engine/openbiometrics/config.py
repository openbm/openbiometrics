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
    """Configuration for document processing.

    Controls document detection, OCR, MRZ parsing, and face extraction
    from identity documents.
    """

    enabled: bool = True
    models_dir: str = "./models"
    ctx_id: int = 0
    enable_ocr: bool = True
    enable_mrz: bool = True
    enable_face_extraction: bool = False


@dataclass
class LivenessConfig:
    """Configuration for standalone active liveness detection.

    For passive liveness within the face pipeline, use FaceConfig.enable_liveness.
    This is for the interactive multi-frame / active liveness challenge system.
    """

    enabled: bool = True
    models_dir: str = "./models"
    ctx_id: int = 0
    session_ttl: float = 300.0  # Session time-to-live in seconds
    num_challenges: int = 3
    timeout_seconds: float = 5.0  # Per-challenge timeout


@dataclass
class PersonConfig:
    """Configuration for person detection and tracking."""

    enabled: bool = True
    models_dir: str = "./models"
    ctx_id: int = 0
    model_path: str = "yolov8n.pt"
    confidence_threshold: float = 0.5
    max_disappeared: int = 30  # Frames before a tracked person is dropped
    iou_threshold: float = 0.3


@dataclass
class VideoConfig:
    """Configuration for video stream processing and camera management."""

    enabled: bool = True
    max_fps: float = 30.0
    track_faces: bool = True
    buffer_size: int = 30


@dataclass
class EventsConfig:
    """Configuration for event emission and webhook dispatch."""

    enabled: bool = True
    max_workers: int = 4  # Thread pool size for event dispatch
    history_size: int = 1000  # Number of recent events to retain
    webhooks_enabled: bool = True


@dataclass
class IdentityConfig:
    """Configuration for identity resolution and face clustering."""

    enabled: bool = True
    watchlist_dir: str = "./watchlists"
    cluster_threshold: float = 0.6  # Default cosine similarity threshold


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
    identity: IdentityConfig = field(default_factory=IdentityConfig)
