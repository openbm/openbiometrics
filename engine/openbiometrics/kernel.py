"""BiometricKernel -- top-level entry point for the OpenBiometrics engine.

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

# Optional module imports -- each is guarded so the kernel works even when
# a subset of dependencies is installed.

try:
    from openbiometrics.document.pipeline import DocumentPipeline
    from openbiometrics.document.pipeline import DocumentConfig as _DocPipelineConfig
except ImportError:
    DocumentPipeline = None  # type: ignore[assignment,misc]
    _DocPipelineConfig = None  # type: ignore[assignment,misc]

try:
    from openbiometrics.liveness.session import ActiveLivenessManager
except ImportError:
    ActiveLivenessManager = None  # type: ignore[assignment,misc]

try:
    from openbiometrics.person.detector import PersonDetector
except ImportError:
    PersonDetector = None  # type: ignore[assignment,misc]

try:
    from openbiometrics.person.tracker import PersonTracker
except ImportError:
    PersonTracker = None  # type: ignore[assignment,misc]

try:
    from openbiometrics.video.manager import CameraManager
except ImportError:
    CameraManager = None  # type: ignore[assignment,misc]

try:
    from openbiometrics.events.bus import EventBus
except ImportError:
    EventBus = None  # type: ignore[assignment,misc]

try:
    from openbiometrics.events.webhooks import WebhookDispatcher
except ImportError:
    WebhookDispatcher = None  # type: ignore[assignment,misc]

try:
    from openbiometrics.identity.resolver import IdentityResolver
except ImportError:
    IdentityResolver = None  # type: ignore[assignment,misc]

try:
    from openbiometrics.identity.clustering import FaceClusterer
except ImportError:
    FaceClusterer = None  # type: ignore[assignment,misc]


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
        self._face_pipeline: FacePipeline | None = None
        self._document_pipeline = None
        self._liveness_manager = None
        self._person_detector = None
        self._person_tracker = None
        self._camera_manager = None
        self._event_bus = None
        self._webhook_dispatcher = None
        self._identity_resolver = None
        self._face_clusterer = None
        self._loaded = False

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def config(self) -> BiometricConfig:
        """Current engine configuration."""
        return self._config

    @property
    def face(self) -> FacePipeline | None:
        """Face processing pipeline (detect, recognize, liveness, demographics)."""
        return self._face_pipeline

    @property
    def document(self):
        """Document processing pipeline (detect, OCR, MRZ, face extraction)."""
        return self._document_pipeline

    @property
    def liveness(self):
        """Active liveness session manager."""
        return self._liveness_manager

    @property
    def person_detector(self):
        """YOLO-based person detector."""
        return self._person_detector

    @property
    def person_tracker(self):
        """IoU-based multi-person tracker."""
        return self._person_tracker

    @property
    def cameras(self):
        """Multi-stream camera manager."""
        return self._camera_manager

    @property
    def events(self):
        """Publish-subscribe event bus."""
        return self._event_bus

    @property
    def webhooks(self):
        """Webhook dispatcher for event forwarding."""
        return self._webhook_dispatcher

    @property
    def identity_resolver(self):
        """Cross-watchlist identity resolver."""
        return self._identity_resolver

    @property
    def clusterer(self):
        """Face embedding clusterer / deduplicator."""
        return self._face_clusterer

    # Backward-compat alias
    @property
    def person(self):
        """Alias for person_detector (backward compatibility)."""
        return self._person_detector

    @property
    def is_loaded(self) -> bool:
        """Whether load() has been called successfully."""
        return self._loaded

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load all configured modules and their models.

        Call once before processing. Safe to call multiple times
        (subsequent calls are no-ops).
        """
        if self._loaded:
            logger.debug("Kernel already loaded, skipping")
            return

        logger.info("Loading BiometricKernel...")

        # Face pipeline -- always loaded (core module)
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
        self._face_pipeline = FacePipeline(pipeline_config)
        self._face_pipeline.load()

        # Document pipeline
        doc_cfg = self._config.document
        if doc_cfg.enabled and DocumentPipeline is not None:
            try:
                doc_pipeline_cfg = _DocPipelineConfig(
                    model_dir=doc_cfg.models_dir,
                    enable_ocr=doc_cfg.enable_ocr,
                    enable_mrz=doc_cfg.enable_mrz,
                    enable_face_extraction=doc_cfg.enable_face_extraction,
                )
                self._document_pipeline = DocumentPipeline(doc_pipeline_cfg)
                logger.info("Document pipeline loaded")
            except Exception as exc:
                logger.warning("Document pipeline failed to initialize: %s", exc)
        elif doc_cfg.enabled:
            logger.info("Document module not available (missing dependencies)")

        # Active liveness manager
        liveness_cfg = self._config.liveness
        if liveness_cfg.enabled and ActiveLivenessManager is not None:
            try:
                self._liveness_manager = ActiveLivenessManager(
                    session_ttl=liveness_cfg.session_ttl,
                    num_challenges=liveness_cfg.num_challenges,
                    timeout_seconds=liveness_cfg.timeout_seconds,
                )
                logger.info("Active liveness manager loaded")
            except Exception as exc:
                logger.warning("Active liveness manager failed to initialize: %s", exc)
        elif liveness_cfg.enabled:
            logger.info("Liveness module not available (missing dependencies)")

        # Person detector
        person_cfg = self._config.person
        if person_cfg.enabled and PersonDetector is not None:
            try:
                self._person_detector = PersonDetector(
                    model_path=person_cfg.model_path,
                    ctx_id=person_cfg.ctx_id,
                    confidence_threshold=person_cfg.confidence_threshold,
                )
                logger.info("Person detector created (model loads lazily)")
            except Exception as exc:
                logger.warning("Person detector failed to initialize: %s", exc)
        elif person_cfg.enabled:
            logger.info("Person detector not available (missing dependencies)")

        # Person tracker
        if person_cfg.enabled and PersonTracker is not None:
            try:
                self._person_tracker = PersonTracker(
                    max_age=person_cfg.max_disappeared,
                    iou_threshold=person_cfg.iou_threshold,
                )
                logger.info("Person tracker created")
            except Exception as exc:
                logger.warning("Person tracker failed to initialize: %s", exc)
        elif person_cfg.enabled and PersonDetector is not None:
            logger.info("Person tracker not available (missing dependencies)")

        # Camera manager
        video_cfg = self._config.video
        if video_cfg.enabled and CameraManager is not None:
            try:
                self._camera_manager = CameraManager(
                    default_pipeline=self._face_pipeline,
                )
                logger.info("Camera manager created")
            except Exception as exc:
                logger.warning("Camera manager failed to initialize: %s", exc)
        elif video_cfg.enabled:
            logger.info("Video module not available (missing dependencies)")

        # Event bus -- always created when events are enabled
        events_cfg = self._config.events
        if events_cfg.enabled and EventBus is not None:
            try:
                self._event_bus = EventBus(
                    max_workers=events_cfg.max_workers,
                    history_size=events_cfg.history_size,
                )
                logger.info("Event bus created")
            except Exception as exc:
                logger.warning("Event bus failed to initialize: %s", exc)

            # Webhook dispatcher
            if (
                events_cfg.webhooks_enabled
                and self._event_bus is not None
                and WebhookDispatcher is not None
            ):
                try:
                    self._webhook_dispatcher = WebhookDispatcher(self._event_bus)
                    logger.info("Webhook dispatcher created")
                except Exception as exc:
                    logger.warning("Webhook dispatcher failed to initialize: %s", exc)
        elif events_cfg.enabled:
            logger.info("Events module not available (missing dependencies)")

        # Identity resolver
        identity_cfg = self._config.identity
        if identity_cfg.enabled and IdentityResolver is not None:
            try:
                from openbiometrics.watchlist.store import WatchlistManager

                watchlist_mgr = WatchlistManager(storage_dir=identity_cfg.watchlist_dir)
                self._identity_resolver = IdentityResolver(watchlist_mgr)
                logger.info("Identity resolver created")
            except ImportError:
                logger.info("Identity resolver not available (missing watchlist module)")
            except Exception as exc:
                logger.warning("Identity resolver failed to initialize: %s", exc)

        # Face clusterer
        if identity_cfg.enabled and FaceClusterer is not None:
            try:
                self._face_clusterer = FaceClusterer()
                logger.info("Face clusterer created")
            except Exception as exc:
                logger.warning("Face clusterer failed to initialize: %s", exc)

        self._loaded = True
        logger.info("BiometricKernel loaded successfully")

    def shutdown(self) -> None:
        """Shut down all modules gracefully."""
        if self._webhook_dispatcher is not None:
            try:
                self._webhook_dispatcher.shutdown()
            except Exception as exc:
                logger.warning("Webhook dispatcher shutdown error: %s", exc)

        if self._event_bus is not None:
            try:
                self._event_bus.shutdown()
            except Exception as exc:
                logger.warning("Event bus shutdown error: %s", exc)

        if self._camera_manager is not None:
            try:
                self._camera_manager.stop_all()
            except Exception as exc:
                logger.warning("Camera manager shutdown error: %s", exc)

        logger.info("BiometricKernel shut down")

    def health(self) -> HealthStatus:
        """Check health of the kernel and all loaded modules.

        Returns:
            HealthStatus with per-module breakdown
        """
        modules: dict[str, bool] = {}
        details: dict[str, str] = {}

        # Face module
        if self._face_pipeline is not None:
            try:
                face_ok = self._face_pipeline._detector is not None
                modules["face"] = face_ok
                if not face_ok:
                    details["face"] = "Detector not initialized"
                else:
                    parts = []
                    if self._face_pipeline._recognizer is not None:
                        parts.append("recognizer")
                    if self._face_pipeline._liveness is not None:
                        parts.append("liveness")
                    if self._face_pipeline._demographics is not None:
                        parts.append("demographics")
                    details["face"] = (
                        f"loaded: detector, {', '.join(parts)}" if parts
                        else "loaded: detector only"
                    )
            except Exception as exc:
                modules["face"] = False
                details["face"] = f"Error: {exc}"
        else:
            modules["face"] = False
            details["face"] = "Not loaded"

        # Document module
        if self._document_pipeline is not None:
            modules["document"] = True
            details["document"] = "loaded"
        elif self._config.document.enabled:
            modules["document"] = False
            details["document"] = "Enabled but not loaded (missing dependencies?)"
        else:
            modules["document"] = False
            details["document"] = "Disabled"

        # Liveness module
        if self._liveness_manager is not None:
            modules["liveness"] = True
            count = getattr(self._liveness_manager, "active_session_count", 0)
            details["liveness"] = f"loaded, {count} active session(s)"
        elif self._config.liveness.enabled:
            modules["liveness"] = False
            details["liveness"] = "Enabled but not loaded (missing dependencies?)"
        else:
            modules["liveness"] = False
            details["liveness"] = "Disabled"

        # Person detector
        if self._person_detector is not None:
            modules["person_detector"] = True
            details["person_detector"] = "loaded"
        elif self._config.person.enabled:
            modules["person_detector"] = False
            details["person_detector"] = "Enabled but not loaded (missing dependencies?)"
        else:
            modules["person_detector"] = False
            details["person_detector"] = "Disabled"

        # Person tracker
        if self._person_tracker is not None:
            modules["person_tracker"] = True
            details["person_tracker"] = "loaded"
        elif self._config.person.enabled:
            modules["person_tracker"] = False
            details["person_tracker"] = "Enabled but not loaded (missing dependencies?)"
        else:
            modules["person_tracker"] = False
            details["person_tracker"] = "Disabled"

        # Camera manager
        if self._camera_manager is not None:
            modules["video"] = True
            try:
                cam_count = len(self._camera_manager.list_cameras())
                details["video"] = f"loaded, {cam_count} camera(s)"
            except Exception:
                details["video"] = "loaded"
        elif self._config.video.enabled:
            modules["video"] = False
            details["video"] = "Enabled but not loaded (missing dependencies?)"
        else:
            modules["video"] = False
            details["video"] = "Disabled"

        # Event bus
        if self._event_bus is not None:
            modules["events"] = True
            details["events"] = "loaded"
        elif self._config.events.enabled:
            modules["events"] = False
            details["events"] = "Enabled but not loaded (missing dependencies?)"
        else:
            modules["events"] = False
            details["events"] = "Disabled"

        # Webhooks
        if self._webhook_dispatcher is not None:
            modules["webhooks"] = True
            try:
                wh_count = len(self._webhook_dispatcher.list_webhooks())
                details["webhooks"] = f"loaded, {wh_count} webhook(s)"
            except Exception:
                details["webhooks"] = "loaded"
        elif self._config.events.webhooks_enabled and self._config.events.enabled:
            modules["webhooks"] = False
            details["webhooks"] = "Enabled but not loaded"
        else:
            modules["webhooks"] = False
            details["webhooks"] = "Disabled"

        # Identity resolver
        if self._identity_resolver is not None:
            modules["identity_resolver"] = True
            details["identity_resolver"] = "loaded"
        elif self._config.identity.enabled:
            modules["identity_resolver"] = False
            details["identity_resolver"] = "Enabled but not loaded"
        else:
            modules["identity_resolver"] = False
            details["identity_resolver"] = "Disabled"

        # Face clusterer
        if self._face_clusterer is not None:
            modules["clusterer"] = True
            details["clusterer"] = "loaded"
        elif self._config.identity.enabled:
            modules["clusterer"] = False
            details["clusterer"] = "Enabled but not loaded"
        else:
            modules["clusterer"] = False
            details["clusterer"] = "Disabled"

        # Overall health: face must be OK, plus no critical failures
        healthy = modules.get("face", False)
        return HealthStatus(healthy=healthy, modules=modules, details=details)
