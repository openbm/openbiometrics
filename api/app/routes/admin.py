"""Admin endpoints: health, model status, and configuration."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import get_kernel
from app.schemas import AdminHealthResponse, ModelStatusSchema
from openbiometrics.kernel import BiometricKernel

router = APIRouter()


@router.get("/health", response_model=AdminHealthResponse)
async def enhanced_health(kernel: BiometricKernel = Depends(get_kernel)):
    """Enhanced health check covering all modules."""
    status = kernel.health()
    return AdminHealthResponse(
        healthy=status.healthy,
        modules=status.modules,
        details=status.details,
    )


@router.get("/models", response_model=list[ModelStatusSchema])
async def model_status(kernel: BiometricKernel = Depends(get_kernel)):
    """Report status of loaded models."""
    models: list[ModelStatusSchema] = []

    face = kernel.face
    if face is not None:
        models.append(ModelStatusSchema(
            name="face_detector",
            module="face",
            loaded=face._detector is not None,
        ))
        models.append(ModelStatusSchema(
            name="face_recognizer",
            module="face",
            loaded=face._recognizer is not None,
        ))
        models.append(ModelStatusSchema(
            name="liveness",
            module="face",
            loaded=getattr(face, "_liveness", None) is not None,
        ))
        models.append(ModelStatusSchema(
            name="demographics",
            module="face",
            loaded=getattr(face, "_demographics", None) is not None,
        ))

    if kernel.document is not None:
        models.append(ModelStatusSchema(
            name="document_detector",
            module="document",
            loaded=True,
        ))
    else:
        models.append(ModelStatusSchema(
            name="document_pipeline",
            module="document",
            loaded=False,
        ))

    if kernel.person_detector is not None:
        models.append(ModelStatusSchema(
            name="person_detector",
            module="person",
            loaded=True,
        ))
    else:
        models.append(ModelStatusSchema(
            name="person_detector",
            module="person",
            loaded=False,
        ))

    if kernel.person_tracker is not None:
        models.append(ModelStatusSchema(
            name="person_tracker",
            module="person",
            loaded=True,
        ))

    if kernel.liveness is not None:
        models.append(ModelStatusSchema(
            name="active_liveness",
            module="liveness",
            loaded=True,
        ))

    if kernel.events is not None:
        models.append(ModelStatusSchema(
            name="event_bus",
            module="events",
            loaded=True,
        ))

    if kernel.cameras is not None:
        models.append(ModelStatusSchema(
            name="camera_manager",
            module="video",
            loaded=True,
        ))

    if kernel.identity_resolver is not None:
        models.append(ModelStatusSchema(
            name="identity_resolver",
            module="identity",
            loaded=True,
        ))

    if kernel.clusterer is not None:
        models.append(ModelStatusSchema(
            name="face_clusterer",
            module="identity",
            loaded=True,
        ))

    return models


@router.get("/config")
async def current_config(kernel: BiometricKernel = Depends(get_kernel)):
    """Return current engine configuration."""
    cfg = kernel.config
    result = {
        "face": {
            "models_dir": cfg.face.models_dir,
            "ctx_id": cfg.face.ctx_id,
            "det_thresh": cfg.face.det_thresh,
            "det_size": list(cfg.face.det_size),
            "max_faces": cfg.face.max_faces,
            "enable_liveness": cfg.face.enable_liveness,
            "enable_demographics": cfg.face.enable_demographics,
            "enable_quality": cfg.face.enable_quality,
            "quality_gate": cfg.face.quality_gate,
        },
        "document": {
            "enabled": cfg.document.enabled,
            "models_dir": cfg.document.models_dir,
            "enable_ocr": cfg.document.enable_ocr,
            "enable_mrz": cfg.document.enable_mrz,
            "enable_face_extraction": cfg.document.enable_face_extraction,
        },
        "liveness": {
            "enabled": cfg.liveness.enabled,
            "session_ttl": cfg.liveness.session_ttl,
            "num_challenges": cfg.liveness.num_challenges,
            "timeout_seconds": cfg.liveness.timeout_seconds,
        },
        "person": {
            "enabled": cfg.person.enabled,
            "model_path": cfg.person.model_path,
            "confidence_threshold": cfg.person.confidence_threshold,
        },
        "video": {
            "enabled": cfg.video.enabled,
            "max_fps": cfg.video.max_fps,
            "track_faces": cfg.video.track_faces,
            "buffer_size": cfg.video.buffer_size,
        },
        "events": {
            "enabled": cfg.events.enabled,
            "webhooks_enabled": cfg.events.webhooks_enabled,
            "max_workers": cfg.events.max_workers,
            "history_size": cfg.events.history_size,
        },
        "identity": {
            "enabled": cfg.identity.enabled,
            "watchlist_dir": cfg.identity.watchlist_dir,
            "cluster_threshold": cfg.identity.cluster_threshold,
        },
    }
    return result
