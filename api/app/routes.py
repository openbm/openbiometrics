"""FastAPI routes for the biometric platform.

Endpoints:
- POST /detect          - Detect faces in image
- POST /verify          - 1:1 verification (two images)
- POST /identify        - 1:N identification against watchlist
- POST /watchlist       - Add face to watchlist
- DELETE /watchlist/{id} - Remove from watchlist
- GET /watchlist         - List watchlist entries
- GET /health            - Service health check
"""

from __future__ import annotations

import uuid

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas import (
    DetectResponse,
    DemographicsInfo,
    FaceDetection,
    FaceResponse,
    HealthResponse,
    IdentifyResponse,
    LivenessInfo,
    QualityInfo,
    VerifyResponse,
    WatchlistEntry,
    WatchlistSearchResult,
)
from openbiometrics.core.pipeline import FacePipeline, FaceResult
from openbiometrics.watchlist.store import WatchlistManager

router = APIRouter()

# These are set by main.py on startup
pipeline: FacePipeline = None  # type: ignore
watchlist_mgr: WatchlistManager = None  # type: ignore


def _decode_image(file_bytes: bytes) -> np.ndarray:
    """Decode uploaded image bytes to BGR numpy array."""
    arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")
    return img


def _face_to_response(result: FaceResult) -> FaceResponse:
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
async def detect_faces(image: UploadFile = File(...)):
    """Detect all faces in an image with quality, demographics, and liveness."""
    img = _decode_image(await image.read())
    results = pipeline.process(img)
    faces = [_face_to_response(r) for r in results]
    return DetectResponse(faces=faces, count=len(faces))


@router.post("/verify", response_model=VerifyResponse)
async def verify_faces(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    threshold: float = Form(0.4),
):
    """1:1 verification — compare two face images."""
    img1 = _decode_image(await image1.read())
    img2 = _decode_image(await image2.read())

    results1 = pipeline.process(img1)
    results2 = pipeline.process(img2)

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
):
    """1:N identification — search face against watchlist."""
    img = _decode_image(await image.read())
    results = pipeline.process(img)

    if not results:
        raise HTTPException(status_code=400, detail="No face detected")

    r = results[0]
    if r.embedding is None:
        raise HTTPException(status_code=500, detail="Recognition model not loaded")

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


@router.post("/watchlist/enroll")
async def enroll_face(
    image: UploadFile = File(...),
    identity_id: str = Form(default=""),
    label: str = Form(...),
    watchlist_name: str = Form("default"),
):
    """Enroll a face into a watchlist."""
    img = _decode_image(await image.read())
    results = pipeline.process(img)

    if not results:
        raise HTTPException(status_code=400, detail="No face detected")

    r = results[0]
    if r.embedding is None:
        raise HTTPException(status_code=500, detail="Recognition model not loaded")

    if not identity_id:
        identity_id = str(uuid.uuid4())

    wl = watchlist_mgr.get(watchlist_name)
    wl.add(identity_id, label, r.embedding)
    wl.save(watchlist_mgr.storage_dir)

    return {
        "identity_id": identity_id,
        "label": label,
        "watchlist": watchlist_name,
        "face": _face_to_response(r),
    }


@router.delete("/watchlist/{identity_id}")
async def remove_from_watchlist(identity_id: str, watchlist_name: str = "default"):
    """Remove an identity from a watchlist."""
    wl = watchlist_mgr.get(watchlist_name)
    if not wl.remove(identity_id):
        raise HTTPException(status_code=404, detail="Identity not found")
    wl.save(watchlist_mgr.storage_dir)
    return {"removed": identity_id}


@router.get("/watchlist")
async def list_watchlists():
    """List all watchlists and their sizes."""
    names = watchlist_mgr.list_watchlists()
    return {
        "watchlists": [{"name": n, "size": watchlist_mgr.get(n).size} for n in names]
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health check."""
    wl_count = sum(watchlist_mgr.get(n).size for n in watchlist_mgr.list_watchlists())
    return HealthResponse(
        status="ok",
        models_loaded=pipeline._detector is not None,
        watchlist_count=wl_count,
    )
