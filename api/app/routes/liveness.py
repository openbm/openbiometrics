"""Active liveness session endpoints."""

from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.deps import get_kernel
from app.schemas import ChallengeResultSchema, ChallengeSchema, LivenessSessionResponse
from openbiometrics.kernel import BiometricKernel
from openbiometrics.liveness.presets import LivenessPreset, get_preset, list_presets

router = APIRouter()


def _get_liveness_manager(kernel: BiometricKernel = Depends(get_kernel)):
    """Get the liveness manager from the kernel, or 503 if unavailable."""
    manager = kernel.liveness
    if manager is None:
        raise HTTPException(
            status_code=503,
            detail="Active liveness module not available",
        )
    return manager


def _decode_image(file_bytes: bytes) -> np.ndarray:
    """Decode uploaded image bytes to BGR numpy array."""
    arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")
    return img


def _session_to_response(session) -> LivenessSessionResponse:
    """Build a LivenessSessionResponse from an ActiveLivenessSession."""
    return LivenessSessionResponse(
        session_id=session.session_id,
        state=session.state.value,
        challenges=[
            ChallengeSchema(
                type=c.type.value,
                instruction=c.instruction,
                timeout_seconds=c.timeout_seconds,
            )
            for c in session.challenges
        ],
    )


@router.get("/presets")
async def get_presets():
    """List all available liveness presets."""
    return [
        {
            "name": p.name.value,
            "description": p.description,
            "num_challenges": p.num_challenges,
            "challenge_types": [ct.value for ct in p.challenge_types],
            "timeout_seconds": p.timeout_seconds,
            "require_passive": p.require_passive,
        }
        for p in list_presets()
    ]


@router.post("/sessions", response_model=LivenessSessionResponse)
async def create_session(
    preset: str | None = Query(None, description="Preset name: eye, smile, multi_range, head_turn, full, passive_only"),
    num_challenges: int = 3,
    timeout_seconds: float = 5.0,
    manager=Depends(_get_liveness_manager),
):
    """Create a new active liveness session.

    Use a preset for standard configurations, or specify custom parameters.
    """
    if preset:
        try:
            p = get_preset(preset)
        except (ValueError, KeyError):
            raise HTTPException(
                status_code=400,
                detail=f"Unknown preset '{preset}'. Use GET /liveness/presets to list available presets.",
            )
        if p.num_challenges == 0:
            raise HTTPException(
                status_code=400,
                detail="passive_only preset has no active challenges. Use POST /faces/detect with liveness=true instead.",
            )
        session = manager.create_session(**p.session_kwargs())
    else:
        session = manager.create_session(
            num_challenges=num_challenges,
            timeout_seconds=timeout_seconds,
        )
    return _session_to_response(session)


@router.post("/sessions/{session_id}/frame", response_model=ChallengeResultSchema)
async def submit_frame(
    session_id: str,
    image: UploadFile = File(...),
    manager=Depends(_get_liveness_manager),
):
    """Submit a video frame for the current challenge."""
    img = _decode_image(await image.read())

    try:
        result = manager.submit_frame(session_id, img)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    return ChallengeResultSchema(
        session_id=result.session_id,
        challenge_type=result.challenge_type.value if result.challenge_type else None,
        passed=result.passed,
        confidence=result.confidence,
        challenges_remaining=result.challenges_remaining,
        session_complete=result.session_complete,
        is_live=result.is_live,
        state=result.state.value,
    )


@router.get("/sessions/{session_id}", response_model=LivenessSessionResponse)
async def get_session(
    session_id: str,
    manager=Depends(_get_liveness_manager),
):
    """Get current status of a liveness session."""
    session = manager.get_session(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    return _session_to_response(session)


@router.delete("/sessions/{session_id}")
async def cancel_session(
    session_id: str,
    manager=Depends(_get_liveness_manager),
):
    """Cancel and remove a liveness session."""
    removed = manager.remove_session(session_id)

    if not removed:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    return {"cancelled": session_id}
