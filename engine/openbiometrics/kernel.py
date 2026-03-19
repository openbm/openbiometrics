"""BiometricKernel — top-level entry point for the OpenBiometrics engine.

The kernel owns the lifecycle of all processing modules and provides
a unified interface for initialization, health checks, and access
to each subsystem.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from openbiometrics.config import BiometricConfig
from openbiometrics.core.pipeline import FacePipeline, PipelineConfig

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health check result for the kernel and its modules."""

    healthy: bool
    modules: dict[str, bool] = field(default_factory=dict)
    details: dict[str, str] = field(default_factory=dict)


class BiometricKernel:
    """Top-level entry point for the OpenBiometrics engine.

    Lazily initializes processing modules based on configuration.
    Call load() to prepare models, then access modules via properties.

    Usage:
        kernel = BiometricKernel(BiometricConfig(
            face=FaceConfig(ctx_id=0),
        ))
        kernel.load()

        results = kernel.face.process(image)
    """

    def __init__(self, config: BiometricConfig | None = None):
        """
        Args:
            config: Engine configuration. Uses defaults if None.
        """
        self._config = config or BiometricConfig()
        self._face: FacePipeline | None = None
        self._document = None  # Phase 2
        self._person = None  # Phase 2
        self._loaded = False

    @property
    def config(self) -> BiometricConfig:
        """Current engine configuration."""
        return self._config

    @property
    def face(self) -> FacePipeline | None:
        """Face processing pipeline (detect, recognize, liveness, demographics)."""
        return self._face

    @property
    def document(self):
        """Document processing module (Phase 2 — returns None)."""
        return self._document

    @property
    def person(self):
        """Person detection / re-identification module (Phase 2 — returns None)."""
        return self._person

    @property
    def is_loaded(self) -> bool:
        """Whether load() has been called successfully."""
        return self._loaded

    def load(self) -> None:
        """Load all configured modules and their models.

        Call once before processing. Safe to call multiple times
        (subsequent calls are no-ops).
        """
        if self._loaded:
            logger.debug("Kernel already loaded, skipping")
            return

        logger.info("Loading BiometricKernel...")

        # Face pipeline — bridge FaceConfig fields into PipelineConfig
        face_cfg = self._config.face
        pipeline_config = PipelineConfig(
            models_dir=face_cfg.models_dir,
            ctx_id=face_cfg.ctx_id,
            det_thresh=face_cfg.det_thresh,
            det_size=face_cfg.det_size,
            max_faces=face_cfg.max_faces,
            enable_liveness=face_cfg.enable_liveness,
            enable_demographics=face_cfg.enable_demographics,
            enable_quality=face_cfg.enable_quality,
            quality_gate=face_cfg.quality_gate,
        )
        self._face = FacePipeline(pipeline_config)
        self._face.load()

        # Phase 2 modules would be initialized here:
        # self._document = DocumentPipeline(self._config.document)
        # self._person = PersonPipeline(self._config.person)

        self._loaded = True
        logger.info("BiometricKernel loaded successfully")

    def health(self) -> HealthStatus:
        """Check health of the kernel and all loaded modules.

        Returns:
            HealthStatus with per-module breakdown
        """
        modules: dict[str, bool] = {}
        details: dict[str, str] = {}

        # Face module
        if self._face is not None:
            try:
                # Check that the detector is initialized (minimum requirement)
                face_ok = self._face._detector is not None
                modules["face"] = face_ok
                if not face_ok:
                    details["face"] = "Detector not initialized"
                else:
                    parts = []
                    if self._face._recognizer is not None:
                        parts.append("recognizer")
                    if self._face._liveness is not None:
                        parts.append("liveness")
                    if self._face._demographics is not None:
                        parts.append("demographics")
                    details["face"] = f"loaded: detector, {', '.join(parts)}" if parts else "loaded: detector only"
            except Exception as exc:
                modules["face"] = False
                details["face"] = f"Error: {exc}"
        else:
            modules["face"] = False
            details["face"] = "Not loaded"

        # Phase 2 placeholders
        modules["document"] = False
        details["document"] = "Phase 2 — not yet implemented"
        modules["person"] = False
        details["person"] = "Phase 2 — not yet implemented"

        healthy = modules.get("face", False)
        return HealthStatus(healthy=healthy, modules=modules, details=details)
