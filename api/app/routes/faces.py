"""Face detection, verification, and identification endpoints.

Backward-compatible with the original routes — same paths and contracts.
"""

from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.deps import get_kernel
from app.schemas import (
    DemographicsInfo,
    DetectResponse,
    FaceDetection,
    FaceResponse,
    HealthResponse,
    IdentifyResponse,
    LivenessInfo,
    QualityInfo,
    VerifyResponse,
    WatchlistSearchResult,
)
from openbiometrics.kernel import BiometricKernel

router = APIRouter(tags=["faces"])


def _decode_image(file_bytes: bytes) -> np.ndarray:
    """Decode uploaded image bytes to BGR numpy array."""
    arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")
    return img


def _face_to_response(result) -> FaceResponse:
    """Convert FaceResult to API response."""
    face = result.face
    resp = FaceResponse(
        detection=FaceDetection(
            bbox=face.bbox.tolist(),
            confidence=face.confidence,
            face_size=face.face_size,
            landmarks=face.landmarks.tolist(),
        ),
        has_embedding=result.embedding is not None,
    )
    if result.quality is not None:
        resp.quality = QualityInfo(
            overall_score=result.quality.overall_score,
            face_size_px=result.quality.face_size_px,
            sharpness=result.quality.sharpness,
            brightness=result.quality.brightness,
            contrast=result.quality.contrast,
            head_pose_ok=result.quality.head_pose_ok,
            is_acceptable=result.quality.is_acceptable,
            reasons=result.quality.reasons,
        )
    if result.age is not None or result.gender is not None:
        resp.demographics = DemographicsInfo(age=result.age, gender=result.gender)
    if result.is_live is not None:
        resp.liveness = LivenessInfo(is_live=result.is_live, score=result.liveness_score)
    return resp


@router.post("/detect", response_model=DetectResponse)
async def detect_faces(
    image: UploadFile = File(...),
    kernel: BiometricKernel = Depends(get_kernel),
):
    """Detect all faces in an image with quality, demographics, and liveness."""
    img = _decode_image(await image.read())
    results = kernel.face.process(img)
    faces = [_face_to_response(r) for r in results]
    return DetectResponse(faces=faces, count=len(faces))


@router.post("/verify", response_model=VerifyResponse)
async def verify_faces(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    threshold: float = Form(0.4),
    kernel: BiometricKernel = Depends(get_kernel),
):
    """1:1 verification -- compare two face images."""
    img1 = _decode_image(await image1.read())
    img2 = _decode_image(await image2.read())

    results1 = kernel.face.process(img1)
    results2 = kernel.face.process(img2)

    if not results1:
        raise HTTPException(status_code=400, detail="No face detected in image1")
    if not results2:
        raise HTTPException(status_code=400, detail="No face detected in image2")

    r1, r2 = results1[0], results2[0]
    if r1.embedding is None or r2.embedding is None:
        raise HTTPException(status_code=500, detail="Recognition model not loaded")

    from openbiometrics.core.recognizer import FaceRecognizer

    similarity = FaceRecognizer.compare(r1.embedding, r2.embedding)

    return VerifyResponse(
        is_match=similarity >= threshold,
        similarity=similarity,
        face1=_face_to_response(r1),
        face2=_face_to_response(r2),
    )


@router.post("/identify", response_model=IdentifyResponse)
async def identify_face(
    image: UploadFile = File(...),
    watchlist_name: str = Form("default"),
    top_k: int = Form(5),
    threshold: float = Form(0.4),
    kernel: BiometricKernel = Depends(get_kernel),
):
    """1:N identification -- search face against watchlist."""
    img = _decode_image(await image.read())
    results = kernel.face.process(img)

    if not results:
        raise HTTPException(status_code=400, detail="No face detected")

    r = results[0]
    if r.embedding is None:
        raise HTTPException(status_code=500, detail="Recognition model not loaded")

    from openbiometrics.watchlist.store import WatchlistManager

    watchlist_mgr = WatchlistManager(storage_dir="./watchlists")
    wl = watchlist_mgr.get(watchlist_name)
    matches = wl.search(r.embedding, top_k=top_k, threshold=threshold)

    return IdentifyResponse(
        face=_face_to_response(r),
        matches=[
            WatchlistSearchResult(
                identity_id=m.identity_id,
                label=m.label,
                similarity=m.similarity,
                metadata=m.metadata,
            )
            for m in matches
        ],
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(kernel: BiometricKernel = Depends(get_kernel)):
    """Service health check."""
    from openbiometrics.watchlist.store import WatchlistManager

    watchlist_mgr = WatchlistManager(storage_dir="./watchlists")
    wl_count = sum(watchlist_mgr.get(n).size for n in watchlist_mgr.list_watchlists())
    return HealthResponse(
        status="ok",
        models_loaded=kernel.face._detector is not None,
        watchlist_count=wl_count,
    )
