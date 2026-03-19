"""Pydantic models for the REST API."""

from pydantic import BaseModel


class FaceDetection(BaseModel):
    bbox: list[float]  # [x1, y1, x2, y2]
    confidence: float
    face_size: float
    landmarks: list[list[float]]


class QualityInfo(BaseModel):
    overall_score: float
    face_size_px: float
    sharpness: float
    brightness: float
    contrast: float
    head_pose_ok: bool
    is_acceptable: bool
    reasons: list[str]


class DemographicsInfo(BaseModel):
    age: int | None = None
    gender: str | None = None


class LivenessInfo(BaseModel):
    is_live: bool | None = None
    score: float | None = None


class FaceResponse(BaseModel):
    detection: FaceDetection
    quality: QualityInfo | None = None
    demographics: DemographicsInfo | None = None
    liveness: LivenessInfo | None = None
    has_embedding: bool = False


class DetectResponse(BaseModel):
    faces: list[FaceResponse]
    count: int


class VerifyRequest(BaseModel):
    threshold: float = 0.4


class VerifyResponse(BaseModel):
    is_match: bool
    similarity: float
    face1: FaceResponse | None = None
    face2: FaceResponse | None = None


class WatchlistEntry(BaseModel):
    identity_id: str
    label: str
    metadata: dict = {}


class WatchlistSearchResult(BaseModel):
    identity_id: str
    label: str
    similarity: float
    metadata: dict


class IdentifyResponse(BaseModel):
    face: FaceResponse
    matches: list[WatchlistSearchResult]


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    watchlist_count: int
